use log::{debug, error, warn};
use serde::{Deserialize, Serialize};
use std::fs;
use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::path::{Path, PathBuf};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ResultError {
    #[error("Could not parse CSV File : {0}")]
    Csv(#[from] csv::Error),
}

#[derive(Debug, Deserialize, Serialize, PartialEq)]
struct HwpcRowRaw {
    timestamp: i64,
    sensor: String,
    target: String,
    socket: i32,
    cpu: i32,
    RAPL_ENERGY_PKG: Option<i64>,
    RAPL_ENERGY_DRAM: Option<i64>,
    RAPL_ENERGY_CORES: Option<i64>,
    time_enabled: i64,
    time_running: i64,
}

#[derive(Debug, Deserialize, Serialize, PartialEq)]
struct HwpcRow {
    timestamp: i64,
    sensor: String,
    target: String,
    socket: i32,
    cpu: i32,
    rapl_energy_pkg: Option<i64>,
    rapl_energy_dram: Option<i64>,
    rapl_energy_cores: Option<i64>,
    time_enabled: i64,
    time_running: i64,
    nb_core: i32,
    nb_ops_per_core: i32,
    iteration: usize,
}

impl HwpcRow {
    fn from_raw_record(
        raw_record: HwpcRowRaw,
        nb_core: i32,
        nb_ops_per_core: i32,
        iteration: usize,
    ) -> Self {
        HwpcRow {
            timestamp: raw_record.timestamp,
            sensor: raw_record.sensor,
            target: raw_record.target,
            socket: raw_record.socket,
            cpu: raw_record.cpu,
            rapl_energy_pkg: raw_record.RAPL_ENERGY_PKG,
            rapl_energy_dram: raw_record.RAPL_ENERGY_DRAM,
            rapl_energy_cores: raw_record.RAPL_ENERGY_CORES,
            time_enabled: raw_record.time_enabled,
            time_running: raw_record.time_running,
            nb_core,
            nb_ops_per_core,
            iteration,
        }
    }
}

#[derive(Debug, Deserialize, Serialize, PartialEq)]
struct PerfRow {
    power_energy_pkg: Option<f64>,
    power_energy_ram: Option<f64>,
    power_energy_cores: Option<f64>,
    time_elapsed: f64,
    nb_core: i32,
    nb_ops_per_core: i32,
    iteration: usize,
}

/// Creates an aggregation of perf_<KIND>_<NB_CPU>_<NB_OPS_PER_CPU> into corresponding perf_alone_<NB_CPU>_<NB_OPS_PER_CPU>.csv file
fn aggregate_perf(raw_perf_results_file: PathBuf) -> io::Result<()> {
    let output_path = &format!("{}.csv", raw_perf_results_file.display());
    fs::File::create(output_path)?;
    let mut output_writer = csv::Writer::from_path(output_path)?;

    if let Some((nb_core, nb_ops_per_core)) =
        parse_perf_metadata(raw_perf_results_file.file_name().unwrap().to_str().unwrap())
    {
        let raw_perf_results_file = File::open(raw_perf_results_file)?;
        let reader = BufReader::new(raw_perf_results_file);
        let mut iteration = 1;
        let mut cores_joules = None;
        let mut pkg_joules = None;
        let mut ram_joules = None;
        let mut time_elapsed = None;

        for line in reader.lines() {
            let line = line?;
            if line.contains("power/energy-cores/") {
                if let Some(value) = line.trim().split_whitespace().next() {
                    cores_joules = Some(value.replace(',', "").parse::<f64>().unwrap_or_default());
                }
            } else if line.contains("power/energy-pkg/") {
                if let Some(value) = line.trim().split_whitespace().next() {
                    pkg_joules = Some(value.replace(',', "").parse::<f64>().unwrap_or_default());
                }
            } else if line.contains("power/energy-ram/") {
                if let Some(value) = line.trim().split_whitespace().next() {
                    ram_joules = Some(value.replace(',', "").parse::<f64>().unwrap_or_default());
                }
            } else if line.contains("seconds time elapsed") {
                if let Some(value) = line.trim().split_whitespace().next() {
                    time_elapsed = Some(value.parse::<f64>().unwrap_or_default());
                }
                let perf_row = PerfRow {
                    power_energy_pkg: pkg_joules,
                    power_energy_ram: ram_joules,
                    power_energy_cores: cores_joules,
                    time_elapsed: time_elapsed.unwrap(),
                    nb_core: nb_core.parse::<i32>().unwrap(),
                    nb_ops_per_core: nb_ops_per_core.parse::<i32>().unwrap(),
                    iteration,
                };
                output_writer.serialize(perf_row)?;
                iteration += 1;
                cores_joules = None;
                pkg_joules = None;
                ram_joules = None;
                time_elapsed = None; // Reset for the next iteration
            }
        }
    } else {
        warn!(
            "Could not parse metadata from file name: {:?}",
            raw_perf_results_file
        );
    }

    Ok(())
}

fn parse_perf_metadata(file_name: &str) -> Option<(String, String)> {
    if let Some(file_name) = Path::new(file_name)
        .file_name()
        .and_then(|os_str| os_str.to_str())
    {
        let parts: Vec<&str> = file_name.split('_').collect();
        if parts.len() == 4 {
            if let (Ok(nb_core), Ok(nb_ops_per_core)) =
                (parts[2].parse::<u32>(), parts[3].parse::<u32>())
            {
                return Some((nb_core.to_string(), nb_ops_per_core.to_string()));
            }
        } else if parts.len() == 5 {
            if let (Ok(nb_core), Ok(nb_ops_per_core)) =
                (parts[3].parse::<u32>(), parts[4].parse::<u32>())
            {
                return Some((nb_core.to_string(), nb_ops_per_core.to_string()));
            }
        }
    } else {
        warn!("Could not parse filename {} to get metadata", file_name);
    }
    None
}

fn parse_hwpc_metadata(dir_name: &str) -> Option<(i32, i32, usize)> {
    if let Some(dir_name) = Path::new(dir_name)
        .file_name()
        .and_then(|os_str| os_str.to_str())
    {
        let parts: Vec<&str> = dir_name.split('_').collect();
        if parts.len() == 5 {
            if let (Ok(nb_core), Ok(nb_ops_per_core), Ok(iteration)) = (
                parts[2].parse::<i32>(),
                parts[3].parse::<i32>(),
                parts[4].parse::<usize>(),
            ) {
                return Some((nb_core, nb_ops_per_core, iteration));
            }
        } else if parts.len() == 6 {
            if let (Ok(nb_core), Ok(nb_ops_per_core), Ok(iteration)) = (
                parts[3].parse::<i32>(),
                parts[4].parse::<i32>(),
                parts[5].parse::<usize>(),
            ) {
                return Some((nb_core, nb_ops_per_core, iteration));
            }
        }
    } else {
        warn!("Could not parse filename {} to get metadata", dir_name);
    }
    None
}

fn aggregate_hwpc_file(
    raw_rapl_file: &Path,
    output_path: &str,
    nb_core: i32,
    nb_ops_per_core: i32,
    iteration: usize,
) -> io::Result<()> {
    let file_exists = std::fs::metadata(output_path).is_ok();
    let file = std::fs::OpenOptions::new()
        .write(true)
        .create(true)
        .append(true)
        .open(output_path)?;

    let mut output_writer = csv::WriterBuilder::new()
        .has_headers(!file_exists)
        .from_writer(file);

    if let Ok(mut reader) = csv::Reader::from_path(raw_rapl_file) {
        let iter = reader.deserialize::<HwpcRowRaw>();

        for hwpc_row_raw in iter {
            match hwpc_row_raw {
                Ok(row_raw) => {
                    let hwpc_raw =
                        HwpcRow::from_raw_record(row_raw, nb_core, nb_ops_per_core, iteration);
                    output_writer.serialize(hwpc_raw)?;
                }
                Err(e) => {
                    warn!("Raw row malformed : {}", e);
                }
            }
        }
    } else {
        warn!("Could not open {}", output_path);
    }
    Ok(())
}

fn aggregate_hwpc_subdir(subdir: &fs::DirEntry, output_path: &str) -> io::Result<()> {
    let raw_rapl_file = subdir.path().join("rapl.csv");
    if let Some((nb_core, nb_ops_per_core, iteration)) =
        parse_hwpc_metadata(subdir.file_name().to_str().unwrap())
    {
        aggregate_hwpc_file(
            &raw_rapl_file,
            output_path,
            nb_core,
            nb_ops_per_core,
            iteration,
        )?;
    } else {
        warn!("Could not parse metadata from directory name: {:?}", subdir);
    }
    Ok(())
}

/// Creates an aggregation of hwpc_<KIND>_<NB_CPU>_<NB_OPS_PER_CPU> into corresponding hwpc_<KIND>_<NB_CPU>_<NB_OPS_PER_CPU>.csv file
fn aggregate_hwpc(raw_results_dir_path: PathBuf) -> io::Result<()> {
    let (output_parent, output_basename) = (
        raw_results_dir_path.parent().unwrap(),
        raw_results_dir_path.file_name().unwrap(),
    );
    let output_path = &format!(
        "{}/{}.csv",
        output_parent.to_str().unwrap(),
        output_basename.to_str().unwrap()
    );

    if Path::new(output_path).exists() {
        match fs::remove_file(output_path) {
            Ok(_) => debug!("File '{}' was deleted successfully.", output_path),
            Err(e) => error!("Failed to delete file '{}': {}", output_path, e),
        }
    }

    let mut raw_results_subdirs = Vec::new();

    if let Ok(entries) = fs::read_dir(&raw_results_dir_path) {
        raw_results_subdirs = entries
            .filter(|entry| entry.as_ref().unwrap().file_type().unwrap().is_dir())
            .collect();
    } else {
        warn!(
            "Could not find subdirectories in {} directory",
            output_parent.to_str().unwrap()
        );
    }

    assert!(raw_results_subdirs
        .iter()
        .map(|subdir| aggregate_hwpc_subdir(subdir.as_ref().unwrap(), output_path))
        .all(|result| result.is_ok()));

    Ok(())
}

fn filter_hwpc_dirs(directory: &str) -> Vec<PathBuf> {
    let mut filtered_files = Vec::new();

    if let Ok(entries) = fs::read_dir(directory) {
        for entry in entries {
            if let Ok(entry) = entry {
                let path = entry.path();
                if path.is_dir() {
                    if let Some(file_name) = path.file_name().and_then(|s| s.to_str()) {
                        if file_name.starts_with("hwpc") {
                            filtered_files.push(path);
                        }
                    }
                }
            }
        }
    }

    filtered_files
}

fn filter_perf_files(directory: &str) -> Vec<PathBuf> {
    let mut filtered_files = Vec::new();

    if let Ok(entries) = fs::read_dir(directory) {
        for entry in entries {
            if let Ok(entry) = entry {
                let path = entry.path();
                if path.is_file() {
                    if let Some(file_name) = path.file_name().and_then(|s| s.to_str()) {
                        if file_name.starts_with("perf_") && !file_name.ends_with(".csv") {
                            filtered_files.push(path);
                        }
                    }
                }
            }
        }
    }

    filtered_files
}
pub fn process_results(results_directory: &str) -> io::Result<()> {
    let perf_raw_files = filter_perf_files(results_directory);
    assert!(perf_raw_files
        .iter()
        .map(|perf_raw_file| aggregate_perf(perf_raw_file.to_path_buf()))
        .all(|result| result.is_ok()));

    let hwpc_raw_dirs = filter_hwpc_dirs(results_directory);
    assert!(hwpc_raw_dirs
        .iter()
        .map(|hwpc_raw_results_dir| aggregate_hwpc(hwpc_raw_results_dir.to_path_buf()))
        .all(|result| result.is_ok()));

    Ok(())
}
