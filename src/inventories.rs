use derive_more::Display;
use log::{debug, error};
use reqwest::Client;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use std::collections::HashMap;
use std::env;
use std::fs::File;
use std::fs::{self};
use std::io::Write;
use std::path::Path;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum InventoryError {
    #[error("HTTP request failed: {0}")]
    HttpRequest(#[from] reqwest::Error),
    #[error("Failed to parse JSON: {0}")]
    JsonParse(#[from] serde_json::Error),
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("The requested resource is blacklisted.")]
    Blacklisted,
}

#[derive(Deserialize, Serialize, Debug, Clone)]
pub struct Node {
    pub uid: String,
    pub cluster: Option<String>,
    pub exotic: bool,
    pub processor: Processor,
    pub architecture: Architecture,
    pub operating_system: Option<OperatingSystem>,
    pub supported_job_types: SupportedJobTypes,
}

#[derive(Deserialize, Serialize, Debug, Clone)]
pub struct SupportedJobTypes {
    pub queues: Vec<String>,
}

impl Node {
    pub fn as_bytes(&self) -> Result<Vec<u8>, InventoryError> {
        let json_data = serde_json::to_vec(self)?;
        Ok(json_data)
    }
    pub fn is_to_be_deployed(&self) -> bool {
        super::SUPPORTED_PROCESSOR_VENDOR.contains(&self.processor.vendor.as_str())
            && self
                .supported_job_types
                .queues
                .contains(&"default".to_string())
    }
}

#[derive(Deserialize, Serialize, Debug, Clone)]
pub struct Architecture {
    cpu_core_numbering: String,
    pub nb_cores: u32,
    nb_procs: i32,
    nb_threads: i32,
    platform_type: String,
}

#[derive(Debug, Clone, Display, PartialEq)]
pub enum StrOrFloat {
    Str(String),
    Float(f64),
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

#[derive(Deserialize, Serialize, Debug, Clone)]
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
    microcode: Option<String>,
    model: String,
    other_description: String,
    pub vendor: String,
    pub version: StrOrFloat, // Is sometimes another type, like f64, and then panic
}

#[derive(Deserialize, Serialize, Debug, Clone)]
pub struct OperatingSystem {
    cstate_driver: String,
    cstate_governor: String,
    pstate_driver: String,
    pstate_governor: String,
    turboboost_enabled: bool,
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

pub async fn fetch_nodes(
    client: &Client,
    base_url: &str,
    site_uid: &str,
    cluster_uid: &str,
) -> Result<Vec<Node>, InventoryError> {
    if let Ok(response) = get_api_call(
        client,
        &format!(
            "{}/sites/{}/clusters/{}/nodes",
            base_url, site_uid, cluster_uid
        ),
    )
    .await
    {
        let nodes: Vec<Node> = serde_json::from_value(response.get("items").unwrap().clone())?;
        Ok(nodes)
    } else {
        Err(InventoryError::Blacklisted)
    }
}

pub async fn get_api_call(
    client: &Client,
    endpoint: &str,
) -> Result<HashMap<String, serde_json::Value>, InventoryError> {
    dotenv::dotenv().ok();
    let username = env::var("G5K_USERNAME").expect("G5K_USERNAME must be set");
    let password = env::var("G5K_PASSWORD").expect("G5K_PASSWORD must be set");

    debug!("GET request to {}", endpoint);

    let response = client
        .get(endpoint)
        .basic_auth(username, Some(password))
        .send()
        .await;
    let response_json = match response {
        Ok(response_body) => response_body.json().await,
        Err(e) => Err(e),
    };

    match response_json {
        Ok(json) => Ok(json),
        Err(e) => Err(InventoryError::HttpRequest(e)),
    }
}

pub async fn post_api_call(
    client: &Client,
    endpoint: &str,
    data: &serde_json::Value,
) -> Result<HashMap<String, serde_json::Value>, InventoryError> {
    dotenv::dotenv().ok();
    let username = env::var("G5K_USERNAME").expect("G5K_USERNAME must be set");
    let password = env::var("G5K_PASSWORD").expect("G5K_PASSWORD must be set");

    debug!("POST request to {}", endpoint);
    debug!("with data {:?}", data);

    let response = client
        .post(endpoint)
        .json(&data)
        .basic_auth(username, Some(password))
        .send()
        .await;
    let response_json = match response {
        Ok(response_body) => response_body.json().await,
        Err(e) => Err(e),
    };

    match response_json {
        Ok(json) => Ok(json),
        Err(e) => Err(InventoryError::HttpRequest(e)),
    }
}

pub async fn generate_inventory(inventories_dir: &str) -> Result<(), InventoryError> {
    dotenv::dotenv().ok(); // Charger les variables d'environnement
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
    let sites = fetch_sites(&client, super::BASE_URL).await.unwrap();
    for site in &sites {
        let site_dir = format!("{}/{}", inventories_dir, &site.uid);
        fs::create_dir_all(&site_dir)?;

        // Récupérer les clusters pour chaque site
        let clusters = fetch_clusters(&client, super::BASE_URL, &site.uid)
            .await
            .unwrap();
        for cluster in &clusters {
            let cluster_dir = format!("{}/{}", site_dir, &cluster.uid);
            fs::create_dir_all(&cluster_dir)?;
            // Récupérer les nœuds pour chaque cluster
            let mut nodes = fetch_nodes(&client, super::BASE_URL, &site.uid, &cluster.uid)
                .await
                .unwrap();
            for node in nodes.iter_mut() {
                node.cluster = Some(cluster.uid.clone().to_string());
                if node.is_to_be_deployed() {
                    let node_specs_file_path = format!("{}/{}.json", cluster_dir, &node.uid);

                    if !Path::new(&node_specs_file_path).exists() {
                        let mut file = File::create(node_specs_file_path)?;
                        file.write_all(&node.as_bytes().unwrap())?;
                    } else {
                        debug!("{} is up to date!", node_specs_file_path);
                    }
                }
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
