# Changelog

All notable changes to this project will be documented in this file.

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
