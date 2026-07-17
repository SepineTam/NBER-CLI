use crate::models::{FeedItem, FeedList, FeedRefreshResult, FeedSourceItem, PaperMetadata};
use chrono::{DateTime, Duration as ChronoDuration, SecondsFormat, Utc};
use rusqlite::{params, Connection, OptionalExtension};
use std::{path::Path, time::Duration};

pub const SCHEMA_VERSION: u8 = 3;
const NBER_FEED_URL: &str = "https://www.nber.org/rss/new.xml";

pub fn ensure_schema(db_path: &Path) -> Result<(), String> {
    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent).map_err(display_error)?;
    }
    let connection = open(db_path)?;
    let current_version: u8 = connection
        .pragma_query_value(None, "user_version", |row| row.get(0))
        .map_err(display_error)?;
    if current_version > SCHEMA_VERSION {
        return Err(format!(
            "database schema version {current_version} is newer than supported version {SCHEMA_VERSION}"
        ));
    }
    connection
        .execute_batch(&format!(
            r#"
            BEGIN IMMEDIATE;
            CREATE TABLE IF NOT EXISTS feed_items (
                paper_id VARCHAR NOT NULL PRIMARY KEY,
                title VARCHAR NOT NULL,
                authors_json VARCHAR NOT NULL,
                abstract VARCHAR NOT NULL,
                url VARCHAR NOT NULL,
                source_url VARCHAR NOT NULL,
                guid VARCHAR NOT NULL,
                first_seen_at VARCHAR NOT NULL,
                last_seen_at VARCHAR NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_feed_items_last_seen_at
                ON feed_items (last_seen_at);
            CREATE TABLE IF NOT EXISTS feed_fetches (
                id INTEGER NOT NULL PRIMARY KEY,
                source_url VARCHAR NOT NULL,
                fetched_at VARCHAR NOT NULL,
                total_count INTEGER NOT NULL,
                new_count INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS read_status (
                paper_id VARCHAR NOT NULL PRIMARY KEY,
                is_read BOOLEAN NOT NULL,
                updated_at VARCHAR NOT NULL
            );
            CREATE TABLE IF NOT EXISTS query_log (
                id INTEGER NOT NULL PRIMARY KEY,
                created_at VARCHAR NOT NULL,
                keyword VARCHAR NOT NULL,
                conditions VARCHAR NOT NULL,
                result_count INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_query_log_created_at
                ON query_log (created_at);
            CREATE TABLE IF NOT EXISTS download_log (
                id INTEGER NOT NULL PRIMARY KEY,
                created_at VARCHAR NOT NULL,
                paper_id VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                saved_path VARCHAR,
                error VARCHAR
            );
            CREATE INDEX IF NOT EXISTS idx_download_log_created_at
                ON download_log (created_at);
            CREATE INDEX IF NOT EXISTS idx_download_log_paper_id
                ON download_log (paper_id);
            CREATE TABLE IF NOT EXISTS info_log (
                id INTEGER NOT NULL PRIMARY KEY,
                created_at VARCHAR NOT NULL,
                paper_id VARCHAR NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_info_log_paper_id
                ON info_log (paper_id);
            CREATE INDEX IF NOT EXISTS idx_info_log_created_at
                ON info_log (created_at);
            CREATE TABLE IF NOT EXISTS info_cache (
                paper_id VARCHAR NOT NULL PRIMARY KEY,
                title VARCHAR NOT NULL,
                authors_json VARCHAR NOT NULL,
                date VARCHAR NOT NULL,
                abstract VARCHAR NOT NULL,
                url VARCHAR,
                published_version VARCHAR,
                topic VARCHAR,
                programs VARCHAR,
                first_cached_at VARCHAR NOT NULL,
                last_fetched_at VARCHAR NOT NULL,
                fetch_count INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_info_cache_last_fetched_at
                ON info_cache (last_fetched_at);
            PRAGMA user_version = {SCHEMA_VERSION};
            COMMIT;
            "#
        ))
        .map_err(display_error)
}

pub fn list_feed(db_path: &Path, limit: usize, offset: usize) -> Result<FeedList, String> {
    let connection = open(db_path)?;
    let mut statement = connection
        .prepare(
            r#"
            SELECT
                feed_items.paper_id,
                feed_items.title,
                feed_items.authors_json,
                feed_items.abstract,
                feed_items.url,
                feed_items.source_url,
                feed_items.guid,
                feed_items.first_seen_at,
                feed_items.last_seen_at,
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
                authors: decode_authors(&authors_json),
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
    let total_count: i64 = connection
        .query_row("SELECT COUNT(*) FROM feed_items", [], |row| row.get(0))
        .map_err(display_error)?;

    Ok(FeedList {
        items,
        total_count: total_count as usize,
        limit,
        offset,
        last_successful_fetch_at: last_successful_fetch_at(&connection)?,
    })
}

pub fn save_feed(
    db_path: &Path,
    feed_items: &[FeedSourceItem],
) -> Result<FeedRefreshResult, String> {
    let mut connection = open(db_path)?;
    let transaction = connection.transaction().map_err(display_error)?;
    let seen_at = utc_now();
    let mut new_count = 0usize;

    for item in feed_items {
        let exists = transaction
            .query_row(
                "SELECT 1 FROM feed_items WHERE paper_id = ?1",
                [&item.paper_id],
                |_| Ok(()),
            )
            .optional()
            .map_err(display_error)?
            .is_some();
        if !exists {
            new_count += 1;
        }
        let authors_json = serde_json::to_string(&item.authors).map_err(display_error)?;
        transaction
            .execute(
                r#"
                INSERT INTO feed_items (
                    paper_id, title, authors_json, abstract, url, source_url, guid,
                    first_seen_at, last_seen_at
                )
                VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?8)
                ON CONFLICT(paper_id) DO UPDATE SET
                    title = excluded.title,
                    authors_json = excluded.authors_json,
                    abstract = excluded.abstract,
                    url = excluded.url,
                    source_url = excluded.source_url,
                    guid = excluded.guid,
                    last_seen_at = excluded.last_seen_at
                "#,
                params![
                    item.paper_id,
                    item.title,
                    authors_json,
                    item.abstract_text,
                    item.url,
                    item.source_url,
                    item.guid,
                    seen_at,
                ],
            )
            .map_err(display_error)?;
    }

    transaction
        .execute(
            r#"
            INSERT INTO feed_fetches (source_url, fetched_at, total_count, new_count)
            VALUES (?1, ?2, ?3, ?4)
            "#,
            params![NBER_FEED_URL, seen_at, feed_items.len(), new_count],
        )
        .map_err(display_error)?;
    let total_count: i64 = transaction
        .query_row("SELECT COUNT(*) FROM feed_items", [], |row| row.get(0))
        .map_err(display_error)?;
    transaction.commit().map_err(display_error)?;

    Ok(FeedRefreshResult {
        new_count,
        total_count: total_count as usize,
        fetched_count: feed_items.len(),
        last_successful_fetch_at: Some(seen_at),
    })
}

pub fn feed_paper_url(db_path: &Path, paper_id: &str) -> Result<Option<String>, String> {
    open(db_path)?
        .query_row(
            "SELECT url FROM feed_items WHERE paper_id = ?1",
            [paper_id],
            |row| row.get(0),
        )
        .optional()
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

pub fn read_cached_paper(
    db_path: &Path,
    paper_id: &str,
    ttl_days: u16,
) -> Result<Option<PaperMetadata>, String> {
    let connection = open(db_path)?;
    let cached = connection
        .query_row(
            r#"
            SELECT title, authors_json, date, abstract, url, published_version,
                   topic, programs, last_fetched_at
            FROM info_cache WHERE paper_id = ?1
            "#,
            [paper_id],
            |row| {
                let authors_json: String = row.get(1)?;
                Ok((
                    PaperMetadata {
                        paper_id: paper_id.to_string(),
                        title: row.get(0)?,
                        authors: decode_authors(&authors_json),
                        date: row.get(2)?,
                        abstract_text: row.get(3)?,
                        url: row.get(4)?,
                        published_version: row.get(5)?,
                        topic: row.get(6)?,
                        programs: row.get(7)?,
                    },
                    row.get::<_, String>(8)?,
                ))
            },
        )
        .optional()
        .map_err(display_error)?;
    let Some((paper, last_fetched_at)) = cached else {
        return Ok(None);
    };
    if cache_expired(&last_fetched_at, ttl_days) {
        return Ok(None);
    }
    connection
        .execute(
            r#"
            UPDATE info_cache
            SET last_fetched_at = ?1, fetch_count = fetch_count + 1
            WHERE paper_id = ?2
            "#,
            params![utc_now(), paper_id],
        )
        .map_err(display_error)?;
    Ok(Some(paper))
}

pub fn write_paper_cache(db_path: &Path, paper: &PaperMetadata) -> Result<(), String> {
    let now = utc_now();
    let authors_json = serde_json::to_string(&paper.authors).map_err(display_error)?;
    open(db_path)?
        .execute(
            r#"
            INSERT INTO info_cache (
                paper_id, title, authors_json, date, abstract, url,
                published_version, topic, programs,
                first_cached_at, last_fetched_at, fetch_count
            )
            VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?10, 0)
            ON CONFLICT(paper_id) DO UPDATE SET
                title = excluded.title,
                authors_json = excluded.authors_json,
                date = excluded.date,
                abstract = excluded.abstract,
                url = excluded.url,
                published_version = excluded.published_version,
                topic = excluded.topic,
                programs = excluded.programs,
                last_fetched_at = excluded.last_fetched_at
            "#,
            params![
                paper.paper_id,
                paper.title,
                authors_json,
                paper.date,
                paper.abstract_text,
                paper.url,
                paper.published_version,
                paper.topic,
                paper.programs,
                now,
            ],
        )
        .map(|_| ())
        .map_err(display_error)
}

fn open(db_path: &Path) -> Result<Connection, String> {
    let connection = Connection::open(db_path).map_err(display_error)?;
    connection
        .busy_timeout(Duration::from_secs(5))
        .map_err(display_error)?;
    Ok(connection)
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

fn decode_authors(value: &str) -> Vec<String> {
    serde_json::from_str(value).unwrap_or_default()
}

fn cache_expired(last_fetched_at: &str, ttl_days: u16) -> bool {
    let Ok(fetched_at) = DateTime::parse_from_rfc3339(last_fetched_at) else {
        return true;
    };
    fetched_at.with_timezone(&Utc) < Utc::now() - ChronoDuration::days(i64::from(ttl_days))
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
    use std::path::PathBuf;

    fn temporary_database(name: &str) -> PathBuf {
        std::env::temp_dir().join(format!("nber-cli-desktop-{name}-{}.db", std::process::id()))
    }

    #[test]
    fn schema_and_read_status_are_cli_compatible() {
        let path = temporary_database("read-status");
        let _ = std::fs::remove_file(&path);
        ensure_schema(&path).unwrap();
        set_read_status(&path, "w12345", true).unwrap();
        let connection = Connection::open(&path).unwrap();
        let value: bool = connection
            .query_row(
                "SELECT is_read FROM read_status WHERE paper_id = 'w12345'",
                [],
                |row| row.get(0),
            )
            .unwrap();
        let version: u8 = connection
            .pragma_query_value(None, "user_version", |row| row.get(0))
            .unwrap();
        assert!(value);
        assert_eq!(version, SCHEMA_VERSION);
        drop(connection);
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn rejects_future_database_schema() {
        let path = temporary_database("future-schema");
        let _ = std::fs::remove_file(&path);
        let connection = Connection::open(&path).unwrap();
        connection.pragma_update(None, "user_version", 99).unwrap();
        drop(connection);
        assert!(ensure_schema(&path)
            .unwrap_err()
            .contains("newer than supported"));
        let _ = std::fs::remove_file(path);
    }
}
