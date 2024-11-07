use derive_more::Display;
use log::{debug, error, info};
use reqwest::Client;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use std::collections::HashMap;
use std::env;
use std::fs::File;
use std::fs::{self};
use std::io::Write;
use std::path::Path;
use thiserror::Error;

#[derive(Deserialize, Serialize, Debug)]
pub struct Node {
    pub uid: String,
    pub cluster: Option<String>,
    pub exotic: bool,
    pub processor: Processor,
    pub architecture: Architecture,
}

impl Node {
    pub fn as_bytes(&self) -> Result<Vec<u8>, InventoryError> {
        let json_data = serde_json::to_vec(self)?;
        Ok(json_data)
    }
}

#[derive(Deserialize, Serialize, Debug)]
pub struct Architecture {
    cpu_core_numbering: String,
    pub nb_cores: u32,
    nb_procs: i32,
    nb_threads: i32,
    platform_type: String,
}

#[derive(Debug, Clone, Display)]
pub enum StrOrFloat {
    Str(String),
    Float(f64),
}

impl StrOrFloat {
    fn as_bytes(&self) -> String {
        match self {
            StrOrFloat::Str(s) => s.clone(),
            StrOrFloat::Float(f) => f.to_string(),
        }
    }
}

impl Serialize for StrOrFloat {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        match self {
            StrOrFloat::Str(s) => serializer.serialize_str(s),
            StrOrFloat::Float(f) => serializer.serialize_f64(*f),
        }
    }
}
impl<'de> Deserialize<'de> for StrOrFloat {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let value = serde_json::Value::deserialize(deserializer)?;

        match value {
            serde_json::Value::String(s) => Ok(StrOrFloat::Str(s)),
            serde_json::Value::Number(n) => {
                if let Some(f) = n.as_f64() {
                    Ok(StrOrFloat::Float(f))
                } else {
                    Err(serde::de::Error::custom("Expected a floating point number"))
                }
            }
            _ => Err(serde::de::Error::custom(
                "Expected a string or a floating point number",
            )),
        }
    }
}

#[derive(Deserialize, Serialize, Debug)]
pub struct Processor {
    cache_l1: Option<i32>,
    cache_l1d: i32,
    cache_l1i: i32,
    cache_l2: i32,
    cache_l3: i32,
    clock_speed: i64,
    ht_capable: bool,
    instruction_set: String,
    pub microarchitecture: String,
    microcode: String,
    model: String,
    other_description: String,
    pub vendor: String,
    pub version: StrOrFloat, // Is sometimes another type, like f64, and then panic
}

#[derive(Deserialize, Debug)]
struct Cluster {
    uid: String,
}

#[derive(Deserialize, Debug)]
struct Site {
    uid: String,
}

async fn fetch_sites(client: &Client, base_url: &str) -> Result<Vec<Site>, InventoryError> {
    let response: HashMap<String, serde_json::Value> =
        get_api_call(client, &format!("{}/sites", base_url))
            .await
            .unwrap();
    let sites: Vec<Site> = serde_json::from_value(response.get("items").unwrap().clone())?;
    Ok(sites)
}

async fn fetch_clusters(
    client: &Client,
    base_url: &str,
    site_uid: &str,
) -> Result<Vec<Cluster>, InventoryError> {
    let response = get_api_call(client, &format!("{}/sites/{}/clusters", base_url, site_uid))
        .await
        .unwrap();
    let clusters: Vec<Cluster> = serde_json::from_value(response.get("items").unwrap().clone())?;
    Ok(clusters)
}

async fn fetch_nodes(
    client: &Client,
    base_url: &str,
    site_uid: &str,
    cluster_uid: &str,
) -> Result<Vec<Node>, InventoryError> {
    let response = get_api_call(
        client,
        &format!(
            "{}/sites/{}/clusters/{}/nodes",
            base_url, site_uid, cluster_uid
        ),
    )
    .await
    .unwrap();
    let nodes: Vec<Node> = serde_json::from_value(response.get("items").unwrap().clone())?;
    Ok(nodes)
}

