# Changelog

All notable changes to this project will be documented here.

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

## 0.2.0 - 2026-05-27

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
