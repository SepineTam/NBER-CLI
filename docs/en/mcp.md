# MCP Server

NBER-CLI includes an MCP server so agents can search NBER, inspect paper metadata, and download PDFs without scraping command output.

## Start the Server

The default transport is stdio:

```bash
uvx nber-cli mcp-server
```

The installed command works the same way:

```bash
nber-cli mcp-server
```

## MCP Client Configuration

Use this configuration for MCP clients that launch stdio servers:

```json
{
  "mcpServers": {
    "nber-cli-mcp": {
      "command": "uvx",
      "args": ["nber-cli", "mcp-server"]
    }
  }
}
```

If `nber-cli` is already installed on the machine, the client can call it directly:

```json
{
  "mcpServers": {
    "nber-cli-mcp": {
      "command": "nber-cli",
      "args": ["mcp-server"]
    }
  }
}
```

## Streamable HTTP Transport

For clients that support streamable HTTP:

```bash
uvx nber-cli mcp-server --transport streamable_http --port 8000
```

`--port` only applies to `streamable_http`. The server binds to the local interface; treat the bound socket as a local-only service and front it with a reverse proxy (or SSH tunnel) if you need remote access. There is no built-in authentication: anyone who can reach the bound port can call all three tools and trigger PDF downloads on the host filesystem. Do not expose the port on a public network without putting it behind a trusted authenticating proxy.

When the client connects over HTTP, use the standard MCP client URL (the `--port` value):

```text
http://127.0.0.1:8000/mcp
```

Adjust the host and path according to the reverse proxy you front the server with.

## Available Tools

### get_paper_info

Fetch metadata and abstract for one NBER working paper.

Parameters:

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `paper_id` | `string` | Required | Paper ID such as `w25000` or `25000`. |
| `include_all` | `boolean` | `true` | Include related fields and published-version data when available. |

Returns a dictionary containing fields such as `id`, `title`, `authors`, `date`, `abstract`, and `url`.

### search_papers

Search NBER working papers.

Parameters:

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `query` | `string` | Required | Title, number, author, abstract phrase, or keyword. |
| `start_date` | `string` or `null` | `null` | Earliest working paper date in `YYYY-MM-DD` format. |
| `end_date` | `string` or `null` | `null` | Latest working paper date in `YYYY-MM-DD` format. |
| `page` | `integer` | `1` | Result page to fetch. |
| `per_page` | `integer` | `20` | Results per page. Supported values are `20`, `50`, and `100`. |

Returns search metadata and a list of papers.

### download_paper

Download one paper PDF.

Parameters:

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `paper_id` | `string` | Required | Paper ID string used verbatim to build the NBER PDF URL (`https://www.nber.org/papers/{paper_id}.pdf`) and, when `output_path` is omitted, the default output filename. NBER's canonical paper IDs include the `w` prefix, e.g. `w34567`. Pass `w34567` rather than `34567` so the request hits the NBER PDF endpoint and the default file name is `w34567.pdf`. |
| `output_path` | `string` or `null` | `null` | Explicit PDF output path. If omitted, the file is saved as `<paper_id>.pdf` in the server's current working directory. |

Returns `true` when the download succeeds. If the download fails, the underlying exception is returned to the MCP caller.

## Agent Usage Notes

- Prefer `search_papers` before `download_paper` when the paper ID is unknown.
- Use `get_paper_info` before downloading when a workflow needs title, author, or abstract confirmation.
- Pass an explicit `output_path` for downloads when the MCP client has a known workspace directory.
- NBER may restrict access to newly released papers during the first week; those downloads can return HTTP 403.

## Security Notes

The MCP server performs network requests to NBER and can write PDFs to disk through `download_paper`. Configure the server only in trusted clients and use explicit download paths when you need predictable file placement.

### Local Persistence and Caching

`get_paper_info` honors the same `info_cache` toggle and TTL as the CLI. When the cache is enabled, the tool reads from `info_cache` on a hit and writes a new row on a miss, mirroring the CLI behavior. Every call also appends a row to `info_log` so the local database records the lookup; the SQLModel/SQLAlchemy-backed local database is shared with the CLI at the path or `sqlite:///...` URL configured in `~/.nber-cli/config.json`. Tool responses do not flag whether the result came from the cache; if the caller needs that signal it must look at its own call history or use the CLI directly.

### Differences From the CLI

- `get_paper_info` does not accept a per-call `--refresh` argument. To force a fresh fetch, the caller can disable the cache, call `get_paper_info`, and re-enable the cache, or wait for the TTL to expire.
- `get_paper_info` does not write the one-line stderr cache hint that the CLI prints.
- The MCP `search_papers` and `download_paper` tools do not currently write to `query_log` or `download_log`; the CLI is the only surface that records those tables in this version.
- MCP tool return values are plain Python dictionaries; they do not wrap successes or failures in a `DownloadBatchResult`-style object. Failures are surfaced by raising the underlying exception to the MCP caller.

### Returned Object Shapes

The tool docstrings describe the public shape. In summary:

- `get_paper_info` returns the same `info(...)` dictionary as the CLI `--format json` path, plus `related(...)` fields when `include_all=True`. `published_version` is only present when truthy and `include_all=True`.
- `search_papers` returns the `search_results(...)` dictionary.
- `download_paper` returns the boolean `True` on success. On failure, the underlying `aiohttp` or network exception is raised to the caller.

### Download Path Rules

When `output_path` is omitted, the file is saved to `<cwd>/<paper_id>.pdf`, where `cwd` is the **server process** working directory. The server is typically launched by the MCP client (for example a Claude Code session), so the working directory is not the user's shell directory. Always pass `output_path` when the file must land in a known place. The download module writes the entire response body to disk in one call and overwrites any existing file at the target path. There is no atomic-rename guarantee; an interrupted write can leave a partial file at the target path.