#[derive(Error, Debug)]
pub enum InventoryError {
    #[error("HTTP request failed: {0}")]
    HttpRequestError(#[from] reqwest::Error),
    #[error("Failed to parse JSON: {0}")]
    JsonParseError(#[from] serde_json::Error),
    #[error("I/O error: {0}")]
    IoError(#[from] std::io::Error),
    // Ajoutez d'autres erreurs spécifiques si nécessaire
}

pub async fn get_api_call(
    client: &Client,
    endpoint: &str,
) -> Result<HashMap<String, serde_json::Value>, InventoryError> {
    dotenv::dotenv().ok();
    let username = env::var("G5K_USERNAME").expect("G5K_USERNAME must be set");
    let password = env::var("G5K_PASSWORD").expect("G5K_PASSWORD must be set");

    info!("Scraping {}", endpoint);

    let response = client
        .get(endpoint)
        .basic_auth(username, Some(password))
        .send()
        .await
        .unwrap()
        .json()
        .await;

    match response {
        Ok(json) => Ok(json),
        Err(e) => Err(InventoryError::HttpRequestError(e)),
    }
}

pub async fn generate_inventory(inventories_dir: &str) -> Result<(), InventoryError> {
    dotenv::dotenv().ok(); // Charger les variables d'environnement
    let base_url = "https://api.grid5000.fr/stable"; // URL de base de l'API
                                                     //
    fs::create_dir_all(inventories_dir)?;
    fs::read_dir(inventories_dir)?.for_each(|entry| {
        let path = entry.unwrap().path();
        let metadata = fs::metadata(&path).unwrap();
        if metadata.is_file()
            && metadata.modified().unwrap()
                < std::time::SystemTime::now() - std::time::Duration::from_secs(604800)
        {
            fs::remove_file(path).unwrap();
        }
    });

    let client = reqwest::Client::builder().build()?;
    // Récupérer les sites
    let sites = fetch_sites(&client, base_url).await.unwrap();
    for site in &sites {
        let site_dir = format!("{}/{}", inventories_dir, &site.uid);
        fs::create_dir_all(&site_dir)?;

        // Récupérer les clusters pour chaque site
        let clusters = fetch_clusters(&client, base_url, &site.uid).await.unwrap();
        for cluster in &clusters {
            let cluster_dir = format!("{}/{}", site_dir, &cluster.uid);
            fs::create_dir_all(&cluster_dir)?;
            // Récupérer les nœuds pour chaque cluster
            let mut nodes = fetch_nodes(&client, base_url, &site.uid, &cluster.uid)
                .await
                .unwrap();
            for node in &mut nodes {
                node.cluster = Some(cluster.uid.clone().to_string());
                let node_specs_file_path = format!("{}/{}.json", cluster_dir, &node.uid);

                if !Path::new(&node_specs_file_path).exists() {
                    let mut file = File::create(node_specs_file_path)?;
                    file.write_all(&node.as_bytes().unwrap())?;
                } else {
                    debug!("{} is up to date!", node_specs_file_path);
                }
                break;
            }
        }
    }

    Ok(())
}

pub fn get_inventory_sites(inventories_dir: &str) -> Result<Vec<String>, InventoryError> {
    let sites = fs::read_dir(inventories_dir)?
        .filter_map(|entry| {
            entry.ok().and_then(|e| {
                e.path()
                    .file_name()
                    .and_then(|name| name.to_str().map(String::from))
            })
        })
        .collect();
    Ok(sites)
}

pub fn get_inventory_site_clusters(
    inventories_dir: &str,
    site: &str,
) -> Result<Vec<String>, InventoryError> {
    let path = format!("{}/{}", inventories_dir, site);
    let clusters = fs::read_dir(path)?
        .filter_map(|entry| {
            entry.ok().and_then(|e| {
                e.path()
                    .file_name()
                    .and_then(|name| name.to_str().map(String::from))
            })
        })
        .collect();
    Ok(clusters)
}

pub fn get_inventory_site_cluster_nodes(
    inventories_dir: &str,
    site: &str,
    cluster: &str,
) -> Result<Vec<String>, InventoryError> {
    let path = format!("{}/{}/{}", inventories_dir, site, cluster);
    let nodes = fs::read_dir(path)?
        .filter_map(|entry| {
            entry.ok().and_then(|e| {
                e.path()
                    .file_name()
                    .and_then(|name| name.to_str().map(String::from))
            })
        })
        .collect();
    Ok(nodes)
}
#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_parse_node_with_string_version() {
        let json_data = json!({
            "uid": "node-1",
            "processor": {
                "vendor": "Intel",
                "microarchitecture": "Nehalem",
                "version": "v1.0",
                "cache_l1d": 32,
                "cache_l1i": 32,
                "cache_l2": 256,
                "cache_l3": 8192,
                "clock_speed": 2300,
                "ht_capable": true,
                "instruction_set": "x86_64",
                "microcode": "0xa",
                "model": "Intel Xeon",
                "other_description": "",
            },
            "architecture": {
                "cpu_core_numbering": "sequential",
                "nb_cores": 4,
                "nb_procs": 1,
                "nb_threads": 8,
                "platform_type": "compute"
            }
        });

        let node: Node =
            serde_json::from_value(json_data).expect("Failed to parse Node with string version");
        assert_eq!(node.processor.version.as_str(), "v1.0");
    }

    #[test]
    fn test_parse_node_with_float_version() {
        let json_data = json!({
            "uid": "node-2",
            "processor": {
                "vendor": "AMD",
                "microarchitecture": "Zen",
                "version": 2.5,
                "cache_l1d": 32,
                "cache_l1i": 32,
                "cache_l2": 512,
                "cache_l3": 16384,
                "clock_speed": 3400,
                "ht_capable": true,
                "instruction_set": "x86_64",
                "microcode": "0x15",
                "model": "Ryzen",
                "other_description": "",
            },
            "architecture": {
                "cpu_core_numbering": "sequential",
                "nb_cores": 8,
                "nb_procs": 1,
                "nb_threads": 16,
                "platform_type": "compute"
            }
        });

        let node: Node =
            serde_json::from_value(json_data).expect("Failed to parse Node with float version");
        assert_eq!(node.processor.version.as_str(), "2.5");
    }

    #[test]
    fn test_parse_empty_cluster() {
        let json_data = json!({ "uid": "cluster-1" });
        let cluster: Cluster = serde_json::from_value(json_data).expect("Failed to parse Cluster");
        assert_eq!(cluster.uid, "cluster-1");
    }

    #[test]
    fn test_parse_empty_site() {
        let json_data = json!({ "uid": "site-1" });
        let site: Site = serde_json::from_value(json_data).expect("Failed to parse Site");
        assert_eq!(site.uid, "site-1");
    }
}
