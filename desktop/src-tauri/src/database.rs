use crate::models::{FeedItem, FeedList, FeedRefreshResult, Paper, PaperTag, PaperTagSource};
use chrono::{SecondsFormat, Utc};
use rusqlite::{params, Connection, OptionalExtension};
use std::{collections::HashMap, path::Path, time::Duration};

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
    if !db_path.exists() {
        return Ok(FeedList {
            items: Vec::new(),
            total_count: 0,
            limit,
            offset,
            last_successful_fetch_at: None,
        });
    }
    validate_schema(db_path)?;
    let connection = open(db_path)?;
    ensure_desktop_tables(&connection)?;
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
                tags: Vec::new(),
            })
        })
        .map_err(display_error)?;
    let mut items = rows.collect::<Result<Vec<_>, _>>().map_err(display_error)?;
    drop(statement);
    let mut tags_by_paper = all_visible_tags(&connection)?;
    for item in &mut items {
        item.tags = tags_by_paper.remove(&item.paper_id).unwrap_or_default();
    }
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
    info_fetched_count: usize,
    info_cached_count: usize,
    info_failed_count: usize,
) -> Result<FeedRefreshResult, String> {
    validate_schema(db_path)?;
    let connection = open(db_path)?;
    ensure_desktop_tables(&connection)?;
    Ok(FeedRefreshResult {
        new_count,
        total_count: feed_total_count(&connection)?,
        fetched_count,
        info_fetched_count,
        info_cached_count,
        info_failed_count,
        last_successful_fetch_at: last_successful_fetch_at(&connection)?,
    })
}

pub fn get_paper(db_path: &Path, paper_id: &str) -> Result<Paper, String> {
    validate_schema(db_path)?;
    let connection = open(db_path)?;
    ensure_desktop_tables(&connection)?;
    let paper = connection
        .query_row(
            r#"
            SELECT
                feed_items.paper_id,
                COALESCE(info_cache.title, feed_items.title),
                COALESCE(info_cache.authors_json, feed_items.authors_json),
                COALESCE(info_cache.date, ''),
                COALESCE(info_cache.abstract, feed_items.abstract),
                COALESCE(info_cache.url, feed_items.url),
                info_cache.published_version,
                info_cache.topic,
                info_cache.programs,
                COALESCE(read_status.is_read, 0),
                CASE WHEN info_cache.paper_id IS NULL THEN 0 ELSE 1 END
            FROM feed_items
            LEFT JOIN info_cache ON info_cache.paper_id = feed_items.paper_id
            LEFT JOIN read_status ON read_status.paper_id = feed_items.paper_id
            WHERE feed_items.paper_id = ?1
            "#,
            [paper_id],
            |row| {
                let authors_json: String = row.get(2)?;
                Ok(Paper {
                    paper_id: row.get(0)?,
                    title: row.get(1)?,
                    authors: serde_json::from_str(&authors_json).unwrap_or_default(),
                    date: row.get(3)?,
                    abstract_text: row.get(4)?,
                    url: row.get(5)?,
                    pdf_url: Some(format!(
                        "https://www.nber.org/system/files/working_papers/{paper_id}/{paper_id}.pdf"
                    )),
                    published_version: row.get(6)?,
                    topic: row.get(7)?,
                    programs: row.get(8)?,
                    is_read: row.get(9)?,
                    from_cache: row.get(10)?,
                    tags: Vec::new(),
                })
            },
        )
        .optional()
        .map_err(display_error)?;
    let mut paper = paper.ok_or_else(|| format!("paper not found: {paper_id}"))?;
    paper.tags = visible_tags(&connection, paper_id)?;
    Ok(paper)
}

