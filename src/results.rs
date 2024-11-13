use serde;
use std::fs::File;
use std::path::Path;
use tar::Archive;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ResultError {}

#[derive()]
pub struct HwpcReport {}

#[derive()]
pub struct PerfReport {}
