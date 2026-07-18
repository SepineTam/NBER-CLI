use crate::models::{FeedItem, FeedList, FeedRefreshResult};
use chrono::{SecondsFormat, Utc};
use rusqlite::{params, Connection, OptionalExtension};
use std::{path::Path, time::Duration};

pub const SCHEMA_VERSION: u8 = 3;

pub fn validate_schema(db_path: &Path) -> Result<(), String> {
    if !db_path.exists() {
        return Err(format!(
            "desktop worker did not initialize {}",
            db_path.display()
        ));
    }
    let connection = open(db_path)?;
    let version: u8 = connection
        .pragma_query_value(None, "user_version", |row| row.get(0))
        .map_err(display_error)?;
    if version != SCHEMA_VERSION {
        return Err(format!(
            "database schema version {version} does not match supported version {SCHEMA_VERSION}"
        ));
    }
    Ok(())
}

pub fn list_feed(db_path: &Path, limit: usize, offset: usize) -> Result<FeedList, String> {
    let connection = open(db_path)?;
    let mut statement = connection
        .prepare(
            r#"
            SELECT
                feed_items.paper_id, feed_items.title, feed_items.authors_json,
                feed_items.abstract, feed_items.url, feed_items.source_url,
                feed_items.guid, feed_items.first_seen_at, feed_items.last_seen_at,
                COALESCE(read_status.is_read, 0)
            FROM feed_items
            LEFT JOIN read_status ON read_status.paper_id = feed_items.paper_id
            ORDER BY feed_items.last_seen_at DESC
            LIMIT ?1 OFFSET ?2
            "#,
        )
        .map_err(display_error)?;
    let rows = statement
        .query_map(params![limit as i64, offset as i64], |row| {
            let authors_json: String = row.get(2)?;
            Ok(FeedItem {
                paper_id: row.get(0)?,
                title: row.get(1)?,
                authors: serde_json::from_str(&authors_json).unwrap_or_default(),
                abstract_text: row.get(3)?,
                url: row.get(4)?,
                source_url: row.get(5)?,
                guid: row.get(6)?,
                first_seen_at: row.get(7)?,
                last_seen_at: row.get(8)?,
                is_read: row.get(9)?,
            })
        })
        .map_err(display_error)?;
    let items = rows.collect::<Result<Vec<_>, _>>().map_err(display_error)?;
    let total_count = feed_total_count(&connection)?;
    Ok(FeedList {
        items,
        total_count,
        limit,
        offset,
        last_successful_fetch_at: last_successful_fetch_at(&connection)?,
    })
}

pub fn feed_refresh_result(
    db_path: &Path,
    fetched_count: usize,
    new_count: usize,
) -> Result<FeedRefreshResult, String> {
    let connection = open(db_path)?;
    Ok(FeedRefreshResult {
        new_count,
        total_count: feed_total_count(&connection)?,
        fetched_count,
        last_successful_fetch_at: last_successful_fetch_at(&connection)?,
    })
}

pub fn feed_paper_exists(db_path: &Path, paper_id: &str) -> Result<bool, String> {
    open(db_path)?
        .query_row(
            "SELECT 1 FROM feed_items WHERE paper_id = ?1",
            [paper_id],
            |_| Ok(()),
        )
        .optional()
        .map(|row| row.is_some())
        .map_err(display_error)
}

pub fn set_read_status(db_path: &Path, paper_id: &str, is_read: bool) -> Result<(), String> {
    open(db_path)?
        .execute(
            r#"
            INSERT INTO read_status (paper_id, is_read, updated_at)
            VALUES (?1, ?2, ?3)
            ON CONFLICT(paper_id) DO UPDATE SET
                is_read = excluded.is_read,
                updated_at = excluded.updated_at
            "#,
            params![paper_id, is_read, utc_now()],
        )
        .map(|_| ())
        .map_err(display_error)
}

fn feed_total_count(connection: &Connection) -> Result<usize, String> {
    let count: i64 = connection
        .query_row("SELECT COUNT(*) FROM feed_items", [], |row| row.get(0))
        .map_err(display_error)?;
    Ok(count as usize)
}

fn last_successful_fetch_at(connection: &Connection) -> Result<Option<String>, String> {
    connection
        .query_row(
            "SELECT fetched_at FROM feed_fetches ORDER BY fetched_at DESC LIMIT 1",
            [],
            |row| row.get(0),
        )
        .optional()
        .map_err(display_error)
}

fn open(db_path: &Path) -> Result<Connection, String> {
    let connection = Connection::open(db_path).map_err(display_error)?;
    connection
        .busy_timeout(Duration::from_secs(5))
        .map_err(display_error)?;
    Ok(connection)
}

fn utc_now() -> String {
    Utc::now().to_rfc3339_opts(SecondsFormat::Secs, false)
}

fn display_error(error: impl std::fmt::Display) -> String {
    error.to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_uninitialized_database() {
        let path =
            std::env::temp_dir().join(format!("nber-cli-worker-schema-{}.db", std::process::id()));
        let _ = std::fs::remove_file(&path);
        Connection::open(&path).unwrap();
        assert!(validate_schema(&path).is_err());
        let _ = std::fs::remove_file(path);
    }
}
