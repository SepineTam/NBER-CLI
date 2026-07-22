# Configuration

Most NBER-CLI runtime behavior uses built-in defaults. The local database also uses a small user config file to remember the database location selected by `nber-cli db init` or `nber-cli db migrate`.

For the full SQLite schema, cache tables, behavior logs, and backup guidance, see [Persistence Layer](persistence.md).

## Runtime Defaults

| Setting | Default | Description |
| --- | --- | --- |
| Request timeout | `60` seconds | Total timeout for network requests. |
| Retry count | `3` | Failed eligible requests are retried before surfacing the error. |
| Request attempts | `4` | Derived from retry count plus the first attempt. |
| Download connection limit | `100` | Maximum concurrent download connections. |
| Per-host connection limit | `10` | Maximum concurrent connections to one host. |
| Search page sizes | `20`, `50`, `100` | Accepted values for `--per-page`. |

These values live in `NBERCLIConfig` and `NBER_CLI_CONFIG`. They are **compile-time constants**: they are not exposed in `~/.nber-cli/config.json`, are not read from any environment variable, and are not settable through CLI flags. To change them you must edit the source code and reinstall the package.

If you need different transport behavior at runtime, call the Python API directly and pass a custom `aiohttp.ClientSession` with the timeout and connector limits you want. The package still wraps eligible requests with its own fixed-attempt retry helper; changing the retry count requires a source change.

## What is configurable today

The following list is exhaustive — values not listed here are constants.

| Surface | Configurable? | Where |
| --- | --- | --- |
| `info.cache_enabled` | Yes | `~/.nber-cli/config.json`; toggle via `nber-cli info cache --turn-on/--off` |
| `info.cache_ttl_days` | Yes | `~/.nber-cli/config.json`; set via `nber-cli info cache --set-refresh <N>` |
| `feed.db-path` (database path or `sqlite:///...` URL) | Yes | `~/.nber-cli/config.json`; set via `nber-cli db init --db-path ...` or `nber-cli db migrate ...` |
| `download.restrict_dir` | Stored, not used as the CLI default | `~/.nber-cli/config.json`; the current CLI still defaults `--restrict` to `true` on every invocation |
| `download.concurrency` | Yes | `~/.nber-cli/config.json`; set via `nber-cli config set download.concurrency <N>` |
| `desktop.server_port` | Legacy / HTTP settings API only | Ignored by Desktop; `nber-server` binds from `--port` and does not read this field. |
| `desktop.feed_refresh_interval_minutes` | Yes | `~/.nber-cli/config.json` or Desktop Settings; valid range `1`–`65535` |
| `desktop.detail_font_size` | Yes | Desktop Settings; accepted values are `14`, `16`, and `18` |
| Desktop preview width | Yes, device-local | WebView local storage; range `360`–`640` px, default `420` px |
| Request timeout | **No** | Code constant in `NBERCLIConfig` |
| Retry count / request attempts | **No** | Code constant in `NBERCLIConfig` |
| Download connection limits | **No** | Code constant in `NBERCLIConfig` |
| Per-host connection limit | **No** | Code constant in `NBERCLIConfig` |
| Search page sizes | **No** | Code constant in `NBERCLIConfig` |
| User-Agent string | **No** | Hard-coded Chrome-like value sent on every request |
| Other HTTP headers | **No** | Hard-coded browser-like headers sent on all requests |

## User Config File

The user config file is:

```text
~/.nber-cli/config.json
```

Current schema:

```json
{
  "schema_version": 3,
  "feed": {
    "db-path": "/Users/name/.nber-cli/nber.db"
  },
  "info": {
    "cache_enabled": true,
    "cache_ttl_days": 30
  },
  "download": {
    "restrict_dir": true,
    "concurrency": 3
  },
  "desktop": {
    "feed_refresh_interval_minutes": 60,
    "detail_font_size": 16
  }
}
```