pub fn set_read_status(db_path: &Path, paper_id: &str, is_read: bool) -> Result<(), String> {
    validate_schema(db_path)?;
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

pub fn ensure_desktop_storage(db_path: &Path) -> Result<(), String> {
    validate_schema(db_path)?;
    ensure_desktop_tables(&open(db_path)?)
}

pub fn sync_raw_tags(db_path: &Path) -> Result<(), String> {
    validate_schema(db_path)?;
    let mut connection = open(db_path)?;
    ensure_desktop_tables(&connection)?;
    let cached_metadata = {
        let mut statement = connection
            .prepare(
                r#"
                SELECT info.paper_id, info.topic, info.programs, info.last_fetched_at
                FROM info_cache info
                LEFT JOIN desktop_raw_tag_sync_state state
                    ON state.paper_id = info.paper_id
                WHERE state.info_fetched_at IS NULL
                   OR state.info_fetched_at != info.last_fetched_at
                "#,
            )
            .map_err(display_error)?;
        let rows = statement
            .query_map([], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, Option<String>>(1)?,
                    row.get::<_, Option<String>>(2)?,
                    row.get::<_, String>(3)?,
                ))
            })
            .map_err(display_error)?;
        rows.collect::<Result<Vec<_>, _>>().map_err(display_error)?
    };
    let transaction = connection.transaction().map_err(display_error)?;
    for (paper_id, topic, programs, info_fetched_at) in cached_metadata {
        if topic.as_deref().is_none_or(|value| value.trim().is_empty())
            && programs
                .as_deref()
                .is_none_or(|value| value.trim().is_empty())
        {
            continue;
        }
        transaction
            .execute(
                "DELETE FROM desktop_raw_tags WHERE paper_id = ?1",
                [&paper_id],
            )
            .map_err(display_error)?;
        insert_raw_values(
            &transaction,
            &paper_id,
            topic.as_deref(),
            PaperTagSource::Topic,
        )?;
        transaction
            .execute(
                r#"
                INSERT INTO desktop_raw_tag_sync_state
                    (paper_id, info_fetched_at, synced_at)
                VALUES (?1, ?2, ?3)
                ON CONFLICT(paper_id) DO UPDATE SET
                    info_fetched_at = excluded.info_fetched_at,
                    synced_at = excluded.synced_at
                "#,
                params![paper_id, info_fetched_at, utc_now()],
            )
            .map_err(display_error)?;
        insert_raw_values(
            &transaction,
            &paper_id,
            programs.as_deref(),
            PaperTagSource::Program,
        )?;
    }
    transaction.commit().map_err(display_error)
}

pub fn add_user_tag(db_path: &Path, paper_id: &str, tag: &str) -> Result<Vec<PaperTag>, String> {
    validate_schema(db_path)?;
    let connection = open(db_path)?;
    ensure_desktop_tables(&connection)?;
    ensure_paper_exists(&connection, paper_id)?;
    let normalized = normalize_tag(tag)?;
    let now = utc_now();
    connection
        .execute(
            r#"
            INSERT INTO desktop_user_tags (paper_id, tag, created_at, updated_at)
            VALUES (?1, ?2, ?3, ?3)
            ON CONFLICT(paper_id, tag) DO UPDATE SET updated_at = excluded.updated_at
            "#,
            params![paper_id, normalized, now],
        )
        .map_err(display_error)?;
    visible_tags(&connection, paper_id)
}

pub fn remove_tag(
    db_path: &Path,
    paper_id: &str,
    tag: &str,
    source: PaperTagSource,
) -> Result<Vec<PaperTag>, String> {
    validate_schema(db_path)?;
    let connection = open(db_path)?;
    ensure_desktop_tables(&connection)?;
    let normalized = normalize_tag(tag)?;
    if source == PaperTagSource::User {
        connection
            .execute(
                "DELETE FROM desktop_user_tags WHERE paper_id = ?1 AND tag = ?2 COLLATE NOCASE",
                params![paper_id, normalized],
            )
            .map_err(display_error)?;
    } else {
        connection
            .execute(
                r#"
                INSERT INTO desktop_hidden_raw_tags (paper_id, tag, hidden_at)
                VALUES (?1, ?2, ?3)
                ON CONFLICT(paper_id, tag) DO UPDATE SET hidden_at = excluded.hidden_at
                "#,
                params![paper_id, normalized, utc_now()],
            )
            .map_err(display_error)?;
    }
    visible_tags(&connection, paper_id)
}

