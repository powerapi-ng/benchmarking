use crate::HwpcEvents;
use std::collections::HashMap;
use std::fmt;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ConfigError {
    #[error("Could not read/create file : {0}")]
    Fs(#[from] std::io::Error),
    #[error("Serde JSON parsing failed: {0}")]
    SerdeJSON(#[from] serde_json::Error),
}

#[derive(Debug, Clone)]
pub struct HwpcConfig {
    pub name: String,
    pub verbose: bool,
    pub cgroup_basepath: String,
    pub frequency: u32,
    pub output: HwpcOutput,
    pub system: HwpcSystem,
}
impl fmt::Display for HwpcConfig {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "name: {},\nverbose: {},\ncgroup_basepath: {},\nfrequency: {},\noutput: {},\nsystem: {}", self.name, self.verbose, self.system, self.frequency, self.output, self.system)
    }
}

#[derive(Debug, Clone)]
pub struct HwpcOutput {
    pub r#type: String,
    pub directory: String,
}
impl fmt::Display for HwpcOutput {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "type: {},\ndirectory: {}", self.r#type, self.directory)
    }
}

#[derive(Debug, Clone)]
pub struct HwpcSystem {
    pub rapl: HwpcSystemRapl,
    pub msr: HwpcSystemMsr,
    pub core: HwpcSystemCore,
}
impl fmt::Display for HwpcSystem {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "HwpcSystem(rapl: {},\nmsr: {},\ncore: {})",
            self.rapl, self.msr, self.core
        )
    }
}

#[derive(Debug, Clone)]
pub struct HwpcSystemRapl {
    pub events: Vec<String>,
    pub monitoring_type: String,
}
impl fmt::Display for HwpcSystemRapl {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "HwpcSystemRapl(events: {:?},\nmonitoring_type: {})",
            self.events, self.monitoring_type
        )
    }
}

#[derive(Debug, Clone)]
pub struct HwpcSystemMsr {
    pub events: Vec<String>,
}
impl fmt::Display for HwpcSystemMsr {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "events: {:?}", self.events)
    }
}

#[derive(Debug, Clone)]
pub struct HwpcSystemCore {
    pub events: Vec<String>,
}
impl fmt::Display for HwpcSystemCore {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "events: {:?}", self.events)
    }
}

pub fn generate_hwpc_configs(
    hwpc_events: &HwpcEvents,
    results_dir: &str,
    core_values: &Vec<u32>,
    prefix: &str,
) -> HashMap<u32, HwpcConfig> {
    let mut hwpc_configs = HashMap::new();

    let hwpc_system_rapl = HwpcSystemRapl {
        events: hwpc_events.rapl.clone(),
        monitoring_type: "MONITOR_ONE_CPU_PER_SOCKET".to_owned(),
    };
    let hwpc_system_msr = HwpcSystemMsr {
        events: hwpc_events.msr.clone(),
    };
    let hwpc_system_core = HwpcSystemCore {
        events: hwpc_events.core.clone(),
    };

    let hwpc_system = HwpcSystem {
        rapl: hwpc_system_rapl,
        msr: hwpc_system_msr,
        core: hwpc_system_core,
    };

    for core_value in core_values {
        let hwpc_output = HwpcOutput {
            r#type: "csv".to_owned(),
            directory: format!("{}/{}_{}", results_dir, prefix, core_value),
        };

        let hwpc_config = HwpcConfig {
            name: format!("{}_sensor_{}", prefix, core_value),
            verbose: true,
            cgroup_basepath: "/sys/fs/cgroup/perf_event".to_owned(),
            frequency: 1000,
            output: hwpc_output,
            system: hwpc_system.clone(),
        };

        hwpc_configs.insert(*core_value, hwpc_config);
    }

    hwpc_configs
}
