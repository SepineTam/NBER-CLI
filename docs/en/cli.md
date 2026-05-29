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

`info` and `search` default to `list`, a readable text format. Use `--format json` when piping output into scripts or agent workflows.
