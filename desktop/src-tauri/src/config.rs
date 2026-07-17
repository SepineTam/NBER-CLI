use crate::models::{DesktopConfig, SaveSettingsInput};
use serde_json::{json, Map, Value};
use std::{
    fs,
    path::{Component, Path, PathBuf},
};

pub const DEFAULT_REFRESH_INTERVAL_MINUTES: u16 = 60;
pub const DEFAULT_INFO_CACHE_TTL_DAYS: u16 = 30;

#[derive(Clone, Debug)]
pub struct RuntimeConfig {
    pub desktop: DesktopConfig,
    pub info_cache_enabled: bool,
    pub info_cache_ttl_days: u16,
}

pub fn load() -> Result<RuntimeConfig, String> {
    let home = home_dir()?;
    let app_dir = home.join(".nber-cli");
    let config_path = app_dir.join("config.json");
    let log_dir = app_dir.join("logs");
    fs::create_dir_all(&app_dir).map_err(display_error)?;
    fs::create_dir_all(&log_dir).map_err(display_error)?;

    let config = read_json(&config_path)?;
    let refresh_interval = positive_u16(
        config.pointer("/desktop/feed_refresh_interval_minutes"),
        DEFAULT_REFRESH_INTERVAL_MINUTES,
    );
    let info_cache_enabled = config
        .pointer("/info/cache_enabled")
        .and_then(Value::as_bool)
        .unwrap_or(true);
    let info_cache_ttl_days = positive_u16(
        config.pointer("/info/cache_ttl_days"),
        DEFAULT_INFO_CACHE_TTL_DAYS,
    );
    let db_path = configured_db_path(&config, &home, &app_dir)?;

    Ok(RuntimeConfig {
        desktop: DesktopConfig {
            feed_refresh_interval_minutes: refresh_interval,
            config_path: path_text(&config_path),
            db_path: path_text(&db_path),
            log_dir: path_text(&log_dir),
        },
        info_cache_enabled,
        info_cache_ttl_days,
    })
}

pub fn initialize(runtime: &RuntimeConfig) -> Result<(), String> {
    let config_path = PathBuf::from(&runtime.desktop.config_path);
    let mut config = read_json(&config_path)?;
    let root = root_object_mut(&mut config)?;

    let desktop = child_object_mut(root, "desktop");
    desktop.insert(
        "feed_refresh_interval_minutes".to_string(),
        json!(runtime.desktop.feed_refresh_interval_minutes),
    );

    let info = child_object_mut(root, "info");
    info.entry("cache_enabled".to_string())
        .or_insert(json!(true));
    info.entry("cache_ttl_days".to_string())
        .or_insert(json!(DEFAULT_INFO_CACHE_TTL_DAYS));

    let feed = child_object_mut(root, "feed");
    feed.insert("db-path".to_string(), json!(runtime.desktop.db_path));
    root.insert(
        "schema_version".to_string(),
        json!(crate::database::SCHEMA_VERSION),
    );
    write_json(&config_path, &config)
}

pub fn save_settings(input: SaveSettingsInput) -> Result<RuntimeConfig, String> {
    let runtime = load()?;
    let interval = input
        .feed_refresh_interval_minutes
        .unwrap_or(runtime.desktop.feed_refresh_interval_minutes);
    if interval == 0 {
        return Err("feed_refresh_interval_minutes must be a positive integer".to_string());
    }

    let config_path = PathBuf::from(&runtime.desktop.config_path);
    let mut config = read_json(&config_path)?;
    child_object_mut(root_object_mut(&mut config)?, "desktop")
        .insert("feed_refresh_interval_minutes".to_string(), json!(interval));
    write_json(&config_path, &config)?;
    load()
}

fn configured_db_path(config: &Value, home: &Path, app_dir: &Path) -> Result<PathBuf, String> {
    let configured = config
        .pointer("/feed/db-path")
        .and_then(Value::as_str)
        .filter(|value| !value.trim().is_empty());
    let path = if let Some(value) = configured {
        parse_database_path(value, home)?
    } else {
        let default = app_dir.join("nber.db");
        let legacy = app_dir.join("feed.db");
        if default.exists() || !legacy.exists() {
            default
        } else {
            legacy
        }
    };
    let normalized = normalize_path(&path);
    validate_database_path(&normalized, home)?;
    Ok(normalized)
}

