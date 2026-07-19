use serde::de::DeserializeOwned;
use serde::Deserialize;
use std::{path::Path, process::Command};
use tauri::{AppHandle, Manager};

const WORKER_NAME: &str = "nber-worker";

#[derive(Debug, Deserialize)]
pub struct FeedFetchOutput {
    pub fetched_count: usize,
    pub new_count: usize,
    pub info_fetched_count: usize,
    pub info_cached_count: usize,
    pub info_failed_count: usize,
}

pub fn initialize(app: Option<&AppHandle>, db_path: &Path) -> Result<(), String> {
    let _: serde_json::Value = run(app, db_path, &["init"])?;
    Ok(())
}

pub fn fetch_feed(app: &AppHandle, db_path: &Path) -> Result<FeedFetchOutput, String> {
    run(Some(app), db_path, &["feed-fetch"])
}

fn run<T: DeserializeOwned>(
    app: Option<&AppHandle>,
    db_path: &Path,
    worker_args: &[&str],
) -> Result<T, String> {
    let mut command = worker_command(app)?;
    command.arg("--db-path").arg(db_path).args(worker_args);
    let output = command
        .output()
        .map_err(|error| format!("failed to start bundled Desktop worker: {error}"))?;
    if !output.status.success() {
        let error = String::from_utf8_lossy(&output.stderr).trim().to_string();
        return Err(if error.is_empty() {
            format!("Desktop worker exited with {}", output.status)
        } else {
            error
        });
    }
    serde_json::from_slice(&output.stdout)
        .map_err(|error| format!("invalid Desktop worker response: {error}"))
}

fn worker_command(app: Option<&AppHandle>) -> Result<Command, String> {
    if let Some(path) = std::env::var_os("NBER_WORKER_PATH") {
        return Ok(Command::new(path));
    }
    for path in worker_candidates(app) {
        if path.exists() {
            return Ok(Command::new(path));
        }
    }
    if cfg!(debug_assertions) {
        let mut command = Command::new("uv");
        command.args(["run", "python", "-m", "nber_cli.desktop_worker"]);
        return Ok(command);
    }
    Err("bundled Desktop worker was not found".to_string())
}

fn worker_candidates(app: Option<&AppHandle>) -> Vec<std::path::PathBuf> {
    let file_name = if cfg!(target_os = "windows") {
        format!("{WORKER_NAME}.exe")
    } else {
        WORKER_NAME.to_string()
    };
    let mut candidates = Vec::new();
    if let Some(app) = app {
        if let Ok(resource_dir) = app.path().resource_dir() {
            candidates.push(resource_dir.join(&file_name));
            candidates.push(resource_dir.join("binaries").join(&file_name));
        }
    }
    if let Ok(executable) = std::env::current_exe() {
        if let Some(parent) = executable.parent() {
            candidates.push(parent.join(&file_name));
            candidates.push(parent.join("../Resources").join(&file_name));
        }
    }
    candidates
}
