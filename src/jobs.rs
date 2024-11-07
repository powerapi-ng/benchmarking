use crate::inventories;
use crate::inventories::Node;
use crate::scripts;
use crate::EventsByVendor;
use log::{error, info};
use openssh::{KnownHosts, Session, Stdio};
use openssh_sftp_client::Sftp;
use rand::Rng;
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_yaml::{self};
use std::collections::HashMap;
use std::env;
use std::fmt::{self, Display};
use std::fs;
use std::str::{self, FromStr};
use thiserror::Error;

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
    Sftp(#[from] openssh_sftp_client::Error),
    #[error("Could not get Inventories entries: {0}")]
    Inventory(#[from] inventories::InventoryError),
    #[error("Could not generate Scripts: {0}")]
    Script(#[from] scripts::ScriptError),
    #[error("HTTP request failed: {0}")]
    HttpRequest(#[from] reqwest::Error),
}

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
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

#[derive(Debug, Serialize, Deserialize)]
pub struct Job {
    pub id: usize,
    pub node: Node,
    pub oar_job_id: Option<u32>,
    pub state: OARState,
    pub tasks: Vec<String>,
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
        tasks: Vec<String>,
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
            tasks,
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
    pub async fn submit_job(&mut self) -> Result<&Self, JobError> {
        let site = self.site.clone();
        let session = ssh_connect(&site).await?;
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
        sftp_upload(&session, &self.script_file, &self.script_file).await?;
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

        Ok(self)
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Jobs {
    pub jobs: Vec<Job>,
}

impl Jobs {
    pub async fn submit_jobs(mut self) -> Result<Self, JobError> {
        // Submit job to site through reqwest
        //
        // Update OAR_JOB_ID field
        for job in self.jobs.iter_mut() {
            job.submit_job().await?;
        }

        Ok(self)
    }

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
                    "{}/{}/jobs/{}",
                    base_url,
                    &job.site,
                    &job.oar_job_id.unwrap()
                ),
            )
            .await
            .unwrap();
            let state: String = serde_json::from_value(response.get("state").unwrap().clone())?;
            job.state = OARState::from(&state);
            if job.finished() {
                info!(
                    "Job {:?} finished with statut : {}",
                    job.oar_job_id, job.state
                );
            } else {
                info!(
                    "Job {:?} is still in '{}' state.",
                    job.oar_job_id, job.state
                );
            }
        }
        self.dump_to_file(file_to_dump_to)?;
        Ok(self)
    }

    pub fn job_is_done(&self) -> bool {
        self.jobs.iter().all(|job| job.finished())
    }
    pub fn dump_to_file(&self, file_path: &str) -> Result<(), JobError> {
        if !std::path::Path::new(file_path).exists() {
            info!("Create Jobs File : '{}'", file_path);
        }
        let file = fs::File::create(file_path)?;
        serde_yaml::to_writer(file, self)?;
        Ok(())
    }
}
// Use OpenSSH client to create an ssh session
async fn ssh_connect(host: &str) -> Result<Session, JobError> {
    let session = Session::connect_mux(host, KnownHosts::Strict).await?;
    info!("SSH Connection established with {}", host);
    Ok(session)
}

// Use OpenSSH Session to upload files though SFTP
async fn sftp_upload(
    session: &Session,
    file_to_upload_path: &str,
    path_to_upload_file: &str,
) -> Result<(), JobError> {
    let content = std::fs::read_to_string(file_to_upload_path)?;
    let bytes_content = content.as_bytes();

    let mut child = session
        .subsystem("sftp")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .await?;

    let sftp = Sftp::new(
        child.stdin().take().unwrap(),
        child.stdout().take().unwrap(),
        Default::default(),
    )
    .await?;
    info!("SFTP Connection established");

    {
        let mut fs = sftp.fs();
        fs.write(path_to_upload_file, bytes_content).await?;
        info!(
            "Local file '{}' written to remote destination '{}'",
            file_to_upload_path, path_to_upload_file
        );
    }
    Ok(())
}

fn generate_core_values(n: usize, max: u32) -> Vec<u32> {
    let mut rng = rand::thread_rng();
    let mut values = Vec::new();

    for _ in 0..n {
        let mut value = 1 + rng.gen_range(1..=max);
        while value.is_power_of_two() {
            value = 1 + rng.gen_range(1..=max);
        }
        values.push(value);
    }

    values.sort_unstable();
    values.dedup();
    values
}

// Generate all jobs and store them in JOBS_FILE
pub fn generate_jobs(
    jobs_file: &str,
    inventories_dir: &str,
    scripts_dir: &str,
    results_dir: &str,
    events_by_vendor: &EventsByVendor,
) -> Result<Jobs, JobError> {
    let mut jobs: Vec<Job> = Vec::new();
    let tasks = vec!["HWPC".to_owned(), "PERF".to_owned(), "HWPC+PERF".to_owned()];

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

                let core_values = generate_core_values(7, node.architecture.nb_cores);
                let job = Job::new(
                    jobs.len(),
                    node,
                    tasks.clone(),
                    core_values,
                    script_file_path,
                    results_node_dir,
                    metadata_file_path,
                    site.clone(),
                );
                scripts::generate_script_file(&job, events_by_vendor)?;
                jobs.push(job);

            }
        }
    }
    println!("jobs file : {:?}", jobs_file);
    let jobs = Jobs { jobs };
    jobs.dump_to_file(jobs_file)?;
    Ok(jobs)
}
