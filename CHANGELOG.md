# Changelog

All notable changes to this project will be documented in this file.

This file is the canonical release history. The English mirror at `docs/en/changelog.md` and the Chinese mirror at `docs/zh/changelog.md` are generated from the same source content and must stay in lock-step. Any release commit updates all three together.

## [Unreleased]

## [0.5.0] - 2026-06-16

### Security
- RSS feed parsing now uses `defusedxml` to block XML external entity (XXE) and entity expansion attacks.
- CLI downloads are restricted to the current working directory and its subdirectories by default. Use `nber-cli download --restrict false` to override per invocation. The `download.restrict_dir` config key is stored and validated, but the current CLI default remains `true`.
- Database `init` and `migrate` paths on macOS and Linux must reside within the user's home directory.
- Synchronous HTTP requests enforce TLS 1.2 as the minimum version.
- Selected info/download failure paths now avoid raw exception text; download-log messages and soft database warnings use sanitized summaries or exception class names.

### Added
- `nber-cli config show` / `get <key>` / `set <key> <value>` / `verify` for inspecting and editing `~/.nber-cli/config.json`.
- `download.concurrency` configuration option (default `3`) and the `--concurrency` / `-c` CLI flag to cap concurrent downloads.
- `--restrict true|false` flag on `nber-cli download` to control directory restriction per invocation.
- `--yes` flag for `nber-cli mcp-server`; the existing `--port` option now requires explicit confirmation when set to a non-default value.
- `sse` transport for `nber-cli mcp-server`.
- JSON Schema (`config.schema.json`) for validating `~/.nber-cli/config.json`.
- Strict raw-configuration validation that reports malformed JSON, invalid section/value types, and schema-minimum violations without silently injecting defaults.
- Plugin manifests and marketplace metadata now share the package version, and the Claude plugin skill path uses the case-sensitive tracked `./skills/NBER-CLI` directory.
- Domain invariant validation in all core dataclasses (`NBER`, `NBERSearchResults`, `NBERFeedItem`, `NBERFeedFetchResult`, clean results, and download results).
- `get_config_value`, `set_config_value`, `read_config`, `write_config`, and `validate_config` exported from the package top level.
- Paper ID format validation (`w?\d+`) across CLI, download, and MCP entry points.
- Validation of fetched paper titles, positive citation IDs, and response/request paper-ID agreement before metadata is accepted.

### Changed
- Replaced legacy `typing.Dict`, `List`, and `Optional` aliases with modern Python 3.11 syntax.
- Added `mypy` configuration and strengthened type annotations across `cli.py`, `config_store.py`, and `fetcher.py`.
- `mcp-server` transport name corrected to `streamable-http`; the existing `--port` option now uses `--yes` confirmation for non-default values.
- Retry loops in `fetcher.py` now use exponential backoff capped at 30 seconds.
- `feed fetch` skips malformed individual RSS items instead of failing the entire feed.
- Invalid configured or per-call download concurrency values are rejected or fall back to the documented safe default instead of creating an invalid semaphore.
- Database schema-changing and data-writing operations reject databases with a future `PRAGMA user_version`; the diagnostic schema-version reader remains read-only.
- Feed fetching establishes/validates the local schema before the network request, then writes feed items plus fetch history transactionally after the response is parsed; cleanup operations pair schema validation/upgrade and deletion in one SQLite transaction.
- `download.py` enables `raise_for_status=True` on `ClientSession`.
- Error handling narrowed to specific network/timeout exception types with preserved exception chains.
- Removed the info cache hit hint that was printed to stderr on cached `info` lookups.

### Fixed
- `feed fetch` now tolerates unescaped `<` characters followed by whitespace or a digit in RSS title and description text while keeping strict XML parsing for all other malformed input.
- RSS parse failures now report their line and column when available, and `feed fetch` reports runtime parse errors with exit code `1` without printing command usage.

## [0.4.0] - 2026-06-04

