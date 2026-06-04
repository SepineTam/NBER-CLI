# CLI Reference

The executable command is `nber-cli`.

```bash
nber-cli [--version] <command> [options]
```

## Global Options

| Option | Description |
| --- | --- |
| `-v`, `--version` | Print the installed NBER-CLI version. |
| `-h`, `--help` | Show command help. |

Running `nber-cli` without a subcommand prints the top-level help and exits successfully.

## Commands

| Command | Purpose |
| --- | --- |
| `download` | Download one or more paper PDFs. |
| `info` | Show metadata and abstract for one paper. |
| `search` | Search NBER working papers. |
| `db` | Manage the local SQLite database. |
| `feed` | Manage the NBER new working papers RSS feed cache. |
| `mcp-server` | Start the MCP server for agents. |

## download

Download one paper:

```bash
nber-cli download w34567
```

Download to an explicit file:

```bash
nber-cli download w34567 --file ~/papers/w34567.pdf
nber-cli download w34567 -f ~/papers/w34567.pdf
```

Download to a target directory:

```bash
nber-cli download w34567 --save-base ~/papers/nber
nber-cli download w34567 -s ~/papers/nber
```

Batch download:

```bash
nber-cli download --batch w34567 w25000 w32000 --save-base ~/papers/nber
nber-cli download -b w34567 w25000 w32000 -s ~/papers/nber
```

### download Options

| Option | Description |
| --- | --- |
| `paper_id` | Optional positional paper ID for single downloads, for example `w34567`. |
| `--file`, `-f` | Explicit target PDF path for a single download. |
| `--save-base`, `-s` | Target directory for generated `<paper_id>.pdf` files. Defaults to the current working directory. |
| `--batch`, `-b` | One or more paper IDs to download concurrently. |

### download Rules

- A single positional paper ID and `--batch` cannot be used together.
- `--file` is only supported for a single paper.
- Batch mode supports `--save-base` only.
- If neither `--file` nor `--save-base` is passed, PDFs are saved in the current working directory.
- If a paper is unavailable, NBER-CLI exits with code `1` and prints a readable error message.

## info

Show paper metadata:

```bash
nber-cli info w25000
```

Show all available fields:

```bash
nber-cli info w25000 --all
```

Return JSON:

```bash
nber-cli info w25000 --format json
nber-cli info w25000 -f json
```

### info Options

| Option | Description |
| --- | --- |
| `paper_id` | Required paper ID, with or without the `w` prefix. |
| `--all`, `-a` | Include related fields and published-version information when available. |
| `--format`, `-f` | Output format: `list` or `json`. Defaults to `list`. |
| `--refresh` | Bypass the local `info_cache` and re-fetch from NBER. The new data is written back to the cache when the cache is enabled. |

When the cache is enabled and the cached entry has not yet passed the configured TTL, repeated `info` calls are served from the local database. The first `info` call after a TTL expiry, or any call with `--refresh`, performs a live fetch.

The MCP `get_paper_info` tool follows the same cache behavior, including the `--refresh` flag.

## info cache

Manage the `info_cache` lookup behavior and clear cached records.

Show the current cache state, TTL, and row count:

```bash
nber-cli info cache
```

Toggle the cache globally:

```bash
nber-cli info cache --turn-on
nber-cli info cache --turn-off
```

Set the cache refresh interval in days:

```bash
nber-cli info cache --set-refresh 7
nber-cli info cache --set-refresh 30
```

`--set-refresh` requires a positive integer. The new value is written to `~/.nber-cli/config.json` and used as the TTL for every subsequent `info` call.

Clean cached records not refreshed in the last 30 days:

```bash
nber-cli info cache clear
nber-cli info cache clear --days 30
```

Clean all cached records:

```bash
nber-cli info cache clear --all
nber-cli info cache clean
```

`info cache clean` is a convenience alias for `info cache clear --all`.

Clean cached records by `last_fetched_at` date:

```bash
nber-cli info cache clear --end-date 2026-06-01
nber-cli info cache clear --start-date 2026-05-01 --end-date 2026-06-01
```

`--end-date` without `--start-date` cleans from the earliest cached record through the end date. `--start-date` and `--end-date` are inclusive. Passing only `--start-date` is invalid.

Before deleting anything, `info cache clear` prints how many cached records match and asks for confirmation:

```text
This operation is irreversible.
Deleted info cache records may be fetched again from NBER.
Continue? [y/N]:
```

Only `y` or `Y` continues. Any other response aborts without deleting records.

### info cache Options

| Subcommand | Option | Description |
| --- | --- | --- |
| (none) | `--turn-on` | Enable the info cache globally. |
| (none) | `--turn-off` | Disable the info cache globally. |
| (none) | `--set-refresh` | Set the info cache refresh interval in days. Must be a positive integer. |
| `clear` | `--days` | Clean cached records not refreshed for this many days. Defaults to `30`. |
| `clear` | `--all` | Clean all cached records. |
| `clear` | `--start-date` | Clean cached records refreshed on or after this date, formatted `YYYY-MM-DD`. |
| `clear` | `--end-date` | Clean cached records refreshed on or before this date, formatted `YYYY-MM-DD`. |
| `clean` | — | Alias for `clear --all`. |

## search

Search by query:

```bash
nber-cli search "Labor Economic"
```

Use date filters:

