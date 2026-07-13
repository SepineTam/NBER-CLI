# Persistence Layer

NBER-CLI uses a local SQLite database plus a JSON config file. The database stores caches and operational logs; the config file stores user-selected runtime settings such as the database path, info cache behavior, and download defaults.

## Files

| File | Default path | Purpose |
| --- | --- | --- |
| Config | `~/.nber-cli/config.json` | Stores `schema_version`, database path, cache, download, and Desktop settings. |
| Database | `~/.nber-cli/nber.db` | Stores feed cache, paper info cache, and behavior logs. |
| Legacy database | `~/.nber-cli/feed.db` | Used only as a fallback when upgrading from older releases and no `nber.db` exists. |
| Debug log | `~/.nber-cli/debug.log` | Rotating log file for warnings, errors, and debug output when enabled. |
| Desktop sidecar logs | `~/.nber-cli/logs/sidecar.stdout.log`, `sidecar.stderr.log` | Output and errors from the bundled local HTTP service. |

## Database Tables

| Table | Primary use | Written by | Cleaned by |
| --- | --- | --- | --- |
| `feed_items` | Cached RSS paper entries keyed by paper ID. | `feed fetch` | `feed clean` |
| `feed_fetches` | Audit trail for RSS fetch attempts and counts. | `feed fetch` | No CLI cleanup command. |
| `read_status` | Per-paper read/unread state used by the local HTTP API and Desktop app. | Desktop / HTTP API | No CLI cleanup command. |
| `info_cache` | Cached paper metadata used by `info` and `get_paper_info`. | `info`, MCP `get_paper_info` | `info cache clear` |
| `query_log` | CLI search query history and result counts. | CLI `search` | No CLI cleanup command. |
| `download_log` | CLI download successes and failures. | CLI `download` | No CLI cleanup command. |
| `info_log` | Paper info lookup history. | CLI `info`, MCP `get_paper_info` | No CLI cleanup command. |

The schema version is stored in SQLite `PRAGMA user_version`. Version `3` is the current schema. Existing v1 and v2 databases upgrade automatically on the next database-backed CLI operation or when the local HTTP server starts. The v2-to-v3 migration adds `read_status` without removing existing feed, cache, or log rows. NBER-CLI refuses to write to a database created by a newer schema version.

## Info Cache Behavior

The info cache is controlled by:

```json
{
  "info": {
    "cache_enabled": true,
    "cache_ttl_days": 30
  }
}
```

When the cache is enabled, `info` and MCP `get_paper_info` first check `info_cache`. A fresh cache hit returns local data and then updates `last_fetched_at` plus `fetch_count`. This makes the TTL sliding: frequently used paper metadata remains fresh relative to the most recent local hit.

Use `--refresh` on the CLI to bypass the cache for one `info` call:

```bash
nber-cli info w25000 --refresh
```

The MCP tool does not expose a per-call refresh flag. To force a live MCP lookup, disable the cache temporarily or wait for the TTL to expire.

## Feed Cache Behavior

`feed fetch` stores every fetched RSS item, then returns either only newly discovered items or all fetched items:

```bash
nber-cli feed fetch
nber-cli feed fetch --display-all true
nber-cli feed fetch --max-items 5
```

`feed_items` is keyed by paper ID. Existing rows are updated with the latest title, abstract, URL, source URL, GUID, authors, and `last_seen_at`. New rows keep their original `first_seen_at`.

`feed_fetches` is an append-only audit table. `feed clean` does not remove it.

## Logs and Soft Failures

Search, download, and info operations try to append behavior logs. These writes are intentionally non-critical: a database error can emit a warning, but it should not prevent the main search, download, or metadata lookup from completing.

Cache reads also fail soft where possible. If a cache read cannot be completed safely, the command falls back to the network path or returns an empty cache count depending on the helper.

## Migration and Path Rules

Initialize or move the database:

```bash
nber-cli db init
nber-cli db init --db-path ~/data/nber.db
nber-cli db init --db-path sqlite:////Users/name/data/nber.db
nber-cli db migrate ~/data/nber.db
```

On macOS and Linux, the database path must stay inside the user's home directory. This limit avoids accidental writes into system or shared locations. The destination for `db migrate` must not already exist, and sidecar files such as `-wal`, `-shm`, and `-journal` move with the database.

## Cleanup Coverage

```bash
nber-cli feed clean --days 30
nber-cli feed clean --all
nber-cli info cache clear --days 30
nber-cli info cache clear --all
```

Both cleanup commands show a preview and require confirmation before deleting rows. `feed clean` deletes only `feed_items`. `info cache clear` deletes only `info_cache`. Logs and `feed_fetches` require manual SQLite maintenance or a fresh database.

## Backup

For a safe backup, close Desktop and stop any running CLI, MCP, or local HTTP server process. Copy `nber.db` together with any `nber.db-wal` and `nber.db-shm` sidecar files. For a database that must remain online, use SQLite's backup command:

```bash
sqlite3 ~/.nber-cli/nber.db ".backup '/path/to/nber-backup.db'"
```
