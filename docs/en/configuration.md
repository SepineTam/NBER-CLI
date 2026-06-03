# Configuration

Most NBER-CLI runtime behavior uses built-in defaults. The feed cache also uses a small user config file to remember the SQLite database path selected by `nber-cli feed init` or `nber-cli feed migrate`.

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

At the moment, the config file is used for feed cache settings:

```json
{
  "feed": {
    "db-path": "/Users/name/.nber-cli/feed.db"
  }
}
```

`feed.db-path` points to the SQLite database used by `nber-cli feed fetch` and `nber-cli feed clean`.

## Feed Cache Database

Default feed cache database path:

```text
~/.nber-cli/feed.db
```

Initialize the default cache:

```bash
nber-cli feed init
```

Initialize a cache at a custom path:

```bash
nber-cli feed init --db-path ~/data/nber-feed.db
```

Move an existing cache and update the config:

```bash
nber-cli feed migrate ~/data/nber-feed.db
```

The feed cache stores RSS items that have already been seen. `feed fetch` uses this cache to decide which items are new. `feed clean` deletes records from this local cache; if deleted records still appear in the RSS feed, they may be fetched again as new items.

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
