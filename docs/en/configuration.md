# Configuration

NBER-CLI currently uses built-in runtime defaults rather than a user configuration file. The defaults are intentionally conservative and work for both CLI and MCP usage.

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
