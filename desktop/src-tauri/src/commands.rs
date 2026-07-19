use crate::{
    config, database,
    models::{
        DesktopConfig, FeedList, FeedRefreshResult, Paper, PaperTag, PaperTagSource, ReadStatus,
        SaveSettingsInput, Settings,
    },
    worker,
};
use regex::Regex;
use std::path::Path;
use tauri::AppHandle;

#[tauri::command]
pub fn get_config() -> Result<DesktopConfig, String> {
    Ok(runtime()?.desktop)
}

#[tauri::command]
pub fn get_feed(limit: Option<usize>, offset: Option<usize>) -> Result<FeedList, String> {
    let limit = limit.unwrap_or(100);
    let offset = offset.unwrap_or(0);
    if !(1..=200).contains(&limit) {
        return Err("limit must be between 1 and 200".to_string());
    }
    let runtime = runtime()?;
    database::list_feed(db_path(&runtime), limit, offset)
}

#[tauri::command]
pub async fn refresh_feed(app: AppHandle) -> Result<FeedRefreshResult, String> {
    let runtime = runtime()?;
    let path = db_path(&runtime).to_path_buf();
    let output = tokio::task::spawn_blocking(move || worker::fetch_feed(&app, &path))
        .await
        .map_err(|error| format!("Desktop worker task failed: {error}"))??;
    database::sync_raw_tags(db_path(&runtime))?;
    database::feed_refresh_result(
        db_path(&runtime),
        output.fetched_count,
        output.new_count,
        output.info_fetched_count,
        output.info_cached_count,
        output.info_failed_count,
    )
}

#[tauri::command]
pub fn get_paper(paper_id: String) -> Result<Paper, String> {
    let runtime = runtime()?;
    let normalized = normalize_paper_id(&paper_id)?;
    let paper = database::get_paper(db_path(&runtime), &normalized)?;
    database::set_read_status(db_path(&runtime), &normalized, true)?;
    Ok(Paper {
        is_read: true,
        ..paper
    })
}

#[tauri::command]
pub fn set_paper_read_status(paper_id: String, is_read: bool) -> Result<ReadStatus, String> {
    let runtime = runtime()?;
    let normalized = normalize_paper_id(&paper_id)?;
    database::set_read_status(db_path(&runtime), &normalized, is_read)?;
    Ok(ReadStatus {
        paper_id: normalized,
        is_read,
    })
}

#[tauri::command]
pub fn add_paper_tag(paper_id: String, tag: String) -> Result<Vec<PaperTag>, String> {
    let runtime = runtime()?;
    let normalized = normalize_paper_id(&paper_id)?;
    database::add_user_tag(db_path(&runtime), &normalized, &tag)
}

#[tauri::command]
pub fn rename_paper_tag(
    paper_id: String,
    old_tag: String,
    new_tag: String,
    source: PaperTagSource,
) -> Result<Vec<PaperTag>, String> {
    let runtime = runtime()?;
    let normalized = normalize_paper_id(&paper_id)?;
    database::rename_tag(db_path(&runtime), &normalized, &old_tag, &new_tag, source)
}

#[tauri::command]
pub fn remove_paper_tag(
    paper_id: String,
    tag: String,
    source: PaperTagSource,
) -> Result<Vec<PaperTag>, String> {
    let runtime = runtime()?;
    let normalized = normalize_paper_id(&paper_id)?;
    database::remove_tag(db_path(&runtime), &normalized, &tag, source)
}

#[tauri::command]
pub fn get_settings() -> Result<Settings, String> {
    Ok(runtime()?.desktop.into())
}

#[tauri::command]
pub fn save_settings(input: SaveSettingsInput) -> Result<Settings, String> {
    let runtime = config::save_settings(input)?;
    if db_path(&runtime).exists() {
        database::validate_schema(db_path(&runtime))?;
    }
    config::initialize(&runtime)?;
    Ok(runtime.desktop.into())
}

pub fn initialize_runtime(app: Option<&AppHandle>) -> Result<(), String> {
    let runtime = config::load()?;
    if db_path(&runtime).exists() && database::validate_schema(db_path(&runtime)).is_err() {
        worker::initialize(app, db_path(&runtime))?;
    }
    if db_path(&runtime).exists() {
        database::validate_schema(db_path(&runtime))?;
        database::ensure_desktop_storage(db_path(&runtime))?;
        database::sync_raw_tags(db_path(&runtime))?;
    }
    config::initialize(&runtime)
}

fn runtime() -> Result<config::RuntimeConfig, String> {
    config::load()
}

fn db_path(runtime: &config::RuntimeConfig) -> &Path {
    Path::new(&runtime.desktop.db_path)
}

fn normalize_paper_id(value: &str) -> Result<String, String> {
    let cleaned = value.trim().to_lowercase();
    let pattern = Regex::new(r"^w?(\d+)$").expect("valid paper ID regex");
    let number = pattern
        .captures(&cleaned)
        .and_then(|captures| captures.get(1))
        .and_then(|matched| matched.as_str().parse::<u64>().ok())
        .filter(|number| *number > 0)
        .ok_or_else(|| "paper_id must look like w12345".to_string())?;
    Ok(format!("w{number}"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normalizes_paper_ids() {
        assert_eq!(normalize_paper_id(" W00123 ").unwrap(), "w123");
        assert!(normalize_paper_id("paper").is_err());
        assert!(normalize_paper_id("w0").is_err());
    }
}
