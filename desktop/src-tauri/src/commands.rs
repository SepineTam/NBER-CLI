use crate::{
    config, database,
    models::{
        DesktopConfig, FeedList, FeedRefreshResult, Paper, ReadStatus, SaveSettingsInput, Settings,
    },
    network,
};
use regex::Regex;
use std::path::Path;

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
pub async fn refresh_feed() -> Result<FeedRefreshResult, String> {
    let runtime = runtime()?;
    let xml = network::download_text(network::NBER_FEED_URL).await?;
    let items = network::parse_feed(&xml)?;
    database::save_feed(db_path(&runtime), &items)
}

#[tauri::command]
pub async fn get_paper(paper_id: String) -> Result<Paper, String> {
    let runtime = runtime()?;
    let normalized = normalize_paper_id(&paper_id)?;
    let feed_url = database::feed_paper_url(db_path(&runtime), &normalized)?
        .ok_or_else(|| format!("paper not found: {normalized}"))?;

    let (mut metadata, from_cache) = if runtime.info_cache_enabled {
        if let Some(paper) = database::read_cached_paper(
            db_path(&runtime),
            &normalized,
            runtime.info_cache_ttl_days,
        )? {
            (paper, true)
        } else {
            (download_paper(&normalized, &feed_url).await?, false)
        }
    } else {
        (download_paper(&normalized, &feed_url).await?, false)
    };

    if metadata.url.is_none() {
        metadata.url = Some(feed_url);
    }
    if !from_cache && runtime.info_cache_enabled {
        database::write_paper_cache(db_path(&runtime), &metadata)?;
    }
    database::set_read_status(db_path(&runtime), &normalized, true)?;

    Ok(Paper {
        paper_id: normalized.clone(),
        title: metadata.title,
        authors: metadata.authors,
        date: metadata.date,
        abstract_text: metadata.abstract_text,
        url: metadata.url,
        pdf_url: Some(format!(
            "https://www.nber.org/system/files/working_papers/{normalized}/{normalized}.pdf"
        )),
        published_version: metadata.published_version,
        topic: metadata.topic,
        programs: metadata.programs,
        is_read: true,
        from_cache,
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
pub fn get_settings() -> Result<Settings, String> {
    Ok(runtime()?.desktop.into())
}

#[tauri::command]
pub fn save_settings(input: SaveSettingsInput) -> Result<Settings, String> {
    let runtime = config::save_settings(input)?;
    database::ensure_schema(db_path(&runtime))?;
    config::initialize(&runtime)?;
    Ok(runtime.desktop.into())
}

async fn download_paper(
    expected_paper_id: &str,
    feed_url: &str,
) -> Result<crate::models::PaperMetadata, String> {
    let page = network::download_text(feed_url).await?;
    let mut paper = network::parse_paper(&page)?;
    if paper.paper_id != expected_paper_id {
        return Err(format!(
            "requested paper ID {expected_paper_id} does not match response paper ID {}",
            paper.paper_id
        ));
    }
    paper.url = Some(feed_url.to_string());
    Ok(paper)
}

fn runtime() -> Result<config::RuntimeConfig, String> {
    let runtime = config::load()?;
    database::ensure_schema(db_path(&runtime))?;
    config::initialize(&runtime)?;
    Ok(runtime)
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
