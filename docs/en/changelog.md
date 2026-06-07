# Changelog

All notable changes to this project will be documented here.

This page mirrors the canonical `CHANGELOG.md` at the repository root. The Chinese mirror at `docs/zh/changelog.md` carries the same content. Any release commit updates all three together.

## 0.4.0 - 2026-06-04

### Added

- Added `nber-cli info --refresh` to bypass the local `info_cache` and re-fetch paper metadata from NBER. The fresh data is written back to the cache when the cache is enabled.
- Added `nber-cli info cache --turn-on` and `--turn-off` to toggle the `info_cache` lookup globally. The setting is persisted to `~/.nber-cli/config.json`.
- Added `nber-cli info cache --set-refresh <N>` to set the cache refresh interval in days. The value is persisted to `~/.nber-cli/config.json` and applied as the TTL for every subsequent `info` call. Defaults to `30` days.
- Added `nber-cli info cache clear` with the same parameter set as `feed clean`: `--days`, `--all`, `--start-date`, and `--end-date`. Filtering uses `last_fetched_at` from the `info_cache` table. `nber-cli info cache clean` is a convenience alias for `clear --all`.
- Added `nber-cli info cache` (no sub-action) to print the current cache state, TTL, and cached row count.
- Added `nber_cli.config_store` module with `InfoCacheSettings` and helpers (`get_info_cache_settings`, `set_info_cache_enabled`, `set_info_cache_ttl_days`) for reading and writing `~/.nber-cli/config.json`.
- Added `nber_cli.info_cache.get_paper_with_info_cache_result` async helper that returns an `InfoCacheLookupResult` carrying the `NBER` paper and a `from_cache` flag.
- Added public Python API exports from the package top level: `InfoCacheSettings`, `clear_info_cache`, `count_info_cache`, `get_info_cache_settings`, `get_info_cache_ttl_days`, `is_info_cache_enabled`, `is_info_cache_expired`, `set_info_cache_enabled`, `set_info_cache_ttl_days`, `NBERInfoCacheClearResult`. `InfoCacheLookupResult` and `get_paper_with_info_cache_result` are exposed from the `nber_cli.info_cache` module rather than the package top level; import them as `from nber_cli.info_cache import ...`.

### Changed

- `~/.nber-cli/config.json` now stores an `info` section: `info.cache_enabled` (default `true`) and `info.cache_ttl_days` (default `30`). Missing or malformed fields fall back to defaults.
- `info` now prints a one-line stderr hint when the paper was served from the local cache, pointing to `nber-cli info <id> --refresh` for a fresh fetch.

## 0.3.1 - 2026-06-03

### Added

- Added `nber-cli db init` and `nber-cli db migrate` for initializing and relocating the local database. These replace `feed init` and `feed migrate`.
- Added `info_cache` table so repeated `nber-cli info` and MCP `get_paper_info` calls return immediately from cache.
- Added `query_log`, `download_log`, and `info_log` tables for recording search keywords, download outcomes, and info lookups.
- Added `schema_version` field in `~/.nber-cli/config.json` for forward-compatible schema upgrades.

### Changed

- Renamed default database file from `feed.db` to `nber.db`. Existing `~/.nber-cli/feed.db` installations keep working without manual steps.
- Upgraded database schema from version 1 to version 2 with automatic upgrade on next invocation.
- Consolidated database code into `nber_cli.db`. Old `init_feed_database` and `migrate_feed_database` helpers remain as thin compatibility wrappers.

## 0.3.0 - 2026-06-03

### Added

- Added `nber-cli feed init` for creating a local SQLite feed cache.
- Added `nber-cli feed fetch` for fetching NBER's new working papers RSS feed and showing newly cached items.
- Added `nber-cli feed fetch --max-items` for limiting displayed feed output.
- Added `nber-cli feed migrate` for moving the feed cache database and updating user config.
- Added `nber-cli feed clean` for cleaning cached feed database records with confirmation.
- Added Python API documentation for feed cache helpers and feed data models.

### Changed

- Added user config documentation for `~/.nber-cli/config.json` and `feed.db-path`.
- Expanded English and Chinese feed cache documentation across CLI, getting started, configuration, and Python API pages.

## 0.2.0 - 2026-05-31

### Changed

- Reworked the CLI into `nber-cli download ...` subcommand syntax.
- Added `--file/-f` and `--save-base/-s` path handling behavior.
- Added `--batch/-b` multi-ID download mode.
- Removed database-backed download state tracking.
- Simplified the downloader to direct async HTTP PDF fetches.
- Updated documentation for the v0.2 command model.
- Removed the legacy web UI module and script entrypoint.

## 0.1.4 - 2025-08-09

### Added

- Added `--version` / `-v` flag to display current version.
- Added comprehensive help message with examples.
- Added `__main__.py` support for `python -m nber_cli`.
- Added argument grouping for better CLI organization.
- Added automatic help display when no arguments are provided.
