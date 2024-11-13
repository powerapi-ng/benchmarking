use bytes::BytesMut;
use log::{error, info};
use openssh::{KnownHosts, Session, Stdio};
use openssh_sftp_client::Sftp;
use std::path::Path;
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
}

type SshResult = Result<(), SshError>;

// Use OpenSSH client to create an ssh session
pub async fn ssh_connect(host: &str) -> Result<Session, SshError> {
    let session = Session::connect_mux(host, KnownHosts::Strict).await?;
    info!("SSH Connection established with {}", host);
    Ok(session)
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
    info!("SFTP Connection established");

    {
        let mut fs = sftp.fs();
        fs.write(path_to_upload_file, bytes_content).await?;
        info!(
            "Local file '{}' written to remote destination '{}'",
            file_to_upload_path, path_to_upload_file
        );
    }
    Ok(())
}

pub async fn sftp_download(
    session: &Session,
    file_to_download_path: &str,
    path_to_download_file: &str,
) -> SshResult {
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
    info!("SFTP Connection established");

    let mut remote_file = sftp.open(Path::new(file_to_download_path)).await?;
    let mut local_file = File::create(path_to_download_file).await?;

    let mut buffer = BytesMut::with_capacity(1_024);

    // Read remote file and write to local file in chunks
    loop {
        buffer.resize(1024, 0); // Resize buffer for each read
        let bytes_read = remote_file.read(1_024, buffer.clone()).await?;

        if bytes_read.clone().unwrap().is_empty() {
            break; // EOF
        }

        local_file
            .write_all(&buffer[..bytes_read.unwrap().len()])
            .await?;
    }

    println!("File downloaded successfully to {}", path_to_download_file);

    Ok(())
}
