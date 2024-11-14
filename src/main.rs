mod configs;
mod inventories;
mod jobs;
mod results;
mod scripts;
mod ssh;

use crate::jobs::Jobs;
use chrono::Local;
use derive_more::Display;
use env_logger::Builder;
use inventories::StrOrFloat;
use log::{debug, error, info, LevelFilter};
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::env;
use std::io::{self, Write};
use std::vec::IntoIter;
use std::{fmt, fs, time::Duration};
use thiserror::Error;

const SUPPORTED_PROCESSOR_VENDOR: &[&str; 3] = &["Intel", "AMD", "Cavium"];
const SLEEP_CHECK_TIME_IN_SECONDES: u64 = 300;
const BASE_URL: &str = "https://api.grid5000.fr/stable"; // URL de base de l'API
const LOGS_DIRECTORY: &str = "logs.d";
const INVENTORIES_DIRECTORY: &str = "inventories.d";
const JOBS_FILE: &str = "jobs.yaml";
const SCRIPTS_DIRECTORY: &str = "scripts.d";
const RESULTS_DIRECTORY: &str = "results.d";
const CONFIG_FILE: &str = "config/events_by_vendor.json";
//
type BenchmarkResult = Result<(), BenchmarkError>;
#[derive(Error, Debug)]
pub enum BenchmarkError {
    #[error("Inventory generation failed: {0}")]
    Inventory(#[from] inventories::InventoryError),
    #[error("Jobs processing failed: {0}")]
    Job(#[from] jobs::JobError),
    #[error("Script generation failed: {0}")]
    Script(#[from] scripts::ScriptError),
    #[error("Serde JSON parsing failed: {0}")]
    SerdeJSON(#[from] serde_json::Error),
    #[error("Serde YAML parsing failed: {0}")]
    SerdeYAML(#[from] serde_yaml::Error),
    #[error("Could not create script file : {0}")]
    Fs(#[from] std::io::Error),
    #[error("Http error : {0}")]
    HttpRequest(#[from] reqwest::Error),
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

#[derive(Debug, PartialEq, Serialize, Deserialize)]
pub struct MicroarchitectureEvents {
    name: String,
    versions: Vec<StrOrFloat>,
    perf_specific_events: PerfEvents,
    hwpc_specific_events: HwpcEvents,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
pub struct VendorEvents {
    name: String,
    microarchitectures: Vec<MicroarchitectureEvents>,
    perf_default_events: PerfEvents,
    hwpc_default_events: HwpcEvents,
}

#[derive(Debug, PartialEq, Serialize, Deserialize)]
pub struct EventsByVendor {
    vendors: Vec<VendorEvents>,
}

impl EventsByVendor {
    pub fn get_events(
        &self,
        vendor_name: &str,
        microarchitecture_name: &str,
        version: &StrOrFloat,
    ) -> (PerfEvents, HwpcEvents) {
        let mut perf_event_set: HashSet<String> = HashSet::new();
        let mut hwpc_event_sets: (HashSet<String>, HashSet<String>, HashSet<String>) =
            (HashSet::new(), HashSet::new(), HashSet::new());

        if let Some(vendor) = self.vendors.iter().find(|v| v.name == vendor_name) {
            if let Some(microarch) = vendor
                .microarchitectures
                .iter()
                .find(|m| m.name == microarchitecture_name && m.versions.contains(version))
            {
                perf_event_set.extend(microarch.perf_specific_events.0.iter().cloned());
                hwpc_event_sets
                    .0
                    .extend(microarch.hwpc_specific_events.rapl.iter().cloned());
                hwpc_event_sets
                    .1
                    .extend(microarch.hwpc_specific_events.msr.iter().cloned());
                hwpc_event_sets
                    .2
                    .extend(microarch.hwpc_specific_events.core.iter().cloned());
            }

            perf_event_set.extend(vendor.perf_default_events.0.iter().cloned());
            hwpc_event_sets
                .0
                .extend(vendor.hwpc_default_events.rapl.iter().cloned());
            hwpc_event_sets
                .1
                .extend(vendor.hwpc_default_events.msr.iter().cloned());
            hwpc_event_sets
                .2
                .extend(vendor.hwpc_default_events.core.iter().cloned());
        }

        let perf_events = PerfEvents(perf_event_set.into_iter().collect());
        let hwpc_events = HwpcEvents {
            rapl: hwpc_event_sets.0.into_iter().collect(),
            msr: hwpc_event_sets.1.into_iter().collect(),
            core: hwpc_event_sets.2.into_iter().collect(),
        };

        (perf_events, hwpc_events)
    }
}

// Creates all directories if not already existing
fn init_directories() -> BenchmarkResult {
    let directories = [
        LOGS_DIRECTORY,
        INVENTORIES_DIRECTORY,
        SCRIPTS_DIRECTORY,
        RESULTS_DIRECTORY,
    ];

    for dir in directories {
        debug!("Creating {} directory", dir);
        fs::create_dir_all(dir).map_err(|e| {
            eprintln!("Failed to create directory {}: {}", dir, e);
            e
        })?;
        debug!(
            "Successfully created or confirmed existing directory: {}",
            dir
        );
    }
    Ok(())
}

fn build_logger(log_level: &str) -> Result<(), log::SetLoggerError> {
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
        .try_init()
}

fn load_events_config() -> Result<EventsByVendor, std::io::Error> {
    let content = fs::read_to_string(CONFIG_FILE)?;
    let events: EventsByVendor = serde_json::from_str(&content)?;
    Ok(events)
}

fn load_or_init_jobs() -> Result<Jobs, BenchmarkError> {
    if std::path::Path::new(JOBS_FILE).exists() {
        info!("Found jobs.yaml file, processing with existing jobs");
        let content = fs::read_to_string(JOBS_FILE)?;
        Ok(serde_yaml::from_str(&content)?)
    } else {
        info!("No jobs.yaml file found, starting with an empty job list");
        Ok(Jobs { jobs: Vec::new() })
    }
}

#[tokio::main]
async fn main() -> Result<(), BenchmarkError> {
    dotenv::dotenv().ok();
    let log_level = env::var("LOG_LEVEL").unwrap_or_else(|_| "debug".to_string());
    build_logger(&log_level).unwrap();
    info!("Starting Benchmarks!");
    debug!("LOG_LEVEL is : {:?}", &log_level);

    init_directories()?;

    let events_by_vendor = load_events_config()?;
    let mut jobs: Jobs = load_or_init_jobs()?;

    inventories::generate_inventory(INVENTORIES_DIRECTORY).await?;
    jobs.generate_jobs(
        JOBS_FILE,
        INVENTORIES_DIRECTORY,
        SCRIPTS_DIRECTORY,
        RESULTS_DIRECTORY,
        &events_by_vendor,
    )
    .await?;

    let client = reqwest::Client::builder().build()?;

    while !jobs.job_is_done() {
        debug!("Job not done!");
        jobs.check_unfinished_jobs(&client, BASE_URL, JOBS_FILE)
            .await?;
        tokio::time::sleep(Duration::from_secs(SLEEP_CHECK_TIME_IN_SECONDES)).await;
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn load_events_from_json(path: &str) -> EventsByVendor {
        let data = fs::read_to_string(path).expect("Unable to read file");
        serde_json::from_str(&data).expect("JSON was not well-formatted")
    }

    #[test]
    fn test_get_events_intel() {
        // Load the EventsByVendor data from a JSON file
        let events_data = load_events_from_json("config/events_by_vendor.json");

        // Test cases with known values (example values, adjust as needed)
        let vendor_name = "Intel";
        let microarchitecture_name = "Skylake";
        let version = StrOrFloat::Str("Gold 5118".to_string());

        // Expected values for Skylake v1 (replace with actual expected data)
        let mut expected_perf_events = PerfEvents(vec![
            "/power/energy-pkg/".to_string(),
            "/power/energy-ram/".to_string(),
        ]);
        expected_perf_events.0.sort();

        let mut expected_hwpc_events = HwpcEvents {
            rapl: vec![
                "RAPL_ENERGY_PKG".to_string(),
                "RAPL_ENERGY_DRAM".to_string(),
            ],
            msr: vec!["TSC".to_string(), "APERF".to_string(), "MPERF".to_string()],
            core: vec![
                "CPU_CLK_THREAD_UNHALTED:REF_P".to_string(),
                "CPU_CLK_THREAD_UNHALTED:THREAD_P".to_string(),
                "LLC_MISSES".to_string(),
                "INSTRUCTIONS_RETIRED".to_string(),
            ],
        };
        expected_hwpc_events.rapl.sort();
        expected_hwpc_events.msr.sort();
        expected_hwpc_events.core.sort();

        // Call get_events with specific vendor, microarchitecture, and version
        let (mut perf_events, mut hwpc_events) =
            events_data.get_events(vendor_name, microarchitecture_name, &version);
        perf_events.0.sort();
        hwpc_events.rapl.sort();
        hwpc_events.msr.sort();
        hwpc_events.core.sort();

        // Assert that the returned events match the expected ones
        assert_eq!(perf_events, expected_perf_events);
        assert_eq!(hwpc_events, expected_hwpc_events);
    }

    #[test]
    fn test_get_events_amd() {
        // Load the EventsByVendor data from a JSON file
        let events_data = load_events_from_json("config/events_by_vendor.json");

        // Test cases with known values (example values, adjust as needed)
        let vendor_name = "AMD";
        let microarchitecture_name = "Zen 2";
        let version = StrOrFloat::Float(7352.0);

        // Expected values for Skylake v1 (replace with actual expected data)
        let mut expected_perf_events = PerfEvents(vec!["/power/energy-pkg/".to_string()]);
        expected_perf_events.0.sort();

        let mut expected_hwpc_events = HwpcEvents {
            rapl: vec!["RAPL_ENERGY_PKG".to_string()],
            msr: vec!["TSC".to_string(), "APERF".to_string(), "MPERF".to_string()],
            core: vec![
                "CYCLES_NOT_IN_HALTS".to_string(),
                "RETIRED_INSTRUCTIONS".to_string(),
                "RETIRED_UOPS".to_string(),
            ],
        };
        expected_hwpc_events.rapl.sort();
        expected_hwpc_events.msr.sort();
        expected_hwpc_events.core.sort();

        // Call get_events with specific vendor, microarchitecture, and version
        let (mut perf_events, mut hwpc_events) =
            events_data.get_events(vendor_name, microarchitecture_name, &version);

        perf_events.0.sort();
        hwpc_events.rapl.sort();
        hwpc_events.msr.sort();
        hwpc_events.core.sort();

        // Assert that the returned events match the expected ones
        assert_eq!(perf_events, expected_perf_events);
        assert_eq!(hwpc_events, expected_hwpc_events);
    }

    #[test]
    fn test_get_events_with_nonexistent_values() {
        let events_data = load_events_from_json("config/events_by_vendor.json");

        // Use values that do not exist in the dataset
        let vendor_name = "NonexistentVendor";
        let microarchitecture_name = "NonexistentArch";
        let version = StrOrFloat::Str("nonexistent_version".to_string());

        // Expect empty results for nonexistent entries
        let expected_perf_events = PerfEvents(vec![]);
        let expected_hwpc_events = HwpcEvents {
            rapl: vec![],
            msr: vec![],
            core: vec![],
        };

        let (perf_events, hwpc_events) =
            events_data.get_events(vendor_name, microarchitecture_name, &version);

        assert_eq!(perf_events, expected_perf_events);
        assert_eq!(hwpc_events, expected_hwpc_events);
    }
}