```bash
nber-cli search "minimum wage" --start-date 2024-01-01 --end-date 2024-12-31
```

Change pagination:

```bash
nber-cli search "inflation" --page 2 --per-page 50
```

Return JSON:

```bash
nber-cli search "inflation" --format json
nber-cli search "inflation" -f json
```

### search Options

| Option | Description |
| --- | --- |
| `query` | Required search query. It may be a title, number, author, abstract phrase, or keyword. |
| `--start-date`, `--start` | Include papers on or after this date, formatted `YYYY-MM-DD`. |
| `--end-date`, `--end` | Include papers on or before this date, formatted `YYYY-MM-DD`. |
| `--page` | Result page to fetch. Defaults to `1`. |
| `--per-page` | Results per page. Allowed values: `20`, `50`, `100`. Defaults to `20`. |
| `--format`, `-f` | Output format: `list` or `json`. Defaults to `list`. |

When only `--start-date` is provided, NBER-CLI automatically uses the current date as the end date.

## feed

`feed` works with NBER's new working papers RSS feed and the local SQLite database. The database tracks which RSS items have already been seen, so `feed fetch` can show only newly discovered papers by default.

### feed fetch

Fetch the RSS feed, store all fetched items in the cache, and display only new items by default:

```bash
nber-cli feed fetch
```

Display all fetched RSS items, including items already present in the cache:

```bash
nber-cli feed fetch --display-all true
nber-cli feed fetch --display-all
```

Limit displayed output:

```bash
nber-cli feed fetch --max-items 5
```

When `--max-items` is provided and `--display-all` is omitted, `--display-all` defaults to `true`. This makes `nber-cli feed fetch --max-items 5` show the first five fetched RSS items instead of showing nothing when there are no new items.

Return JSON:

```bash
nber-cli feed fetch --format json
nber-cli feed fetch -f json
```

### feed clean

Clean cached feed database records. This deletes records from the local cache, not from NBER. Deleted cache records may be fetched again as new items if they still appear in the RSS feed.

Clean records not seen for 30 days:

```bash
nber-cli feed clean
nber-cli feed clean --days 30
```

Clean all cached records:

```bash
nber-cli feed clean --all
```

Clean records by last-seen date:

```bash
nber-cli feed clean --end-date 2026-05-31
nber-cli feed clean --start-date 2026-05-01 --end-date 2026-05-31
```

`--end-date` without `--start-date` cleans from the earliest cached record through the end date. `--start-date` and `--end-date` are inclusive. Passing only `--start-date` is invalid.

Before deleting anything, `feed clean` prints how many cached records match and asks for confirmation:

```text
This operation is irreversible.
Deleted cache records may be fetched again as new items if they still appear in the RSS feed.
Continue? [y/N]:
```

Only `y` or `Y` continues. Any other response aborts without deleting records.

### feed Options

| Subcommand | Option | Description |
| --- | --- | --- |
| `fetch` | `--display-all [true|false]` | Display all fetched RSS items instead of only new items. |
| `fetch` | `--format`, `-f` | Output format: `list` or `json`. Defaults to `list`. |
| `fetch` | `--max-items` | Maximum number of feed items to display. |
| `clean` | `--days` | Clean cached records not seen for this many days. Defaults to `30`. |
| `clean` | `--all` | Clean all cached feed records. |
| `clean` | `--start-date` | Clean cached records last seen on or after this date, formatted `YYYY-MM-DD`. |
| `clean` | `--end-date` | Clean cached records last seen on or before this date, formatted `YYYY-MM-DD`. |

## db

`db` manages the local SQLite database used by `info`, `search`, `download`, and `feed` for cache and behavior logs.

### db init

Initialize the database and write its path to the user config:

```bash
nber-cli db init
nber-cli db init --db-path ~/.nber-cli/nber.db
```

If `--db-path` is omitted, the default database path is `~/.nber-cli/nber.db`.

If an existing `~/.nber-cli/feed.db` from 0.3.0 is present and no `nber.db` exists yet, NBER-CLI uses that legacy file in place. Schema is automatically upgraded from version 1 to version 2 on first use.

### db migrate

Move the database to a new path and update the user config:

```bash
nber-cli db migrate ~/data/nber.db
```

Migration moves the SQLite database file and any SQLite sidecar files such as `-wal`, `-shm`, and `-journal`. The target path must not already exist.

### db Options

| Subcommand | Option | Description |
| --- | --- | --- |
| `init` | `--db-path` | SQLite database path. Defaults to `~/.nber-cli/nber.db`. |
| `migrate` | `new_db_path` | New SQLite database path. |

## mcp-server

Start the default stdio MCP server:

```bash
nber-cli mcp-server
```

Start an HTTP transport:

```bash
nber-cli mcp-server --transport streamable_http --port 8000
```

### mcp-server Options

| Option | Description |
| --- | --- |
| `--transport` | Transport mechanism: `stdio` or `streamable_http`. Defaults to `stdio`. |
| `--port` | Port for `streamable_http`. Defaults to `8000`. |

For client configuration and tool details, see [MCP Server](mcp.md).

## Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | Command completed successfully, or help was printed. |
| `1` | Runtime failure such as a failed download. |
| `2` | Invalid command-line arguments. |

## Output Formats

`info`, `search`, and `feed fetch` default to `list`, a readable text format. Use `--format json` when piping output into scripts or agent workflows.