pub fn rename_tag(
    db_path: &Path,
    paper_id: &str,
    old_tag: &str,
    new_tag: &str,
    source: PaperTagSource,
) -> Result<Vec<PaperTag>, String> {
    validate_schema(db_path)?;
    let mut connection = open(db_path)?;
    ensure_desktop_tables(&connection)?;
    ensure_paper_exists(&connection, paper_id)?;
    let old_normalized = normalize_tag(old_tag)?;
    let new_normalized = normalize_tag(new_tag)?;
    let now = utc_now();
    let transaction = connection.transaction().map_err(display_error)?;
    if source == PaperTagSource::User {
        transaction
            .execute(
                "DELETE FROM desktop_user_tags WHERE paper_id = ?1 AND tag = ?2 COLLATE NOCASE",
                params![paper_id, old_normalized],
            )
            .map_err(display_error)?;
    } else {
        transaction
            .execute(
                r#"
                INSERT INTO desktop_hidden_raw_tags (paper_id, tag, hidden_at)
                VALUES (?1, ?2, ?3)
                ON CONFLICT(paper_id, tag) DO UPDATE SET hidden_at = excluded.hidden_at
                "#,
                params![paper_id, old_normalized, now],
            )
            .map_err(display_error)?;
    }
    transaction
        .execute(
            r#"
            INSERT INTO desktop_user_tags (paper_id, tag, created_at, updated_at)
            VALUES (?1, ?2, ?3, ?3)
            ON CONFLICT(paper_id, tag) DO UPDATE SET updated_at = excluded.updated_at
            "#,
            params![paper_id, new_normalized, now],
        )
        .map_err(display_error)?;
    transaction.commit().map_err(display_error)?;
    visible_tags(&connection, paper_id)
}

