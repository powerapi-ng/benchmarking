// Generate the whole script for each asked task, each asked nb_cores and a fixed nb_ops / core
use crate::configs;
use crate::configs::HwpcConfig;
use crate::jobs;
use crate::EventsByVendor;
use crate::PerfEvents;
use askama::Template;
use log::info;
use std::collections::HashMap;
use std::env;
use std::fs::File;
use std::io::Write;
use thiserror::Error;

#[derive(Template)]
#[template(path = "benchmark.sh", escape = "none")]
struct BenchmarkTemplate {
    perf_alone: bool,
    hwpc_alone: bool,
    hwpc_and_perf: bool,
    docker_hub_username: String,
    docker_hub_token: String,
    hwpc_alone_configs: HashMap<u32, HwpcConfig>,
    hwpc_and_perf_configs: HashMap<u32, HwpcConfig>,
    hwpc_home_directory: String,
    queue_type: String,
    node_uid: String,
    walltime: String,
    exotic_node: bool,
    results_directory: String,
    core_values: Vec<u32>,
    perf_events: PerfEvents,
    cpu_ops_by_core: u32,
}

impl BenchmarkTemplate {
    fn new(
        perf_alone: bool,
        hwpc_alone: bool,
        hwpc_and_perf: bool,
        docker_hub_username: String,
        docker_hub_token: String,
        hwpc_alone_configs: HashMap<u32, HwpcConfig>,
        hwpc_and_perf_configs: HashMap<u32, HwpcConfig>,
        hwpc_home_directory: Option<String>,
        queue_type: String,
        node_uid: String,
        walltime: String,
        exotic_node: bool,
        results_directory: String,
        core_values: Vec<u32>,
        perf_events: PerfEvents,
        cpu_ops_by_core: Option<u32>,
    ) -> Self {
        Self {
            perf_alone,
            hwpc_alone,
            hwpc_and_perf,
            docker_hub_username,
            docker_hub_token,
            hwpc_alone_configs,
            hwpc_and_perf_configs,
            hwpc_home_directory: hwpc_home_directory.unwrap_or_default(),
            queue_type,
            node_uid,
            walltime,
            exotic_node,
            results_directory,
            core_values,
            perf_events,
            cpu_ops_by_core: cpu_ops_by_core.unwrap_or_default(),
        }
    }
}

#[derive(Error, Debug)]
pub enum ScriptError {
    #[error("Could not create script file : {0}")]
    FsError(#[from] std::io::Error),
    #[error("Could not create HWPC Config files : {0}")]
    ConfigError(#[from] configs::ConfigError),
}

pub fn generate_script_file(
    job: &jobs::Job,
    events_by_vendor: &EventsByVendor,
) -> Result<(), ScriptError> {
    dotenv::dotenv().ok();
    info!("Creating file : {}", &job.script_file);
    let mut file = File::create(&job.script_file)?;
    info!("Created file : {}", &job.script_file);

    let (perf_events, hwpc_events) = events_by_vendor.get_events(
        &job.node.processor.vendor,
        &job.node.processor.microarchitecture,
        &job.node.processor.version.to_string(),
    );
    let hwpc_alone_configs = configs::generate_hwpc_configs(
        &hwpc_events,
        &job.results_dir,
        &job.core_values,
        "hwpc_alone",
    );
    let hwpc_and_perf_configs = configs::generate_hwpc_configs(
        &hwpc_events,
        &job.results_dir,
        &job.core_values,
        "hwpc_and_perf",
    );
    let benchmark = BenchmarkTemplate::new(
        true,
        true,
        true,
        env::var("DOCKER_HUB_USERNAME").expect("DOCKER_HUB_USERNAME must be set"),
        env::var("DOCKER_HUB_TOKEN").expect("DOCKER_HUB_TOKEN must be set"),
        hwpc_alone_configs,
        hwpc_and_perf_configs,
        Some("/app".to_owned()),
        "default".to_owned(),
        job.node.uid.clone(),
        "4".to_string(),
        job.node.exotic.clone(),
        job.results_dir.clone(),
        job.core_values.clone(),
        perf_events,
        Some(50_000),
    );
    let benchmark = benchmark.render().unwrap();
    file.write_all(benchmark.as_bytes())?;
    Ok(())
}
