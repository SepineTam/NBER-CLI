# Getting Started

This guide gets you from a fresh machine to searching, inspecting, and downloading NBER working papers.

## Requirements

- Python 3.11 or newer.
- Network access to `https://www.nber.org`.
- `uv`, `pipx`, or `pip` for installation.

The fastest path is `uvx`, which runs the package in an isolated environment without a permanent install.

## Run with uvx

```bash
uvx nber-cli --version
uvx nber-cli search "Labor Economic"
uvx nber-cli info w25000
uvx nber-cli download w34567
```

## Install as a Tool

Use `uv tool install` when you want the `nber-cli` command available on your shell path:

```bash
uv tool install nber-cli
nber-cli --version
```

You can also install with `pipx`:

```bash
pipx install nber-cli
nber-cli --version
```

## Run as a Python Module

The package also exposes a module entry point. This is useful when the `nber-cli` console script is not on your `PATH` (for example, when running from a checked-out working tree or inside a virtual environment where the wrapper was not generated):

```bash
python -m nber_cli --version
python -m nber_cli search "labor economics"
python -m nber_cli info w25000
```

`python -m nber_cli` is functionally identical to the `nber-cli` command — same arguments, same exit codes, same stdout/stderr contracts. From a working tree you can also run it through `uv`:

```bash
uv run python -m nber_cli --version
```

## First Search

```bash
nber-cli search "labor economics"
```

Search accepts title text, author names, abstracts, keywords, and paper numbers. The default result page contains 20 papers.

Add a date range and result size:

```bash
nber-cli search "minimum wage" --start-date 2024-01-01 --end-date 2024-12-31 --per-page 50
```

Return JSON for scripts:

```bash
nber-cli search "inflation" --format json
```

## Read Paper Details

```bash
nber-cli info w25000
```

Paper IDs can be passed with or without the `w` prefix:

```bash
nber-cli info 25000
```

Use `--all` to include related fields and published-version information when NBER exposes them:

```bash
nber-cli info w25000 --all
```

## Follow New Papers with the Feed Cache

Initialize the local database:

```bash
nber-cli db init
```

Fetch the NBER new working papers RSS feed:

```bash
nber-cli feed fetch
```

The first fetch stores the current RSS items in the cache and displays them as new. Later fetches show only items that were not already cached.

Limit output while showing the latest fetched items:

```bash
nber-cli feed fetch --max-items 5
```

Clean old cache records:

```bash
nber-cli feed clean --days 30
```

`feed clean` asks for confirmation before deleting cached records.

## Download a PDF

Download into the current directory:

```bash
nber-cli download w34567
```

Save into a directory:

```bash
nber-cli download w34567 --save-base ~/papers/nber
```

Save to an explicit file path:

```bash
nber-cli download w34567 --file ~/papers/nber/w34567.pdf
```

## Batch Download

```bash
nber-cli download --batch w34567 w25000 w32000 --save-base ~/papers/nber
```

Batch mode supports `--save-base`; it does not support `--file`.

## Next Steps

- Read the [CLI Reference](cli.md) for all commands and options.
- Configure the [MCP Server](mcp.md) for agent workflows.
- Use the [Python API](python-api.md) in your own async code.
