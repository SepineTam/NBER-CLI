use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum PaperTagSource {
    Topic,
    Program,
    User,
}

impl PaperTagSource {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Topic => "topic",
            Self::Program => "program",
            Self::User => "user",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct PaperTag {
    pub name: String,
    pub source: PaperTagSource,
}

#[derive(Clone, Debug, Serialize)]
pub struct DesktopConfig {
    pub feed_refresh_interval_minutes: u16,
    pub config_path: String,
    pub db_path: String,
    pub log_dir: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct Settings {
    pub feed_refresh_interval_minutes: u16,
    pub config_path: String,
    pub db_path: String,
    pub log_dir: String,
}

impl From<DesktopConfig> for Settings {
    fn from(config: DesktopConfig) -> Self {
        Self {
            feed_refresh_interval_minutes: config.feed_refresh_interval_minutes,
            config_path: config.config_path,
            db_path: config.db_path,
            log_dir: config.log_dir,
        }
    }
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct SaveSettingsInput {
    pub feed_refresh_interval_minutes: Option<u16>,
}

#[derive(Clone, Debug, Serialize)]
pub struct FeedItem {
    pub paper_id: String,
    pub title: String,
    pub authors: Vec<String>,
    #[serde(rename = "abstract")]
    pub abstract_text: String,
    pub url: String,
    pub source_url: String,
    pub guid: String,
    pub first_seen_at: String,
    pub last_seen_at: String,
    pub is_read: bool,
    pub tags: Vec<PaperTag>,
}

#[derive(Debug, Serialize)]
pub struct FeedList {
    pub items: Vec<FeedItem>,
    pub total_count: usize,
    pub limit: usize,
    pub offset: usize,
    pub last_successful_fetch_at: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct FeedRefreshResult {
    pub new_count: usize,
    pub total_count: usize,
    pub fetched_count: usize,
    pub info_fetched_count: usize,
    pub info_cached_count: usize,
    pub info_failed_count: usize,
    pub last_successful_fetch_at: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct ReadStatus {
    pub paper_id: String,
    pub is_read: bool,
}

#[derive(Clone, Debug, Serialize)]
pub struct Paper {
    pub paper_id: String,
    pub title: String,
    pub authors: Vec<String>,
    pub date: String,
    #[serde(rename = "abstract")]
    pub abstract_text: String,
    pub url: Option<String>,
    pub pdf_url: Option<String>,
    pub published_version: Option<String>,
    pub topic: Option<String>,
    pub programs: Option<String>,
    pub is_read: bool,
    pub from_cache: bool,
    pub tags: Vec<PaperTag>,
}
