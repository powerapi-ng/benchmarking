mod configs;
mod inventories;
mod jobs;
mod logging;
mod results;
mod scripts;

use crate::jobs::Jobs;
use chrono::Local;
use derive_more::Display;
use env_logger::Builder;
use log::{debug, error, info, warn, LevelFilter};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::collections::HashSet;
use std::env;
use std::io::{self, Write};
use std::vec::IntoIter;
use std::{fmt, fs, thread, time::Duration};
use thiserror::Error;
use tokio;

#[derive(Error, Debug)]
pub enum BenchmarkError {
    #[error("Inventory generation failed: {0}")]
    InventoryError(#[from] inventories::InventoryError),
    #[error("Jobs processing failed: {0}")]
    JobError(#[from] jobs::JobError),
    #[error("Script generation failed: {0}")]
    ScriptError(#[from] scripts::ScriptError),
    #[error("Serde JSON parsing failed: {0}")]
    SerdeJSONError(#[from] serde_json::Error),
    #[error("Serde YAML parsing failed: {0}")]
    SerdeYAMLError(#[from] serde_yaml::Error),
    #[error("Could not create script file : {0}")]
    FsError(#[from] std::io::Error),
    #[error("Http error : {0}")]
    HttpRequestError(#[from] reqwest::Error), //    #[error("Results processing failed: {0}")]
                                              //    ResultError(#[from] results::ResultError),
}

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct HwpcEvents {
    rapl: Vec<String>,
    msr: Vec<String>,
    core: Vec<String>,
}

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PerfEvents(Vec<String>);
impl Display for PerfEvents {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "PerfEvents: {:?}", self)
    }
}
impl IntoIterator for PerfEvents {
    type Item = String;
    type IntoIter = IntoIter<String>;

    fn into_iter(self) -> Self::IntoIter {
        self.0.into_iter()
    }
}

impl PerfEvents {
    pub fn iter(&self) -> std::slice::Iter<String> {
        self.0.iter()
    }
}

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct MicroarchitectureEvents {
    name: String,
    versions: Vec<String>,
    perf_specific_events: PerfEvents,
    hwpc_specific_events: HwpcEvents,
}

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct VendorEvents {
    name: String,
    microarchitectures: Vec<MicroarchitectureEvents>,
    perf_default_events: PerfEvents,
    hwpc_default_events: HwpcEvents,
}

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct EventsByVendor {
    vendors: Vec<VendorEvents>,
}

impl EventsByVendor {
    pub fn get_events(
        &self,
        vendor_name: &str,
        microarchitecture_name: &str,
        version: &str,
    ) -> (PerfEvents, HwpcEvents) {
        let mut perf_event_set: HashSet<String> = HashSet::new();
        let mut rapl_set: HashSet<String> = HashSet::new();
        let mut msr_set: HashSet<String> = HashSet::new();
        let mut core_set: HashSet<String> = HashSet::new();

        for vendor in &self.vendors {
            if vendor.name == vendor_name {
                for microarchitecture in &vendor.microarchitectures {
                    if microarchitecture.name == microarchitecture_name
                        && microarchitecture.versions.contains(&version.to_string())
                    {
                        for event in &microarchitecture.perf_specific_events.0 {
                            perf_event_set.insert(event.clone());
                        }

                        for event in &microarchitecture.hwpc_specific_events.rapl {
                            rapl_set.insert(event.clone());
                        }
                        for event in &microarchitecture.hwpc_specific_events.msr {
                            msr_set.insert(event.clone());
                        }
                        for event in &microarchitecture.hwpc_specific_events.core {
                            core_set.insert(event.clone());
                        }
                    }
                }

                for event in &vendor.perf_default_events.0 {
                    perf_event_set.insert(event.clone());
                }
                for event in &vendor.hwpc_default_events.rapl {
                    rapl_set.insert(event.clone());
                }
                for event in &vendor.hwpc_default_events.msr {
                    msr_set.insert(event.clone());
                }
                for event in &vendor.hwpc_default_events.core {
                    core_set.insert(event.clone());
                }
            }
        }

        let perf_events = perf_event_set.into_iter().collect();
        let hwpc_events = HwpcEvents {
            rapl: rapl_set.into_iter().collect(),
            msr: msr_set.into_iter().collect(),
            core: core_set.into_iter().collect(),
        };

        (PerfEvents(perf_events), hwpc_events)
    }
}

const LOGS_DIRECTORY: &str = "logs.d";
const INVENTORIES_DIRECTORY: &str = "inventories.d";
const JOBS_FILE: &str = "jobs.yaml";
const SCRIPTS_DIRECTORY: &str = "scripts.d";
const RESULTS_DIRECTORY: &str = "results.d";

// Creates all directories if not already existing
fn init_directories() {
    let directories = [
        LOGS_DIRECTORY,
        INVENTORIES_DIRECTORY,
        SCRIPTS_DIRECTORY,
        RESULTS_DIRECTORY,
    ];

    for dir in directories {
        debug!("Creating {} directory", dir);
        fs::create_dir_all(dir).expect("Could not create directory");
    }
}

// Ask users if he wants to skip unfinished jobs found in JOBS_DIRECTORY
fn skip_remaining_jobs() -> bool {
    let mut input = String::new();
    print!("Remaining JOBS found. Skip those? [y, N]: ");
    io::stdout().flush().unwrap();
    io::stdin()
        .read_line(&mut input)
        .expect("Failed to read line");

    matches!(input.trim(), "y" | "Y")
}

// Set the logger according to log_level (default to DEBUG, can be set thought ENV_VAR)
fn build_logger(log_level: &str) {
    Builder::new()
        .filter(None, log_level.parse().unwrap_or(LevelFilter::Debug))
        .format(|buf, record| {
            let datetime = Local::now().format("%Y-%m-%d %H:%M:%S");
            writeln!(
                buf,
                "[{}] - [{}] - [{}] - {}",
                datetime,
                record.level(),
                record.target(),
                record.args()
            )
        })
        .init();
}

#[tokio::main]
async fn main() -> Result<(), BenchmarkError> {
    // Set up logging
    {
        let log_level = env::var("LOG_LEVEL").unwrap_or_else(|_| "debug".to_string());
        build_logger(&log_level);
        info!("Starting Benchmarks!");
        debug!("LOG_LEVEL is : {:?}", &log_level);
    }

    // Create all directories
    init_directories();

    // Check if user wants to process unfinished JOBS
    // no -> from "generate_inventory" step
    // yes -> from "process jobs" step
    let events_by_vendor_content = std::fs::read_to_string("config/test.json")?;
    let events_by_vendor = serde_json::from_str(&events_by_vendor_content)?;
    let mut jobs: Jobs;
    if skip_remaining_jobs() {
        println!("Skipping !");
        info!("Skipping found unfinished JOBS !");
        inventories::generate_inventory(INVENTORIES_DIRECTORY).await?;
        jobs = jobs::generate_jobs(
            JOBS_FILE,
            INVENTORIES_DIRECTORY,
            SCRIPTS_DIRECTORY,
            RESULTS_DIRECTORY,
            &events_by_vendor,
        )
        .unwrap();
        jobs = jobs.submit_jobs().await?;
    } else {
        println!("Not Skipping !");
        let jobs_file_content = std::fs::read_to_string(JOBS_FILE)?;
        jobs = serde_yaml::from_str(&jobs_file_content)?;
    }

    dotenv::dotenv().ok(); // Charger les variables d'environnement
    let base_url = "https://api.grid5000.fr/stable/sites/"; // URL de base de l'API
    let client = reqwest::Client::builder().build()?;

    while !jobs.job_is_done() {
        info!("Job not done!");

        jobs = jobs
            .check_unfinished_jobs(&client, base_url, JOBS_FILE)
            .await?;

        tokio::time::sleep(Duration::from_secs(10)).await;
    }
    Ok(())
}
