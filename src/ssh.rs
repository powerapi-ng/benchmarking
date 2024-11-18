use bytes::BytesMut;
use log::{debug, error, info};
use openssh::{KnownHosts, Session, Stdio};
use openssh_sftp_client::Sftp;
use regex::Regex;
use std::path::Path;
use std::str::{self};
use thiserror::Error;
use tokio::fs::File;
use tokio::io::AsyncWriteExt;

#[derive(Error, Debug)]
pub enum SshError {
    #[error("Could not upload script: {0}")]
    Ssh(#[from] openssh::Error),
    #[error("Could not upload script: {0}")]
    Sftp(#[from] openssh_sftp_client::Error),
    #[error("Could not read script: {0}")]
    Io(#[from] std::io::Error),
    #[error("Could not read host output: {0}")]
    Utf8(#[from] str::Utf8Error),
    #[error("Could not parse int: {0}")]
    ParseInt(#[from] std::num::ParseIntError),
}

type SshResult = Result<(), SshError>;

// Use OpenSSH client to create an ssh session
pub async fn ssh_connect(host: &str) -> Result<Session, SshError> {
    let session = Session::connect_mux(host, KnownHosts::Strict).await?;
    debug!("SSH Connection established with {}", host);
    Ok(session)
}

pub async fn create_remote_directory(session: &Session, file: &str) -> SshResult {
    let script_directory = std::path::Path::new(file)
        .parent()
        .unwrap()
        .to_string_lossy()
        .into_owned();

    session
        .command("mkdir")
        .arg("-p")
        .arg(&script_directory)
        .output()
        .await?;

    Ok(())
}

pub async fn make_script_executable(session: &Session, script_file: &str) -> SshResult {
    session
        .command("chmod")
        .arg("u+x")
        .arg(script_file)
        .output()
        .await?;

    Ok(())
}

pub async fn run_oarsub(session: &Session, script_file: &str) -> Result<Option<u32>, SshError> {
    let oarsub_output = session
        .command("oarsub")
        .arg("-S")
        .arg(script_file)
        .output()
        .await?;

    if oarsub_output.status.success() {
        let output_str = str::from_utf8(&oarsub_output.stdout)?;
        let re = Regex::new(r"OAR_JOB_ID=(\d+)").unwrap();
        if let Some(captures) = re.captures(output_str) {
            let job_id = captures.get(1).unwrap().as_str().parse::<u32>()?;
            info!("Job successfully submitted with OAR_JOB_ID: {}", job_id);
            Ok(Some(job_id))
        } else {
            error!("Failed to parse OAR_JOB_ID");
            Ok(None)
        }
    } else {
        error!("Job submission failed: {:?}", oarsub_output.stderr);
        Ok(None)
    }
}

// Use OpenSSH Session to upload files though SFTP
pub async fn sftp_upload(
    session: &Session,
    file_to_upload_path: &str,
    path_to_upload_file: &str,
) -> SshResult {
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
    debug!("SFTP Connection established");

    {
        let mut fs = sftp.fs();
        fs.write(path_to_upload_file, bytes_content).await?;
        debug!(
            "Local file '{}' written to remote destination '{}'",
            file_to_upload_path, path_to_upload_file
        );
    }
    Ok(())
}
