use super::EventsByVendor;
use crate::configs;
use crate::inventories::{self, Node};
use crate::results;
use crate::scripts;
use crate::ssh;
use chrono::{Duration, Local, Timelike};
use log::{debug, error, info, warn};
use serde::{Deserialize, Serialize};
use serde_yaml::{self};
use std::collections::HashMap;
use std::fmt::{self, Display};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::str::{self};
use std::{env, fs};
use subprocess::{Popen, PopenConfig, Redirection};
use thiserror::Error;

const MAX_CONCURRENT_JOBS: usize = 20;
const G5K_DAY_BOTTOM_BOUNDARY: i64 = 9;
const G5K_DAY_UP_BOUNDARY: i64 = 19;

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
    Processing,
    Deployed,
    WaitingToBeDeployed,
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
            OARState::Processing => "Processing",
            OARState::Deployed => "Deployed",
            OARState::WaitingToBeDeployed => "WaitingToBeDeployed",
        }
    }

    fn is_terminal(&self) -> bool {
        self == &OARState::Terminated
            || self == &OARState::Failed
            || self == &OARState::UnknownState
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
            "processing" => Ok(OARState::Processing),
            "deployed" => Ok(OARState::Deployed),
            "waiting_to_be_deployed" => Ok(OARState::WaitingToBeDeployed),
            unknown => Err(JobError::UnknownState(unknown.to_string())),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Job {
    pub id: usize,
    pub node: Node,
    pub oar_job_id: Option<u64>,
    pub state: OARState,
    pub core_values: Vec<u32>,
    pub script_file: String,
    pub results_dir: String,
    pub site: String,
    pub deployment_id: Option<String>,
    pub os_flavor: String,
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

    fn new(
        id: usize,
        node: Node,
        core_values: Vec<u32>,
        site: String,
        root_scripts_dir: &str,
        root_results_dir: &str,
        os_flavor: String,
    ) -> Self {
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
            deployment_id: None,
            os_flavor,
        }
    }

    fn finished(&self) -> bool {
        self.state.is_terminal()
    }

    pub async fn submit_job(&mut self) -> JobResult {
        info!("Submitting job on {}", &self.node.uid);
        let session = ssh::ssh_connect(&self.site).await?;
        ssh::create_remote_directory(&session, &self.script_file).await?;
        ssh::sftp_upload(&session, &self.script_file, &self.script_file).await?;
        ssh::make_script_executable(&session, &self.script_file).await?;

        if self.os_flavor == super::DEFAULT_OS_FLAVOR {
            let oar_job_id = ssh::run_oarsub(&session, &self.script_file).await;
            if let Ok(Some(job_id)) = oar_job_id {
                self.oar_job_id = Some(job_id);
                self.state = OARState::Waiting;
            } else {
                self.state = OARState::Failed;
            }
        } else {
            let client = reqwest::Client::builder().build()?;
            let endpoint = format!("{}/sites/{}/jobs", super::BASE_URL, self.site);
            let data = serde_json::json!({"properties": format!("host={}",self.node.uid), "resources": format!("walltime={}", scripts::WALLTIME), "types": ["deploy"], "command": "sleep 14500"});

            if let Ok(response) = inventories::post_api_call(&client, &endpoint, &data).await {
                debug!("Job has been posted on deploy mode");
                self.state = OARState::WaitingToBeDeployed;
                let job_id = response.get("uid").unwrap();
                self.oar_job_id = job_id.as_u64();
            } else {
                error!("Job has failed to be posted on deploy mode");
                self.state = OARState::Failed;
            }
        }

        session.close().await?;

        Ok(())
    }

    pub async fn update_job_state(
        &mut self,
        client: &reqwest::Client,
        base_url: &str,
    ) -> JobResult {
        let state: OARState;
        if self.state == OARState::Processing {
            let endpoint = format!(
                "{}/sites/{}/deployments/{}",
                base_url,
                self.site,
                self.deployment_id.clone().unwrap()
            );
            if let Ok(response) = inventories::get_api_call(&client, &endpoint).await {
                let str_state = response.get("status").unwrap().as_str().unwrap();
                if str_state == "terminated" {
                    state = OARState::Deployed;
                } else if str_state == "processing" {
                    state = OARState::Processing;
                } else {
                    state = OARState::Failed;
                }
            } else {
                state = OARState::Failed;
            }
        } else {
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
            let str_state = response.get("state").unwrap().as_str();
            if str_state == Some("waiting") && self.state == OARState::WaitingToBeDeployed {
                state = OARState::WaitingToBeDeployed;
            } else if str_state == Some("launching") || str_state == Some("to_launch") {
                state = self.state.clone();
            } else {
                state = OARState::try_from(str_state.unwrap()).unwrap();
            }
        }

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
            OARState::Running => self.job_running().await,
            OARState::Deployed => self.job_os_deployed().await,
            _ => {
                error!("Unhandled state transition to {}", new_state);
                Ok(())
            }
        }
    }

    pub async fn job_running(&mut self) -> JobResult {
        if self.os_flavor == super::DEFAULT_OS_FLAVOR {
            info!("Starting script on {}", &self.node.uid);
            return Ok(());
        }
        info!("Deploying new environement on {}", &self.node.uid);
        // CURL KADEPLOY
        let client = reqwest::Client::builder().build()?;
        let endpoint = format!("{}/sites/{}/deployments", super::BASE_URL, self.site);
        let pub_key_content = fs::read_to_string(".ssh_g5k.pub")
            .map_err(|e| format!("Failed to read the SSH public key: {}", e))
            .unwrap();
        let pub_key_content = pub_key_content.trim();

        let data = serde_json::json!({
            "nodes": [&format!("{}.{}.grid5000.fr",self.node.uid, self.site)],
            "environment": self.os_flavor,
            "key": pub_key_content
        });

        match inventories::post_api_call(&client, &endpoint, &data).await {
            Ok(response) => {
                debug!("Job os_flavor is being deployed");
                self.state = OARState::Processing;
                let deployment_id = response.get("uid").unwrap();
                self.deployment_id = Some(deployment_id.as_str().unwrap().to_owned());
            }
            Err(e) => {
                error!("Job os_flavor has failed to be deployed : {:?}", e);
                self.state = OARState::Failed;
            }
        }

        Ok(())
    }

    pub async fn job_os_deployed(&mut self) -> JobResult {
        info!("Running script on {}", &self.node.uid);

        let session = ssh::ssh_connect(&self.site).await?;
        let host = format!("{}.{}.grid5000.fr", self.node.uid, self.site);
        if let Ok(_script_result) = ssh::run_script(&session, &host, &self.script_file).await {
            self.state = OARState::Running;
        } else {
            self.state = OARState::Failed;
        }
        Ok(())
    }

    pub async fn job_terminated(&mut self) -> JobResult {
        info!("Downloading and processing results from {}", &self.node.uid);
        let root_results_dir = Path::new(&self.results_dir)
            .components()
            .filter_map(|comp| match comp {
                std::path::Component::Normal(name) => name.to_str(),
                _ => None,
            })
            .next();
        if let Err(_rsync_result) =
            rsync_results(&self.site, &self.results_dir, root_results_dir.unwrap())
        {
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

    pub async fn update_node(&mut self, client: &reqwest::Client, base_url: &str) -> JobResult {
        let cluster = self.node.cluster.clone().unwrap();
        if let Ok(nodes) = inventories::fetch_nodes(&client, base_url, &self.site, &cluster).await {
            let node: Node = nodes
                .into_iter()
                .find(|node| node.uid == self.node.uid)
                .unwrap();

            debug!(
                "Cluster : {} ; Node : {} ; os : {:?}",
                cluster, node.uid, node.operating_system
            );
            self.node = node;
        } else {
            warn!("Could not gather nodes");
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
        os_flavor: String,
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
                if let Some((site, _cluster, node)) = cluster_nodes.get(index) {
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
                        while false {//!within_time_window(scripts::WALLTIME) {
                            info!(
                                "Too close of day|night boundaries for {} WALLTIME",
                                scripts::WALLTIME
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
                            configs::generate_core_values(node.architecture.nb_cores);
                        let mut job = Job::new(
                            self.jobs.len(),
                            node.clone(),
                            core_values,
                            site.to_string(),
                            scripts_dir,
                            results_dir,
                            os_flavor.clone(),
                        );
                        fs::create_dir_all(
                            std::path::Path::new(&job.script_file).parent().unwrap(),
                        )?;
                        fs::create_dir_all(results_dir)?;

                        scripts::generate_script_file(&job, events_by_vendor)?;

                        job.submit_job().await?;
                        self.jobs.push(job);
                        info!("Job submitted for {} node", node_uid);
                        debug!("Wait 300 ms before another submission");
                        tokio::time::sleep(std::time::Duration::from_millis(2000)).await;

                        let client = reqwest::Client::builder().build()?;
                        self.check_unfinished_jobs(&client, super::BASE_URL, jobs_file)
                            .await?;

                        // Throttling based on the maximum allowed concurrent jobs
                    } else {
                        info!("Job already listed on {} node, skipping", node_uid);
                        tokio::time::sleep(std::time::Duration::from_millis(10)).await;
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
        info!("Checking unfinished job");
        for job in self.jobs.iter_mut().filter(|j| !j.finished()) {
            job.update_job_state(client, base_url).await?;
            if !job.finished() {
                info!(
                    "Job {:?} is still in '{}' state.",
                    job.oar_job_id, job.state
                );
            }
            tokio::time::sleep(std::time::Duration::from_millis(2000)).await;
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

pub fn rsync_results(site: &str, results_dir: &str, root_results_dir: &str) -> JobResult {
    let remote_directory = format!("{}:/home/nleblond/{}", site, root_results_dir);
    let mut p = Popen::create(
        &["rsync", "-avzP", &remote_directory, "."],
        PopenConfig {
            stdout: Redirection::Pipe,
            ..Default::default()
        },
    )?;

    let (out, err) = p.communicate(None)?;

    if let Ok(Some(exit_status)) = p.wait_timeout(std::time::Duration::from_secs(120)) {
        if exit_status.success() {
            debug!("Rsync with site {} done.\n{:?}", site, out);
        } else {
            debug!("Rsync with site {} failed.\n{:?} ; {:?}", site, out, err);
            return Err(JobError::UnknownState("Rsync failed".to_string()));
        }
    } else {
        p.terminate()?;
    }
    let checksum_file = format!("{}.tar.xz.md5", results_dir);
    let mut p = Popen::create(
        &["md5sum", "-c", &checksum_file],
        PopenConfig {
            stdout: Redirection::Pipe,
            ..Default::default()
        },
    )?;

    let (out, err) = p.communicate(None)?;

    if let Ok(Some(exit_status)) = p.wait_timeout(std::time::Duration::from_secs(120)) {
        if exit_status.success() {
            debug!("Checksum success.\n{:?}", out);
        } else {
            debug!("Checksum fail.\n{:?} ; {:?}", out, err);
            return Err(JobError::UnknownState("Checksum failed".to_string()));
        }
    } else {
        p.terminate()?;
    }

    Ok(())
}

fn extract_tar_xz(dir_path: &str) -> Result<(), String> {
    let dir = Path::new(dir_path);

    let tar_xz_name = match dir.file_name() {
        Some(name) => {
            let mut archive_name = PathBuf::from(name);
            archive_name.set_extension("tar.xz");
            archive_name
        }
        None => return Err("Failed to compute archive name from directory path.".to_string()),
    };

    let archive_path = dir
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(&tar_xz_name);

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
        .map_err(|e| format!("Failed to execute tar command stripping 5: {}", e))
        .unwrap();

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

fn parse_walltime(walltime: &str) -> Option<Duration> {
    let parts: Vec<&str> = walltime.split(':').collect();
    match parts.len() {
        1 => parts[0].parse::<i64>().ok().map(|h| Duration::hours(h)),
        2 => {
            let hours = parts[0].parse::<i64>().ok()?;
            let minutes = parts[1].parse::<i64>().ok()?;
            Some(Duration::hours(hours) + Duration::minutes(minutes))
        }
        3 => {
            let hours = parts[0].parse::<i64>().ok()?;
            let minutes = parts[1].parse::<i64>().ok()?;
            let seconds = parts[2].parse::<i64>().ok()?;
            Some(Duration::hours(hours) + Duration::minutes(minutes) + Duration::seconds(seconds))
        }
        _ => None,
    }
}

fn within_time_window(walltime: &str) -> bool {
    let now = Local::now();
    let current_hour = now.hour() as i64;
    let walltime_duration = parse_walltime(walltime).unwrap_or_else(|| Duration::hours(0));
    let adjusted_hour = (current_hour + walltime_duration.num_hours()) % 24;
    if adjusted_hour > G5K_DAY_BOTTOM_BOUNDARY
        && adjusted_hour < G5K_DAY_UP_BOUNDARY
        && current_hour >= G5K_DAY_BOTTOM_BOUNDARY
    {
        return true;
    }
    if adjusted_hour > G5K_DAY_UP_BOUNDARY && current_hour > G5K_DAY_UP_BOUNDARY {
        return true;
    }
    if adjusted_hour < G5K_DAY_BOTTOM_BOUNDARY && current_hour < G5K_DAY_BOTTOM_BOUNDARY {
        return true;
    }
    if adjusted_hour < G5K_DAY_BOTTOM_BOUNDARY && current_hour > G5K_DAY_UP_BOUNDARY {
        return true;
    }
    return false;
}
