# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-05-27

### Changed
- Reworked the CLI into `nber-cli download ...` subcommand syntax.
- Added `--file/-f` and `--save-base/-s` path handling behavior.
- Added `--batch/-b` multi-ID download mode.
- Removed database-backed download state tracking.
- Simplified downloader to direct async HTTP PDF fetches.
- Updated documentation for the v0.2 command model.

## [0.1.4] - 2025-08-09

### Added
- Added `--version` / `-v` flag to display current version.
- Added comprehensive help message with examples.
- Added `__main__.py` file to support `python -m nber_cli` usage.
- Added argument grouping for better CLI organization.
- Added automatic help display when no arguments are provided.