### Added
- `nber-cli info --refresh` skips the local `info_cache` and re-fetches the paper from NBER. The new data is written back to the cache when the cache is enabled.
- `nber-cli info cache --turn-on` / `--turn-off` toggle the `info_cache` lookup globally and persist the state to `~/.nber-cli/config.json`.
- `nber-cli info cache --set-refresh <N>` sets the cache refresh interval in days. The value is persisted to `~/.nber-cli/config.json` and used as the TTL for every subsequent `info` call. Defaults to `30` days.
- `nber-cli info cache clear` with `--days`, `--all`, `--start-date`, or `--end-date` mirrors the `feed clean` parameter set, using `last_fetched_at` from the `info_cache` table. `nber-cli info cache clean` is a convenience alias for `clear --all`.
- `nber-cli info cache` (no sub-action) prints the current cache state, TTL, and cached row count.
- New `nber_cli.config_store` module: centralised read and write of `~/.nber-cli/config.json` plus the `InfoCacheSettings` dataclass and helpers (`get_info_cache_settings`, `set_info_cache_enabled`, `set_info_cache_ttl_days`).
- New `nber_cli.info_cache.get_paper_with_info_cache_result` async helper (in the `nber_cli.info_cache` module) that returns an `InfoCacheLookupResult` carrying the `NBER` paper and a `from_cache` flag, so callers (CLI and MCP) can surface a "loaded from cache" hint.
- Public Python API exports from the package top level: `InfoCacheSettings`, `clear_info_cache`, `count_info_cache`, `get_info_cache_settings`, `get_info_cache_ttl_days`, `is_info_cache_enabled`, `is_info_cache_expired`, `set_info_cache_enabled`, `set_info_cache_ttl_days`, `NBERInfoCacheClearResult`. `InfoCacheLookupResult` and `get_paper_with_info_cache_result` are exposed from the `nber_cli.info_cache` module rather than the package top level; import them as `from nber_cli.info_cache import ...`.

### Changed
- `~/.nber-cli/config.json` now carries an `info` section: `info.cache_enabled` (default `true`) and `info.cache_ttl_days` (default `30`). Missing or malformed fields fall back to defaults.
- `info` now prints a one-line stderr hint when the paper was served from the local cache, pointing to `nber-cli info <id> --refresh` for a fresh fetch.

## [0.3.1] - 2026-06-03

### Added
- `db init` and `db migrate` top-level subcommands replace `feed init` and `feed migrate`. The database is now general-purpose and stores feed cache, behavior logs, and paper metadata cache.
- `info_cache` table caches paper metadata fetched via `info` and the MCP `get_paper_info` tool. Subsequent lookups return immediately from the cache.
- `query_log`, `download_log`, and `info_log` tables record search keywords, download outcomes, and paper info lookups for later auditing.
- `schema_version` field written to `~/.nber-cli/config.json` so future schema migrations can roll forward safely.

### Changed
- Default database renamed from `feed.db` to `nber.db`. Existing `~/.nber-cli/feed.db` installations continue to work without manual steps.
- Database schema upgraded from `user_version = 1` to `user_version = 2`. Existing v1 databases are upgraded automatically on next CLI invocation; original `feed_items` rows are preserved.
- Database code consolidated into `nber_cli.db`. The original `init_feed_database`, `migrate_feed_database`, and `get_feed_database_path` helpers are kept as thin compatibility wrappers.

## [0.3.0] - 2026-06-03

### Added
- `feed init` subcommand: initialize a local SQLite feed cache and write its path to user config.
- `feed fetch` subcommand: fetch NBER's new working papers RSS feed, cache seen items, and show newly discovered papers by default.
- `feed fetch --max-items`: limit displayed feed output. When used without `--display-all`, display-all behavior is enabled automatically.
- `feed migrate` subcommand: move the feed cache database and SQLite sidecar files to a new path, then update user config.
- `feed clean` subcommand: clean cached feed database records by age, date range, or all records after interactive confirmation.
- Python API exports for feed cache helpers and feed result models.

### Changed
- Added user config support at `~/.nber-cli/config.json` for the feed cache database path.
- Expanded English and Chinese documentation for feed commands, configuration, Python API, and release notes.

## [0.2.0] - 2026-05-31

### Added
- `download` subcommand: single paper ID or batch mode (`--batch`), explicit file path (`--file`), target directory (`--save-base`).
- `info` subcommand: paper metadata with `--all` flag for full details and `--format json` option.
- `search` subcommand: full-text search with date filters (`--start-date`, `--end-date`), pagination (`--page`, `--per-page`), `--format json` option.
- `mcp-server` subcommand: MCP server for AI agent integration with stdio and streamable_http transports.

### Changed
- Reworked CLI into subcommand syntax (`nber-cli <subcommand>`).
- Simplified downloader to direct async HTTP PDF fetches (removed database-backed state tracking).
- Removed legacy web UI module and script entrypoint.

## [0.1.4] - 2025-08-09

### Added
- Added `--version` / `-v` flag to display current version.
- Added comprehensive help message with examples.
- Added `__main__.py` file to support `python -m nber_cli` usage.
- Added argument grouping for better CLI organization.
- Added automatic help display when no arguments are provided.
