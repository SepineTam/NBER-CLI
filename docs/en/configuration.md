# Configuration

Most NBER-CLI runtime behavior uses built-in defaults. The local database also uses a small user config file to remember the SQLite database path selected by `nber-cli db init` or `nber-cli db migrate`.

## Runtime Defaults

| Setting | Default | Description |
| --- | --- | --- |
| Request timeout | `60` seconds | Total timeout for network requests. |
| Retry count | `3` | Failed eligible requests are retried before surfacing the error. |
| Request attempts | `4` | Derived from retry count plus the first attempt. |
| Download connection limit | `100` | Maximum concurrent download connections. |
| Per-host connection limit | `10` | Maximum concurrent connections to one host. |
| Search page sizes | `20`, `50`, `100` | Accepted values for `--per-page`. |

These values live in `NBERCLIConfig` and `NBER_CLI_CONFIG`.

## User Config File

The user config file is:

```text
~/.nber-cli/config.json
```

Current schema:

```json
{
  "schema_version": 2,
  "feed": {
    "db-path": "/Users/name/.nber-cli/nber.db"
  }
}
```

`feed.db-path` points to the SQLite database used by `info`, `search`, `download`, and `feed`. The historical `feed` key name is preserved for backward compatibility; the database itself is general-purpose.

`schema_version` records the current database schema version. NBER-CLI updates it after `db init` or schema upgrades.

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

Move an existing database and update the config:

```bash
nber-cli db migrate ~/data/nber.db
```

If you upgraded from 0.3.0 and still have `~/.nber-cli/feed.db`, NBER-CLI will keep using that legacy file when no `nber.db` is present. The schema is upgraded automatically on first invocation.

The database holds:

- `feed_items` and `feed_fetches`: RSS cache used by `feed fetch` and `feed clean`.
- `info_cache`: paper metadata cache used by `info` and the MCP `get_paper_info` tool.
- `query_log`, `download_log`, `info_log`: behavior logs for search keywords, download outcomes, and info lookups.

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
nber-cli download w34567 --save-base ~/papers/nber
```

Creates:

```text
~/papers/nber/w34567.pdf
```

Explicit file download:

```bash
nber-cli download w34567 --file ~/papers/custom-name.pdf
```

Creates exactly the requested path, including parent directories when possible.

## Date Filtering

Search dates use `YYYY-MM-DD`.

```bash
nber-cli search "trade" --start-date 2024-01-01 --end-date 2024-12-31
```

If `--start-date` is provided without `--end-date`, NBER-CLI uses the current date as the end date.

## Network Behavior

NBER-CLI sends a browser-like user agent, uses retries for transient failures, and raises readable errors for common download failures:

- HTTP 403 can mean a newly released paper is still under NBER's first-week access restriction.
- HTTP 404 means the paper PDF was not found.
- Timeout and connection failures are reported as network errors.

## No Credentials Required

NBER-CLI does not require an API key. It works against public NBER web pages and NBER's public working paper search endpoint.
