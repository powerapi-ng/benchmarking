use crate::HwpcEvents;
use rand::Rng;
use serde::Serialize;
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

pub trait PrettyDisplay: serde::Serialize {
    fn fmt_pretty(&self) -> String {
        serde_json::to_string_pretty(self).unwrap_or_default()
    }
}

macro_rules! impl_pretty_display {
    ($($t:ty),+) => {
        $(
            impl PrettyDisplay for $t {}
            impl fmt::Display for $t {
                fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
                    write!(f, "{}", self.fmt_pretty())
                }
            }
        )+
    };
}

#[derive(Debug, Clone, Serialize)]
pub struct HwpcConfig {
    pub name: String,
    pub verbose: bool,
    pub cgroup_basepath: String,
    pub frequency: u32,
    pub output: HwpcOutput,
    pub system: HwpcSystem,
}

#[derive(Debug, Clone, Serialize)]
pub struct HwpcOutput {
    pub r#type: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct HwpcSystem {
    pub rapl: HwpcSystemRapl,
    pub msr: HwpcSystemMsr,
    pub core: HwpcSystemCore,
}

#[derive(Debug, Clone, Serialize)]
pub struct HwpcSystemRapl {
    pub events: Vec<String>,
    pub monitoring_type: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct HwpcSystemMsr {
    pub events: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct HwpcSystemCore {
    pub events: Vec<String>,
}

impl_pretty_display!(
    HwpcConfig,
    HwpcOutput,
    HwpcSystem,
    HwpcSystemRapl,
    HwpcSystemMsr
);

impl fmt::Display for HwpcSystemCore {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "{}",
            serde_json::to_string_pretty(self).unwrap_or_default()
        )
    }
}

pub fn generate_core_values(n: usize, max: u32) -> Vec<u32> {
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
    values.push(max);
    values.dedup();
    values
}

fn build_hwpc_system(hwpc_events: &HwpcEvents) -> HwpcSystem {
    HwpcSystem {
        rapl: HwpcSystemRapl {
            events: hwpc_events.rapl.clone(),
            monitoring_type: "MONITOR_ONE_CPU_PER_SOCKET".to_owned(),
        },
        msr: HwpcSystemMsr {
            events: hwpc_events.msr.clone(),
        },
        core: HwpcSystemCore {
            events: hwpc_events.core.clone(),
        },
    }
}

fn build_hwpc_config(name: String, system: HwpcSystem, os_flavor: &str) -> HwpcConfig {
    let cgroup_basepath;
    if os_flavor == "ubuntu2404-nfs" {
        cgroup_basepath = "/sys/fs/cgroup";
    } else {
        cgroup_basepath = "/sys/fs/cgroup/perf_event";
    }
    HwpcConfig {
        name,
        verbose: true,
        cgroup_basepath: cgroup_basepath.to_owned(),
        frequency: 1000,
        output: HwpcOutput {
            r#type: "csv".to_owned(),
        },
        system,
    }
}

pub fn generate_hwpc_configs(
    hwpc_events: &HwpcEvents,
    core_values: &[u32],
    prefix: &str,
    os_flavor: &str,
) -> HashMap<u32, HwpcConfig> {
    let hwpc_system = build_hwpc_system(hwpc_events);
    core_values
        .iter()
        .map(|&core_value| {
            let name = format!("{}_sensor_{}", prefix, core_value);
            (core_value, build_hwpc_config(name, hwpc_system.clone(), os_flavor))
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    const MAX_VALUE: u32 = 100;
    const NB_VALUE: usize = 10;

    #[test]
    fn test_generate_core_values() {
        let values = generate_core_values(NB_VALUE, MAX_VALUE);
        assert!(values.len() > 0);
        assert!(values
            .iter()
            .all(|&v| v <= MAX_VALUE && !v.is_power_of_two()));
    }

    #[test]
    fn test_max_is_present() {
        let values = generate_core_values(NB_VALUE, MAX_VALUE);
        assert!(values.contains(&MAX_VALUE));
    }
}
