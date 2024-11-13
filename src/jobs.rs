use super::EventsByVendor;
use crate::configs;
use crate::inventories::{self, Node};
use crate::scripts;
use crate::ssh;
use log::{error, info};
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_yaml::{self};
use std::collections::HashMap;
use std::fmt::{self, Display};
use std::str::{self, FromStr};
use std::time::Duration;
use std::{env, fs};
use subprocess::{Popen, PopenConfig, Redirection};
use thiserror::Error;

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
        match self {
            Self::Hold => write!(f, "Hold"),
            Self::Waiting => write!(f, "Waiting"),
            Self::Running => write!(f, "Running"),
            Self::Terminated => write!(f, "Terminated"),
            Self::Finishing => write!(f, "Finishing"),
            Self::Failed => write!(f, "Failed"),
            Self::NotSubmitted => write!(f, "NotSubmitted"),
            Self::UnknownState => write!(f, "UnknownState"),
        }
    }
}

impl OARState {
    fn from(state: &str) -> Self {
        match state {
            "running" => OARState::Running,
            "error" => OARState::Failed,
            "waiting" => OARState::Waiting,
            "terminated" => OARState::Terminated,
            "hold" => OARState::Hold,
            "finishing" => OARState::Finishing,
            &_ => OARState::UnknownState,
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
    pub metadata_file: String,
    pub site: String,
}

impl Job {
    fn new(
        id: usize,
        node: Node,
        core_values: Vec<u32>,
        script_file: String,
        results_dir: String,
        metadata_file: String,
        site: String,
    ) -> Self {
        Job {
            id,
            node,
            oar_job_id: None, // Submission through OAR will give this ID
            state: OARState::NotSubmitted, // Default init state
            core_values,
            script_file,
            results_dir,
            metadata_file,
            site,
        }
    }
    fn finished(&self) -> bool {
        self.state == OARState::Terminated || self.state == OARState::Failed
    }
    pub async fn submit_job(&mut self) -> JobResult {
        let site = self.site.clone();
        let session = ssh::ssh_connect(&site).await?;
        let script_directory_path = std::path::Path::new(&self.script_file)
            .parent() // Gets the parent directory
            .map(|s| s.to_string_lossy().into_owned())
            .unwrap();
        let mkdir_argument = format!("-p {}", script_directory_path);
        info!(
            "Command to be executed on host '{}' : {}",
            site, mkdir_argument
        );
        let _mkdir = session
            .command("mkdir")
            .arg("-p")
            .arg(&script_directory_path)
            .output()
            .await?;
        let re = Regex::new(r"OAR_JOB_ID=(\d+)").unwrap();
        ssh::sftp_upload(&session, &self.script_file, &self.script_file).await?;
        let _executable = session
            .command("chmod")
            .arg("u+x")
            .arg(&self.script_file)
            .output()
            .await?;

        let oarsub = session
            .command("oarsub")
            .arg("-S")
            .arg(&self.script_file)
            .output()
            .await?;

        if oarsub.status.success() {
            if let Some(captures) = re.captures(str::from_utf8(&oarsub.stdout).unwrap()) {
                if let Some(job_id_str) = captures.get(1) {
                    let oar_job_id = u32::from_str(job_id_str.as_str()).ok().unwrap();
                    self.oar_job_id = Some(oar_job_id);
                    self.state = OARState::Waiting;
                    info!(
                        "Job successfully submitted with OAR_JOB_ID : {}",
                        oar_job_id
                    );
                }
            } else {
                error!("Failed to parse a OAR_JOB_ID");
            }
        } else {
            self.state = OARState::Failed;
            error!("Command failed: {:?}", oarsub.stderr);
        }

        session.close().await?;

        Ok(())
    }

    pub async fn state_transition(&mut self, new_state: OARState) -> JobResult {
        self.state = new_state.clone();
        info!(
            "Job {} with OAR_JOB_ID {:?} changes from {} => {}",
            self.id, self.oar_job_id, self.state, new_state
        );

        match new_state {
            OARState::Terminated => self.job_teminated().await,
            OARState::Failed => self.job_teminated().await,
            _ => {
                error!(
                    "Transition to {} state is not implemented yet, no actions performed",
                    new_state
                );
                Ok(())
            }
        }
    }

    pub async fn job_teminated(&mut self) -> JobResult {
        let site = &self.site;
        let cluster = self.node.cluster.as_ref().unwrap();
        let node = &self.node.uid;

        rsync_results(site, cluster, node)?;

        Ok(())
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Jobs {
    pub jobs: Vec<Job>,
}

impl Jobs {
    pub async fn check_unfinished_jobs(
        mut self,
        client: &reqwest::Client,
        base_url: &str,
        file_to_dump_to: &str,
    ) -> Result<Self, JobError> {
        for job in self.jobs.iter_mut().filter(|j| !j.finished()) {
            let response: HashMap<String, serde_json::Value> = crate::inventories::get_api_call(
                client,
                &format!(
                    "{}/sites/{}/jobs/{}",
                    base_url,
                    &job.site,
                    &job.oar_job_id.unwrap()
                ),
            )
            .await
            .unwrap();
            let state: String = serde_json::from_value(response.get("state").unwrap().clone())?;
            let state = OARState::from(&state);
            if state != job.state {
                job.state_transition(state).await?;
            }
            if !job.finished() {
                info!(
                    "Job {:?} is still in '{}' state.",
                    job.oar_job_id, job.state
                );
            }
        }
        self.dump_to_file(file_to_dump_to)?;
        Ok(self)
    }
    fn nb_ongoing_jobs(&self) -> usize {
        self.jobs
            .to_owned()
            .iter()
            .filter(|j| !j.finished())
            .collect::<Vec<&Job>>()
            .len()
    }

    pub fn job_is_done(&self) -> bool {
        self.jobs.iter().all(|job| job.finished())
    }
    pub fn dump_to_file(&self, file_path: &str) -> JobResult {
        if !std::path::Path::new(file_path).exists() {
            info!("Create Jobs File : '{}'", file_path);
        }
        let file = fs::File::create(file_path)?;
        serde_yaml::to_writer(file, self)?;
        Ok(())
    }
}

// Generate all jobs and store them in JOBS_FILE
pub async fn generate_jobs(
    jobs_file: &str,
    inventories_dir: &str,
    scripts_dir: &str,
    results_dir: &str,
    events_by_vendor: &EventsByVendor,
) -> Result<Jobs, JobError> {
    let mut jobs: Jobs = Jobs { jobs: Vec::new() };

    let sites = inventories::get_inventory_sites(inventories_dir)?;
    for site in sites {
        let clusters = inventories::get_inventory_site_clusters(inventories_dir, &site)?;
        for cluster in clusters {
            let scripts_cluster_dir = format!("{}/{}/{}", scripts_dir, &site, cluster);
            let results_cluster_dir = format!("{}/{}/{}", results_dir, &site, cluster);
            fs::create_dir_all(&scripts_cluster_dir)?;

            let nodes =
                inventories::get_inventory_site_cluster_nodes(inventories_dir, &site, &cluster)?;
            if let Some(node_file) = nodes.first() {
                let metadata_file_path =
                    format!("{}/{}/{}/{}", inventories_dir, &site, &cluster, &node_file);
                let metadata_file_content = std::fs::read_to_string(&metadata_file_path)?;
                let node: Node = serde_json::from_str(&metadata_file_content)?;
                let node_uid = node.uid.clone();

                let script_file_path = format!("{}/{}.sh", &scripts_cluster_dir, &node_uid);
                let results_node_dir = format!("{}/{}", &results_cluster_dir, &node_uid);
                fs::create_dir_all(&results_node_dir)?;

                let core_values = configs::generate_core_values(5, node.architecture.nb_cores);
                let mut job = Job::new(
                    jobs.jobs.len(),
                    node,
                    core_values,
                    script_file_path,
                    results_node_dir,
                    metadata_file_path,
                    site.clone(),
                );
                let client = reqwest::Client::builder().build()?;
                scripts::generate_script_file(&job, events_by_vendor)?;
                job.submit_job().await?;
                jobs.jobs.push(job);
                jobs = jobs
                    .check_unfinished_jobs(&client, super::BASE_URL, jobs_file)
                    .await?;

                while jobs.nb_ongoing_jobs() >= MAX_CONCURRENT_JOBS {
                    info!("{} jobs are currently in [Waiting|Running|Finishing] state, waits before submitting more", MAX_CONCURRENT_JOBS);
                }
            }
        }
    }
    jobs.dump_to_file(jobs_file)?;
    Ok(jobs)
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
            info!("Rsync with site {} done.\n{:?}", site, out);
        } else {
            info!("Rsync with site {} failed.\n{:?} ; {:?}", site, out, err);
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
            info!("Checksum success.\n{:?}", out);
        } else {
            info!("Checksum fail.\n{:?} ; {:?}", out, err);
        }
    } else {
        p.terminate()?;
    }

    Ok(())
}