fn parse_database_path(value: &str, home: &Path) -> Result<PathBuf, String> {
    let raw = if value.starts_with("sqlite:") {
        if value == "sqlite:///:memory:" {
            return Err("in-memory SQLite databases are not supported".to_string());
        }
        if !value.starts_with("sqlite:///") || value.contains('?') || value.contains('#') {
            return Err("database URL must use a local sqlite:/// path".to_string());
        }
        let stripped = value.trim_start_matches("sqlite:///");
        if stripped.is_empty() {
            return Err("database URL must include a file path".to_string());
        }
        if value.starts_with("sqlite:////") {
            format!("/{stripped}")
        } else {
            stripped.to_string()
        }
    } else {
        value.to_string()
    };

    let expanded = if raw == "~" {
        home.to_path_buf()
    } else if let Some(suffix) = raw.strip_prefix("~/") {
        home.join(suffix)
    } else {
        PathBuf::from(raw)
    };
    if expanded.is_absolute() {
        Ok(expanded)
    } else {
        std::env::current_dir()
            .map(|current| current.join(expanded))
            .map_err(display_error)
    }
}

#[cfg(not(target_os = "windows"))]
fn validate_database_path(path: &Path, home: &Path) -> Result<(), String> {
    if !path.starts_with(home) {
        return Err(format!(
            "database path must be within the home directory: {}",
            path.display()
        ));
    }
    Ok(())
}

#[cfg(target_os = "windows")]
fn validate_database_path(_path: &Path, _home: &Path) -> Result<(), String> {
    Ok(())
}

fn read_json(path: &Path) -> Result<Value, String> {
    if !path.exists() {
        return Ok(json!({}));
    }
    let text = fs::read_to_string(path).map_err(display_error)?;
    let value: Value = serde_json::from_str(&text)
        .map_err(|error| format!("invalid configuration file {}: {error}", path.display()))?;
    if !value.is_object() {
        return Err("config root must be an object".to_string());
    }
    Ok(value)
}

fn write_json(path: &Path, value: &Value) -> Result<(), String> {
    let text = serde_json::to_string_pretty(value).map_err(display_error)? + "\n";
    let temporary = path.with_extension("json.tmp");
    fs::write(&temporary, text).map_err(display_error)?;
    #[cfg(target_os = "windows")]
    if path.exists() {
        fs::remove_file(path).map_err(display_error)?;
    }
    fs::rename(&temporary, path).map_err(display_error)
}

fn normalize_path(path: &Path) -> PathBuf {
    let mut normalized = PathBuf::new();
    for component in path.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                normalized.pop();
            }
            Component::Prefix(_) | Component::RootDir | Component::Normal(_) => {
                normalized.push(component.as_os_str());
            }
        }
    }
    normalized
}

fn root_object_mut(value: &mut Value) -> Result<&mut Map<String, Value>, String> {
    value
        .as_object_mut()
        .ok_or_else(|| "config root must be an object".to_string())
}

fn child_object_mut<'a>(root: &'a mut Map<String, Value>, key: &str) -> &'a mut Map<String, Value> {
    let child = root.entry(key.to_string()).or_insert_with(|| json!({}));
    if !child.is_object() {
        *child = json!({});
    }
    child.as_object_mut().expect("object inserted above")
}

fn positive_u16(value: Option<&Value>, default: u16) -> u16 {
    value
        .and_then(Value::as_u64)
        .filter(|value| *value > 0 && *value <= u16::MAX as u64)
        .map(|value| value as u16)
        .unwrap_or(default)
}

fn home_dir() -> Result<PathBuf, String> {
    std::env::var_os("HOME")
        .or_else(|| std::env::var_os("USERPROFILE"))
        .map(PathBuf::from)
        .ok_or_else(|| "could not determine user home directory".to_string())
}

fn path_text(path: &Path) -> String {
    path.to_string_lossy().into_owned()
}

fn display_error(error: impl std::fmt::Display) -> String {
    error.to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_sqlite_absolute_path() {
        let home = Path::new("/Users/test");
        assert_eq!(
            parse_database_path("sqlite:////Users/test/data/nber.db", home).unwrap(),
            PathBuf::from("/Users/test/data/nber.db")
        );
    }

    #[test]
    fn expands_home_database_path() {
        let home = Path::new("/Users/test");
        assert_eq!(
            parse_database_path("~/.nber-cli/custom.db", home).unwrap(),
            PathBuf::from("/Users/test/.nber-cli/custom.db")
        );
    }

    #[test]
    fn normalizes_parent_components_before_home_validation() {
        assert_eq!(
            normalize_path(Path::new("/Users/test/data/../nber.db")),
            PathBuf::from("/Users/test/nber.db")
        );
    }
}