fn ensure_desktop_tables(connection: &Connection) -> Result<(), String> {
    connection
        .execute_batch(
            r#"
            CREATE TABLE IF NOT EXISTS desktop_raw_tags (
                paper_id TEXT NOT NULL,
                tag TEXT NOT NULL COLLATE NOCASE,
                source TEXT NOT NULL CHECK (source IN ('topic', 'program')),
                last_synced_at TEXT NOT NULL,
                PRIMARY KEY (paper_id, tag, source)
            );
            CREATE TABLE IF NOT EXISTS desktop_user_tags (
                paper_id TEXT NOT NULL,
                tag TEXT NOT NULL COLLATE NOCASE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (paper_id, tag)
            );
            CREATE TABLE IF NOT EXISTS desktop_hidden_raw_tags (
                paper_id TEXT NOT NULL,
                tag TEXT NOT NULL COLLATE NOCASE,
                hidden_at TEXT NOT NULL,
                PRIMARY KEY (paper_id, tag)
            );
            CREATE TABLE IF NOT EXISTS desktop_raw_tag_sync_state (
                paper_id TEXT PRIMARY KEY,
                info_fetched_at TEXT NOT NULL,
                synced_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_desktop_raw_tags_tag
                ON desktop_raw_tags(tag COLLATE NOCASE);
            CREATE INDEX IF NOT EXISTS idx_desktop_user_tags_tag
                ON desktop_user_tags(tag COLLATE NOCASE);
            "#,
        )
        .map_err(display_error)
}

fn insert_raw_values(
    connection: &Connection,
    paper_id: &str,
    values: Option<&str>,
    source: PaperTagSource,
) -> Result<(), String> {
    for tag in split_raw_tags(values) {
        connection
            .execute(
                r#"
                INSERT OR IGNORE INTO desktop_raw_tags
                    (paper_id, tag, source, last_synced_at)
                VALUES (?1, ?2, ?3, ?4)
                "#,
                params![paper_id, tag, source.as_str(), utc_now()],
            )
            .map_err(display_error)?;
    }
    Ok(())
}

fn split_raw_tags(values: Option<&str>) -> Vec<String> {
    values
        .unwrap_or_default()
        .split(';')
        .filter_map(|value| normalize_tag(value).ok())
        .collect()
}

fn normalize_tag(value: &str) -> Result<String, String> {
    let normalized = value.split_whitespace().collect::<Vec<_>>().join(" ");
    if normalized.is_empty() {
        return Err("tag cannot be empty".to_string());
    }
    if normalized.chars().count() > 60 {
        return Err("tag cannot be longer than 60 characters".to_string());
    }
    Ok(normalized)
}

fn ensure_paper_exists(connection: &Connection, paper_id: &str) -> Result<(), String> {
    let exists: bool = connection
        .query_row(
            "SELECT EXISTS(SELECT 1 FROM feed_items WHERE paper_id = ?1)",
            [paper_id],
            |row| row.get(0),
        )
        .map_err(display_error)?;
    if exists {
        Ok(())
    } else {
        Err(format!("paper not found: {paper_id}"))
    }
}

fn visible_tags(connection: &Connection, paper_id: &str) -> Result<Vec<PaperTag>, String> {
    let mut statement = connection
        .prepare(
            r#"
            SELECT tag, source FROM (
                SELECT tag, 'user' AS source, 0 AS priority
                FROM desktop_user_tags
                WHERE paper_id = ?1
                UNION ALL
                SELECT raw.tag, raw.source, CASE raw.source WHEN 'topic' THEN 1 ELSE 2 END
                FROM desktop_raw_tags raw
                WHERE raw.paper_id = ?1
                  AND NOT EXISTS (
                      SELECT 1 FROM desktop_hidden_raw_tags hidden
                      WHERE hidden.paper_id = raw.paper_id
                        AND hidden.tag = raw.tag COLLATE NOCASE
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM desktop_user_tags user
                      WHERE user.paper_id = raw.paper_id
                        AND user.tag = raw.tag COLLATE NOCASE
                  )
            )
            GROUP BY tag COLLATE NOCASE
            ORDER BY MIN(priority), tag COLLATE NOCASE
            "#,
        )
        .map_err(display_error)?;
    let rows = statement
        .query_map([paper_id], |row| {
            let source: String = row.get(1)?;
            Ok(PaperTag {
                name: row.get(0)?,
                source: match source.as_str() {
                    "topic" => PaperTagSource::Topic,
                    "program" => PaperTagSource::Program,
                    _ => PaperTagSource::User,
                },
            })
        })
        .map_err(display_error)?;
    rows.collect::<Result<Vec<_>, _>>().map_err(display_error)
}

fn all_visible_tags(connection: &Connection) -> Result<HashMap<String, Vec<PaperTag>>, String> {
    let mut statement = connection
        .prepare(
            r#"
            SELECT paper_id, tag, source FROM (
                SELECT paper_id, tag, 'user' AS source, 0 AS priority
                FROM desktop_user_tags
                UNION ALL
                SELECT raw.paper_id, raw.tag, raw.source,
                       CASE raw.source WHEN 'topic' THEN 1 ELSE 2 END
                FROM desktop_raw_tags raw
                WHERE NOT EXISTS (
                    SELECT 1 FROM desktop_hidden_raw_tags hidden
                    WHERE hidden.paper_id = raw.paper_id
                      AND hidden.tag = raw.tag COLLATE NOCASE
                )
                AND NOT EXISTS (
                    SELECT 1 FROM desktop_user_tags user
                    WHERE user.paper_id = raw.paper_id
                      AND user.tag = raw.tag COLLATE NOCASE
                )
            )
            GROUP BY paper_id, tag COLLATE NOCASE
            ORDER BY paper_id, MIN(priority), tag COLLATE NOCASE
            "#,
        )
        .map_err(display_error)?;
    let rows = statement
        .query_map([], |row| {
            let source: String = row.get(2)?;
            Ok((
                row.get::<_, String>(0)?,
                PaperTag {
                    name: row.get(1)?,
                    source: match source.as_str() {
                        "topic" => PaperTagSource::Topic,
                        "program" => PaperTagSource::Program,
                        _ => PaperTagSource::User,
                    },
                },
            ))
        })
        .map_err(display_error)?;
    let mut tags_by_paper: HashMap<String, Vec<PaperTag>> = HashMap::new();
    for row in rows {
        let (paper_id, tag) = row.map_err(display_error)?;
        tags_by_paper.entry(paper_id).or_default().push(tag);
    }
    Ok(tags_by_paper)
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
    use std::path::PathBuf;

    fn temporary_database(name: &str) -> PathBuf {
        std::env::temp_dir().join(format!("nber-cli-desktop-{name}-{}.db", std::process::id()))
    }

    fn feed_database(name: &str) -> PathBuf {
        let path = temporary_database(name);
        let _ = std::fs::remove_file(&path);
        let connection = Connection::open(&path).unwrap();
        connection
            .execute_batch(
                r#"
                CREATE TABLE feed_items (
                    paper_id TEXT PRIMARY KEY, title TEXT NOT NULL,
                    authors_json TEXT NOT NULL, abstract TEXT NOT NULL,
                    url TEXT NOT NULL, source_url TEXT NOT NULL,
                    guid TEXT NOT NULL, first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                );
                CREATE TABLE info_cache (
                    paper_id TEXT PRIMARY KEY, title TEXT NOT NULL,
                    authors_json TEXT NOT NULL, date TEXT NOT NULL,
                    abstract TEXT NOT NULL, url TEXT,
                    published_version TEXT, topic TEXT, programs TEXT,
                    first_cached_at TEXT NOT NULL, last_fetched_at TEXT NOT NULL,
                    fetch_count INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE read_status (
                    paper_id TEXT PRIMARY KEY, is_read BOOLEAN NOT NULL,
                    updated_at TEXT NOT NULL
                );
                INSERT INTO feed_items VALUES (
                    'w12345', 'Feed title', '["Feed Author"]', 'Feed abstract',
                    'https://www.nber.org/papers/w12345',
                    'https://www.nber.org/papers/w12345#rss', 'w12345',
                    '2026-07-18T00:00:00Z', '2026-07-18T00:00:00Z'
                );
                PRAGMA user_version = 3;
                "#,
            )
            .unwrap();
        path
    }

    #[test]
    fn rejects_uninitialized_database() {
        let path = temporary_database("worker-schema");
        let _ = std::fs::remove_file(&path);
        Connection::open(&path).unwrap();
        assert!(validate_schema(&path).is_err());
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn missing_database_is_an_empty_feed() {
        let path = temporary_database("empty-feed");
        let _ = std::fs::remove_file(&path);

        let feed = list_feed(&path, 50, 0).unwrap();

        assert!(feed.items.is_empty());
        assert_eq!(feed.total_count, 0);
        assert!(!path.exists());
    }

    #[test]
    fn paper_falls_back_to_feed_without_cached_info() {
        let path = feed_database("paper-feed-fallback");

        let paper = get_paper(&path, "w12345").unwrap();

        assert_eq!(paper.title, "Feed title");
        assert_eq!(paper.date, "");
        assert_eq!(paper.abstract_text, "Feed abstract");
        assert!(!paper.from_cache);
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn paper_prefers_cached_info() {
        let path = feed_database("paper-info-cache");
        Connection::open(&path)
            .unwrap()
            .execute(
                r#"
                INSERT INTO info_cache VALUES (
                    'w12345', 'Cached title', '["Cached Author"]', '2026/07/18',
                    'Cached abstract', 'https://www.nber.org/papers/w12345',
                    'Published paper', 'Economics', 'EFG',
                    '2026-07-18T00:00:00Z', '2026-07-18T00:00:00Z', 0
                )
                "#,
                [],
            )
            .unwrap();

        let paper = get_paper(&path, "w12345").unwrap();

        assert_eq!(paper.title, "Cached title");
        assert_eq!(paper.authors, vec!["Cached Author"]);
        assert_eq!(paper.date, "2026/07/18");
        assert_eq!(paper.topic.as_deref(), Some("Economics"));
        assert!(paper.from_cache);
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn syncs_raw_topics_and_programs_into_visible_tags() {
        let path = feed_database("raw-tags");
        Connection::open(&path)
            .unwrap()
            .execute(
                r#"
                INSERT INTO info_cache VALUES (
                    'w12345', 'Cached title', '[]', '2026/07/18', 'Abstract', NULL,
                    NULL, 'Labor Economics; Development',
                    'Labor Studies; Economic Fluctuations and Growth',
                    '2026-07-18T00:00:00Z', '2026-07-18T00:00:00Z', 0
                )
                "#,
                [],
            )
            .unwrap();

        sync_raw_tags(&path).unwrap();
        let paper = get_paper(&path, "w12345").unwrap();

        assert_eq!(paper.tags.len(), 4);
        assert!(paper.tags.contains(&PaperTag {
            name: "Labor Economics".to_string(),
            source: PaperTagSource::Topic,
        }));
        assert!(paper.tags.contains(&PaperTag {
            name: "Labor Studies".to_string(),
            source: PaperTagSource::Program,
        }));
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn raw_and_user_tag_edits_remain_separate() {
        let path = feed_database("editable-tags");
        ensure_desktop_storage(&path).unwrap();
        let connection = Connection::open(&path).unwrap();
        connection
            .execute(
                "INSERT INTO desktop_raw_tags VALUES (?1, ?2, ?3, ?4)",
                params!["w12345", "Macroeconomics", "topic", utc_now()],
            )
            .unwrap();

        let tags = add_user_tag(&path, "w12345", "  Must   Read ").unwrap();
        assert!(tags.iter().any(|tag| tag.name == "Must Read"));

        let tags = remove_tag(&path, "w12345", "Macroeconomics", PaperTagSource::Topic).unwrap();
        assert!(!tags.iter().any(|tag| tag.name == "Macroeconomics"));

        sync_raw_tags(&path).unwrap();
        let tags = visible_tags(&Connection::open(&path).unwrap(), "w12345").unwrap();
        assert!(!tags.iter().any(|tag| tag.name == "Macroeconomics"));

        let tags = rename_tag(
            &path,
            "w12345",
            "Must Read",
            "Priority",
            PaperTagSource::User,
        )
        .unwrap();
        assert_eq!(
            tags,
            vec![PaperTag {
                name: "Priority".to_string(),
                source: PaperTagSource::User,
            }]
        );
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn renaming_raw_tag_hides_original_and_creates_user_tag() {
        let path = feed_database("rename-raw-tag");
        ensure_desktop_storage(&path).unwrap();
        Connection::open(&path)
            .unwrap()
            .execute(
                "INSERT INTO desktop_raw_tags VALUES (?1, ?2, ?3, ?4)",
                params!["w12345", "Development", "topic", utc_now()],
            )
            .unwrap();

        let tags = rename_tag(
            &path,
            "w12345",
            "Development",
            "My Development Papers",
            PaperTagSource::Topic,
        )
        .unwrap();

        assert_eq!(
            tags,
            vec![PaperTag {
                name: "My Development Papers".to_string(),
                source: PaperTagSource::User,
            }]
        );
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn validates_user_tags() {
        let path = feed_database("tag-validation");
        assert!(add_user_tag(&path, "w12345", "   ").is_err());
        assert!(add_user_tag(&path, "w12345", &"x".repeat(61)).is_err());
        let _ = std::fs::remove_file(path);
    }
}
