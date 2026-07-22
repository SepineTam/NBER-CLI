# Glossary

## NBER Paper ID

A working paper identifier such as `w25000`. Most user-facing commands accept the ID with or without the `w` prefix, but URLs and default PDF filenames use the canonical `w` prefix.

## CLI

The `nber-cli` command implemented in `src/nber_cli/cli.py`. It is optimized for humans and scripts: text output by default, JSON output where supported, and stable non-zero exits for failures.

## MCP Server

The agent-facing server implemented in `src/nber_cli/mcp/mcp.py` with FastMCP. It exposes three tools: `get_paper_info`, `search_papers`, and `download_paper`.

## Info Cache

The `info_cache` table and `info_cache.py` helper flow. It stores paper metadata so repeated `info` and `get_paper_info` calls can avoid another NBER page fetch while the row is within the configured TTL.

## Sliding TTL

The info cache refresh model. On a cache hit, NBER-CLI updates `last_fetched_at` and increments `fetch_count`, so expiration is measured from the latest local hit rather than only from the original network fetch.

## Feed System

The RSS workflow in `feed.py`. It reads `https://www.nber.org/rss/new.xml`, parses items with `defusedxml`, stores them in `feed_items`, and returns new or all items depending on the command options.

## Local Database

The SQLite database resolved by `db.get_database_path()`. By default it lives at `~/.nber-cli/nber.db`. It stores Feed and metadata caches, read state, behavior logs, and four Desktop tag tables.

## Config File

The JSON file at `~/.nber-cli/config.json`. It stores the configured database path, database schema version, info-cache and download settings, plus the Desktop refresh interval and detail font size.

## SQLModel

The typed ORM layer used by `db.py` on top of SQLAlchemy. Tables such as `FeedItem`, `InfoCache`, `QueryLog`, `DownloadLog`, and `InfoLog` are declared as SQLModel models.

## Behavior Logs

Local-only tables that record operational events:

- `query_log` records CLI search keywords and result counts.
- `download_log` records CLI download outcomes.
- `info_log` records CLI and MCP paper info lookups.

These logs are not sent to any project server.

## Soft Failure

A non-critical database write failure that should not break the main operation. For example, a failed `query_log` write should not prevent search results from being printed.

## Download Restriction

The current lexical working-directory check for download targets. CLI enables it by default and can disable it with `--restrict false`; MCP always enables it. In 0.10.0 it does not resolve `..` or symbolic links and is therefore not a security sandbox.

## `display_all`

A feed fetch option. When false, `feed fetch` displays only newly discovered RSS entries. When true, it displays all currently fetched RSS entries, including rows already present in the cache.

## `include_all`

An MCP `get_paper_info` option. When true, the returned dictionary includes related fields and `published_version` when NBER exposes them.

## `--refresh`

A CLI `info` flag that bypasses the local info cache for one call and fetches the paper page from NBER again. MCP does not currently expose an equivalent per-call flag.

## First-Week Restriction

NBER can return HTTP 403 for newly released papers that are not yet publicly downloadable. NBER-CLI reports this as a permission/access message rather than treating it as a missing paper.

## Future Schema

A database whose SQLite `PRAGMA user_version` is newer than the version supported by the installed NBER-CLI. The package rejects writes to this database to avoid downgrade corruption.