`feed.db-path` points to the local database used by the Python `info`, `search`, `download`, and `feed` paths. It may be a normal filesystem path or a SQLite URL such as `sqlite:///relative/nber.db` or `sqlite:////Users/name/data/nber.db`. The historical `feed` key name is preserved for backward compatibility; the database itself is general-purpose. The optional HTTP server has a [documented custom-path split](http-api.md#install-and-start), so pass the same path with `nber-server --db-path`.

`download.restrict_dir` is currently stored and schema-validated, but the CLI does not use it as the default for downloads. Each invocation defaults to restricted mode. Use `--restrict false` explicitly for an unrestricted invocation.

`download.concurrency` caps the number of concurrent downloads. It defaults to `3` and can be overridden per invocation with `--concurrency <N>`.

`schema_version` records the current database schema version. NBER-CLI updates it after `db init` or schema upgrades.

Desktop does not run a local server, so it ignores the legacy `desktop.server_port` value. The optional `nber-server` also does not read this field when binding; its actual port comes from `--port`. `desktop.feed_refresh_interval_minutes` controls automatic Feed refresh and must be between `1` and `65535`. The timer runs only while Desktop is open, initialized, visible, and not already refreshing.

`desktop.detail_font_size` controls paper-detail reading text. Desktop accepts only `14`, `16`, or `18` and defaults invalid or missing values to `16`. The preview-pane width is not written to this file; it is stored in WebView local storage for the current device.

`info.cache_enabled` controls the `info_cache` lookup globally. Set to `false` to force every `info` call (and the MCP `get_paper_info` tool) to go straight to NBER. Defaults to `true`.

`info.cache_ttl_days` sets the refresh interval in days. The TTL is **sliding**: every cache hit updates the row's `last_fetched_at` (via `touch_info_cache`) and increments `fetch_count`, so repeatedly consulted papers keep their cached copy for at least `cache_ttl_days` after the most recent hit. Cached entries whose `last_fetched_at` is older than the TTL threshold are treated as cache misses and re-fetched on the next `info` call. Must be a positive integer. Defaults to `30`.

Both `info` keys are managed by `nber-cli info cache --turn-on/--off/--set-refresh <N>`. Missing or malformed fields fall back to defaults and never cause NBER-CLI to fail.

## Local Database

Default database path:

```text
~/.nber-cli/nber.db
```

Initialize the default database:

```bash
nber-cli db init
```

Initialize at a custom path:

```bash
nber-cli db init --db-path ~/data/nber.db
```

Initialize with a SQLite URL:

```bash
nber-cli db init --db-path sqlite:////Users/name/data/nber.db
```

Move an existing database and update the config:

```bash
nber-cli db migrate ~/data/nber.db
```

If you upgraded from 0.3.0 and still have `~/.nber-cli/feed.db`, NBER-CLI will keep using that legacy file when no `nber.db` is present. The schema is upgraded automatically on first invocation.

The database holds:

- `feed_items` and `feed_fetches`: RSS cache used by `feed fetch` and `feed clean`.
- `info_cache`: paper metadata cache used by `info` and the MCP `get_paper_info` tool. Cache reads are gated by `info.cache_enabled` and respect the `info.cache_ttl_days` TTL.
- `read_status`: per-paper state used by Desktop and the optional HTTP API.
- `desktop_raw_tags`, `desktop_user_tags`, `desktop_hidden_raw_tags`, and `desktop_raw_tag_sync_state`: Desktop-only tag source, user, hiding, and synchronization state.
- `query_log`, `download_log`, `info_log`: behavior logs for search keywords, download outcomes, and info lookups.

### Storage, Safety, and Extensibility

The database is local-only. NBER-CLI does not send this cache or log database to project infrastructure, and no NBER-CLI server receives a copy. By default it lives under `~/.nber-cli/nber.db`; when `db init` or `db migrate` is used on macOS or Linux, the selected file must stay inside the user's home directory. This keeps the default persistence model predictable and avoids accidental writes into system or shared locations.

The on-disk format is SQLite, so the database is a self-contained file plus standard SQLite sidecar files when WAL or journaling is active. Schema changes are versioned with SQLite's `PRAGMA user_version`; NBER-CLI refuses to write to a database created by a newer schema version, which protects data from accidental downgrade writes. Operations that update cache or log rows use transactions through the SQLModel/SQLAlchemy engine, and non-critical log/cache writes fail soft so a local database problem does not break search, download, or metadata lookup workflows.

The Python access layer is SQLModel on top of SQLAlchemy. Tables are declared as typed SQLModel models, while the public API still returns filesystem `Path` values for compatibility. This gives the current CLI a stable SQLite file today and leaves room for future database work, such as richer typed queries, stricter schema migrations, or additional SQLAlchemy-supported backends, without changing the user-facing commands first.

## Database Operations

The database is created and upgraded automatically the first time any command that touches it runs. Running `nber-cli db init` is **not** required before using `info`, `search`, `download`, or `feed`; it exists for callers that want to pre-create the file or pin a non-default path. After `db init` (or after the first successful run), the schema version is recorded in `~/.nber-cli/config.json` under `schema_version`.

### Table Reference

| Table | Written by | Read by | Cleanup |
| --- | --- | --- | --- |
| `feed_items` | CLI / Desktop worker / HTTP API | CLI / Desktop / HTTP API | `feed clean` (with confirmation) |
| `feed_fetches` | CLI / Desktop worker / HTTP API | Desktop and HTTP status calculations | none |
| `read_status` | Desktop / HTTP API | Desktop / HTTP API | none |
| `info_cache` | CLI / MCP / Desktop worker / HTTP paper route | CLI / MCP / Desktop worker / HTTP paper route | `info cache clear` (with confirmation); HTTP uses configured/default Python DB, which may differ from server `--db-path` |
| `query_log` | `search` | not read by any command | none |
| `download_log` | `download` (single and batch) | not read by any command | none |
| `info_log` | `info` and `get_paper_info` | not read by any command | none |
| `desktop_raw_tags` | Desktop | Desktop | none |
| `desktop_user_tags` | Desktop | Desktop | individual tag removal |
| `desktop_hidden_raw_tags` | Desktop | Desktop | none |
| `desktop_raw_tag_sync_state` | Desktop | Desktop | none |

### CLI vs MCP Differences

- The CLI and the MCP `get_paper_info` tool both write to `info_log` and `info_cache` when the cache is enabled. Neither surface emits a separate cache-hit hint.
- `feed fetch` behaves identically in both surfaces; the MCP layer does not currently expose it.
- The CLI is the only surface that writes `query_log` (via `search`) and `download_log` (via `download`). The MCP `search_papers` and `download_paper` tools do **not** write those tables in the current version.

### Migrate and Reset

`nber-cli db migrate <new_db_path>` moves the database to a new path or SQLite URL, including any SQLite `-wal`, `-shm`, and `-journal` sidecar files, and updates `feed.db-path` in the user config. The destination must not already exist; the command refuses to overwrite an existing file.

There is no built-in command to reset the database to an empty state. The supported ways to start over are:

- Move the existing file aside with `nber-cli db migrate`, or
- Stop the CLI, delete `nber.db` (and any sidecar files) directly, and run `nber-cli db init` against a new path.

### Backups

The database is a single SQLite file plus its sidecar files. To back it up safely:

1. Stop any running `nber-cli` or MCP server process that might hold a write transaction.
2. Copy `nber.db` together with `nber.db-wal` and `nber.db-shm` (when present) into the backup location.
3. Use `sqlite3 nber.db ".backup '<backup_path>'"` for a crash-consistent snapshot without stopping the CLI; this is the recommended approach for live systems.

### Cleanup Coverage Today

- `feed clean` removes rows from `feed_items` only. `feed_fetches` is a continuously growing audit log and is **not** cleared by `feed clean --all`. To prune it, run a manual `DELETE FROM feed_fetches WHERE ...` against the database or use `sqlite3` directly.
- `info cache clear` removes rows from `info_cache` only. `info_log` is not cleared.
- `query_log`, `download_log`, and `info_log` have **no** CLI cleanup command. The only ways to remove them today are `nber-cli db migrate` to a new database, manual `sqlite3` operations, or deleting `nber.db`.

## Output Paths

Single download default:

```bash
nber-cli download w34567
```

Creates:

```text
./w34567.pdf
```

Directory-based download:

```bash
nber-cli download w34567 --save-base papers/nber
```

Creates:

```text
./papers/nber/w34567.pdf
```

Explicit file download:

```bash
nber-cli download w34567 --file papers/custom-name.pdf
```

Creates exactly the requested path, including parent directories when possible.

## Date Filtering

Search dates use `YYYY-MM-DD`.

```bash
nber-cli search "trade" --start-date 2024-01-01 --end-date 2024-12-31
```

If `--start-date` is provided without `--end-date`, NBER-CLI uses the current date as the end date.

## Network Behavior

NBER-CLI sends a full set of browser-like request headers, including `User-Agent`, `Accept`, `Accept-Language`, and `Sec-Fetch-*` values, on every request to NBER. This matches the headers a real browser sends and is required because NBER's CDN now rejects requests that only carry a minimal `User-Agent`. NBER-CLI uses retries for transient failures and raises readable errors for common download failures.

- HTTP 403 can mean a newly released paper is still under NBER's first-week access restriction.
- HTTP 404 means the paper PDF was not found.
- Timeout and connection failures are reported as network errors.

## Logging

NBER-CLI writes debug logs to `~/.nber-cli/debug.log`. The file rotates at 1 MB and keeps up to three backups. By default only warnings and errors are written to the log file.

Use `--verbose` on any command to print debug messages to stderr and capture them in the log file.

```bash
nber-cli --verbose search "labor economics"
nber-cli --verbose feed fetch
```

You can also enable debug-level logging without printing to stderr by setting `NBER_CLI_DEBUG=1`. This is useful for headless or scripted runs where you want a persistent debug trail without noisy console output.

## No Credentials Required

NBER-CLI does not require an API key. It works against public NBER web pages and NBER's public working paper search endpoint.
