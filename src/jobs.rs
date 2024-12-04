use super::EventsByVendor;
use crate::configs;
use crate::inventories::{self, Node};
use crate::scripts;
use crate::ssh;
use crate::results;
use log::{debug, error, info, warn};
use serde::{Deserialize, Serialize};
use serde_yaml::{self};
use std::collections::HashMap;
use std::fmt::{self, Display};
use std::str::{self};
use std::time::Duration;
use std::{env, fs};
use std::path::{Path, PathBuf};
use subprocess::{Popen, PopenConfig, Redirection};
use thiserror::Error;
use std::process::Command;

const MAX_CONCURRENT_JOBS: usize = 20;

#[derive(Error, Debug)]
pub enum JobError {
    #[error("Openssh client failed: {0}")]
    Openssh(#[from] openssh::Error),
    #[error("Serde YAML parsing failed: {0}")]
    SerdeYAML(#[from] serde_yaml::Error),
    #[error("Serde JSON parsing failed: {0}")]
    SerdeJSON(#[from] serde_json::Error),
    #[error("Env parsing failed: {0}")]
    Env(#[from] env::VarError),
    #[error("Could not read script: {0}")]
    Io(#[from] std::io::Error),
    #[error("Could not upload script: {0}")]
    Ssh(#[from] ssh::SshError),
    #[error("Could not get Inventories entries: {0}")]
    Inventory(#[from] inventories::InventoryError),
    #[error("Could not generate Scripts: {0}")]
    Script(#[from] scripts::ScriptError),
    #[error("HTTP request failed: {0}")]
    HttpRequest(#[from] reqwest::Error),
    #[error("Rsync failed : {0}")]
    Rsync(#[from] subprocess::PopenError),
    #[error("Unknown OAR state: {0}")]
    UnknownState(String),
}

type JobResult = Result<(), JobError>;

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize, Clone)]
pub enum OARState {
    NotSubmitted,
    Hold,
    Waiting,
    Running,
    Terminated,
    Finishing,
    Failed,
    UnknownState,
}

impl Display for OARState {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.to_str())
    }
}

impl OARState {
    fn to_str(&self) -> &'static str {
        match self {
            OARState::NotSubmitted => "NotSubmitted",
            OARState::Hold => "Hold",
            OARState::Waiting => "Waiting",
            OARState::Running => "Running",
            OARState::Terminated => "Terminated",
            OARState::Finishing => "Finishing",
            OARState::Failed => "Failed",
            OARState::UnknownState => "UnknownState",
        }
    }

    fn is_terminal(&self) -> bool {
        self == &OARState::Terminated || self == &OARState::Failed || self == &OARState::UnknownState
    }
}

impl TryFrom<&str> for OARState {
    type Error = JobError;

    fn try_from(state: &str) -> Result<Self, Self::Error> {
        match state {
            "running" => Ok(OARState::Running),
            "error" => Ok(OARState::Failed),
            "waiting" => Ok(OARState::Waiting),
            "terminated" => Ok(OARState::Terminated),
            "hold" => Ok(OARState::Hold),
            "finishing" => Ok(OARState::Finishing),
            "not_submitted" => Ok(OARState::NotSubmitted),
            unknown => Err(JobError::UnknownState(unknown.to_string())),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Job {
    pub id: usize,
    pub node: Node,
    pub oar_job_id: Option<u32>,
    pub state: OARState,
    pub core_values: Vec<u32>,
    pub script_file: String,
    pub results_dir: String,
    pub site: String,
}

impl Job {
    fn build_script_file_path(node: &Node, site: &str, root_scripts_dir: &str) -> String {
        format!(
            "{}/{}/{}/{}.sh",
            root_scripts_dir,
            site,
            node.cluster.as_ref().unwrap(),
            node.uid
        )
    }

    fn build_results_dir_path(node: &Node, site: &str, root_results_dir: &str) -> String {
        format!(
            "{}/{}/{}/{}",
            root_results_dir,
            site,
            node.cluster.as_ref().unwrap(),
            node.uid
        )
    }

    fn new(id: usize, node: Node, core_values: Vec<u32>, site: String, root_scripts_dir: &str, root_results_dir: &str) -> Self {
        let script_file = Job::build_script_file_path(&node, &site, root_scripts_dir);
        let results_dir = Job::build_results_dir_path(&node, &site, root_results_dir);

        Job {
            id,
            node,
            oar_job_id: None, // Submission through OAR will give this ID
            state: OARState::NotSubmitted, // Default init state
            core_values,
            script_file,
            results_dir,
            site,
        }
    }

    fn finished(&self) -> bool {
        self.state.is_terminal()
    }

    pub async fn submit_job(&mut self) -> JobResult {
        let session = ssh::ssh_connect(&self.site).await?;
        ssh::create_remote_directory(&session, &self.script_file).await?;
        ssh::sftp_upload(&session, &self.script_file, &self.script_file).await?;
        ssh::make_script_executable(&session, &self.script_file).await?;

        let oar_job_id = ssh::run_oarsub(&session, &self.script_file).await;

        if let Ok(Some(job_id)) = oar_job_id {
            self.oar_job_id = Some(job_id);
            self.state = OARState::Waiting;
        } else {
            self.state = OARState::Failed;
        }

        session.close().await?;
        Ok(())
    }

    pub async fn update_job_state(
        &mut self,
        client: &reqwest::Client,
        base_url: &str,
    ) -> JobResult {
        let response: HashMap<String, serde_json::Value> = crate::inventories::get_api_call(
            client,
            &format!(
                "{}/sites/{}/jobs/{}",
                base_url,
                &self.site,
                &self.oar_job_id.unwrap()
            ),
        )
        .await
        .unwrap();
        let state: String = serde_json::from_value(response.get("state").unwrap().clone())?;
        let state = OARState::try_from(state.as_str())?;
        if state != self.state {
            self.state_transition(state).await?;
        }
        Ok(())
    }

    pub async fn state_transition(&mut self, new_state: OARState) -> JobResult {
        info!(
            "Transitioning Job {} with OAR_JOB_ID {:?} from {} to {}",
            self.id, self.oar_job_id, self.state, new_state
        );
        self.state = new_state.clone();

        match new_state {
            OARState::Terminated | OARState::Failed => self.job_terminated().await,
            _ => {
                error!("Unhandled state transition to {}", new_state);
                Ok(())
            }
        }
    }

    pub async fn job_terminated(&mut self) -> JobResult {
        if let Err(rsync_result) = rsync_results(
            &self.site,
            self.node.cluster.as_deref().unwrap(),
            &self.node.uid,
        ) {
            self.state = OARState::UnknownState;
        } else {
            if let Ok(_extracted) = extract_tar_xz(&self.results_dir) {
                results::process_results(&self.results_dir)?;
            } else {
                warn!("Could not extract tar");
            }
        }
        Ok(())
    }

}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Jobs {
    pub jobs: Vec<Job>,
}

impl Jobs {
    // Generate all jobs and store them in JOBS_FILE
    pub async fn generate_jobs(
        &mut self,
        jobs_file: &str,
        inventories_dir: &str,
        scripts_dir: &str,
        results_dir: &str,
        events_by_vendor: &EventsByVendor,
    ) -> Result<(), JobError> {
        let sites = inventories::get_inventory_sites(inventories_dir)?;
        let mut clusters_nodes: Vec<Vec<(String, String, Node)>> = Vec::new();
        for site in sites {
            let clusters = inventories::get_inventory_site_clusters(inventories_dir, &site)?;

            for cluster in clusters {
                let nodes = inventories::get_inventory_site_cluster_nodes(
                    inventories_dir,
                    &site,
                    &cluster,
                )?;
                let mut cluster_nodes: Vec<(String, String, Node)> = Vec::new();

                // Load each node's metadata as a Node instance
                for node_file in &nodes {
                    let metadata_file_path =
                        format!("{}/{}/{}/{}", inventories_dir, &site, &cluster, node_file);
                    let metadata_file_content = std::fs::read_to_string(&metadata_file_path)?;
                    let node: Node = serde_json::from_str(&metadata_file_content)?;
                    cluster_nodes.push((site.clone(), cluster.clone(), node));
                }
                if cluster_nodes.len() > 0 {
                    clusters_nodes.push(cluster_nodes);
                }
            }
        }

        // Execute round-robin submissions across clusters by node index
        let mut index = 0;
        loop {
            let mut all_clusters_completed = true;

            for cluster_nodes in clusters_nodes.iter() {
                // Check if this cluster has a node at the current index
                if let Some((site, cluster, node)) = cluster_nodes.get(index) {
                    all_clusters_completed = false;

                    let node_uid = node.uid.clone();
                    debug!("Draw {} node from list of possible nodes", node_uid);
                    if !self.job_planned_on_node(&node_uid) {
                        while self.nb_ongoing_jobs() >= MAX_CONCURRENT_JOBS {
                            info!(
                                "{} jobs are currently active; pausing before submitting more",
                                MAX_CONCURRENT_JOBS
                            );
                            tokio::time::sleep(std::time::Duration::from_secs(
                                super::SLEEP_CHECK_TIME_IN_SECONDES,
                            ))
                            .await;

                            let client = reqwest::Client::builder().build()?;
                            self.check_unfinished_jobs(&client, super::BASE_URL, jobs_file)
                                .await?;
                        }
                        // Job creation and submission
                        let core_values =
                            configs::generate_core_values(5, node.architecture.nb_cores);
                        let mut job =
                            Job::new(self.jobs.len(), node.clone(), core_values, site.to_string(), scripts_dir, results_dir);
                        fs::create_dir_all(
                            std::path::Path::new(&job.script_file).parent().unwrap(),
                        )?;
                        fs::create_dir_all(results_dir)?;

                        let client = reqwest::Client::builder().build()?;
                        scripts::generate_script_file(&job, events_by_vendor)?;
                        job.submit_job().await?;
                        self.jobs.push(job);
                        info!("Job submitted for {} node", node_uid);
                        info!("Wait 1 secondes before another submission");
                        tokio::time::sleep(Duration::from_secs(1)).await;

                        self.check_unfinished_jobs(&client, super::BASE_URL, jobs_file)
                            .await?;

                        // Throttling based on the maximum allowed concurrent jobs
                    } else {
                        info!("Job already listed on {} node, skipping", node_uid);
                        tokio::time::sleep(Duration::from_millis(100)).await;
                    }
                }
            }

            if all_clusters_completed {
                break;
            }
            index += 1; // Move to the next node index across clusters
        }

        self.dump_to_file(jobs_file)?;
        Ok(())
    }

    pub async fn check_unfinished_jobs(
        &mut self,
        client: &reqwest::Client,
        base_url: &str,
        file_to_dump_to: &str,
    ) -> Result<(), JobError> {
        for job in self.jobs.iter_mut().filter(|j| !j.finished()) {
            job.update_job_state(client, base_url).await?;
            if !job.finished() {
                debug!(
                    "Job {:?} is still in '{}' state.",
                    job.oar_job_id, job.state
                );
            }
            tokio::time::sleep(Duration::from_secs(5)).await;
        }

        self.dump_to_file(file_to_dump_to)?;
        Ok(())
    }

    fn nb_ongoing_jobs(&self) -> usize {
        self.jobs
            .to_owned()
            .iter()
            .filter(|j| !j.finished())
            .collect::<Vec<&Job>>()
            .len()
    }
    pub fn job_planned_on_node(&self, searched_node_uid: &str) -> bool {
        self.jobs
            .iter()
            .any(|job| job.node.uid == searched_node_uid)
    }

    pub fn job_is_done(&self) -> bool {
        self.jobs.iter().all(|job| job.finished())
    }
    pub fn dump_to_file(&self, file_path: &str) -> JobResult {
        if !std::path::Path::new(file_path).exists() {
            debug!("Create Jobs File : '{}'", file_path);
        }
        let file = fs::File::create(file_path)?;
        serde_yaml::to_writer(file, self)?;
        Ok(())
    }
}

pub fn rsync_results(site: &str, cluster: &str, node: &str) -> JobResult {
    let remote_directory = format!("{}:/home/nleblond/results.d", site);
    let mut p = Popen::create(
        &["rsync", "-avzP", &remote_directory, "."],
        PopenConfig {
            stdout: Redirection::Pipe,
            ..Default::default()
        },
    )?;

    let (out, err) = p.communicate(None)?;

    if let Ok(Some(exit_status)) = p.wait_timeout(Duration::from_secs(120)) {
        if exit_status.success() {
            debug!("Rsync with site {} done.\n{:?}", site, out);
        } else {
            debug!("Rsync with site {} failed.\n{:?} ; {:?}", site, out, err);
            return Err(JobError::UnknownState("Rsync failed".to_string()))
        }
    } else {
        p.terminate()?;
    }
    let checksum_file = format!("results.d/{}/{}/{}.tar.xz.md5", site, cluster, node);
    let mut p = Popen::create(
        &["md5sum", "-c", &checksum_file],
        PopenConfig {
            stdout: Redirection::Pipe,
            ..Default::default()
        },
    )?;

    let (out, err) = p.communicate(None)?;

    if let Ok(Some(exit_status)) = p.wait_timeout(Duration::from_secs(120)) {
        if exit_status.success() {
            debug!("Checksum success.\n{:?}", out);
        } else {
            debug!("Checksum fail.\n{:?} ; {:?}", out, err);
            return Err(JobError::UnknownState("Checksum failed".to_string()))
        }
    } else {
        p.terminate()?;
    }

    Ok(())
}

fn extract_tar_xz(dir_path: &str) -> Result <(), String> {
    let dir = Path::new(dir_path);

    let tar_xz_name = match dir.file_name() {
        Some(name) => {
            let mut archive_name = PathBuf::from(name);
            archive_name.set_extension("tar.xz");
            archive_name
        }
        None => return Err("Failed to compute archive name from directory path.".to_string()),
    };

    let archive_path = dir.parent().unwrap_or_else(|| Path::new(".")).join(&tar_xz_name);

    if !archive_path.exists() {
        return Err(format!("Archive not found: {:?}", archive_path));
    }

    let output_5 = Command::new("tar")
        .arg("-xf")
        .arg(&archive_path)
        .arg("--strip-components=5") // Strips the leading directory components
        .arg("-C")
        .arg(dir.parent().unwrap_or_else(|| Path::new(".")))
        .output()
        .map_err(|e| format!("Failed to execute tar command stripping 5: {}", e))?;

    if !output_5.status.success() {
        let output_3 = Command::new("tar")
            .arg("-xf")
            .arg(&archive_path)
            .arg("--strip-components=3") // Strips the leading directory components
            .arg("-C")
            .arg(dir.parent().unwrap_or_else(|| Path::new(".")))
            .output()
            .map_err(|e| format!("Failed to execute tar command stripping 3: {}", e))?;

        if !output_3.status.success() {

            return Err(format!(
                "tar command failed with error: {}",
                String::from_utf8_lossy(&output_3.stderr)
            ));
        }
    }

    Ok(())
}
