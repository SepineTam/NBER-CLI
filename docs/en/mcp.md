# MCP Server

NBER-CLI includes an MCP server so agents can search NBER, inspect paper metadata, and download PDFs without scraping command output.

For how the MCP server shares core modules with the CLI, see [System Architecture](architecture.md).

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

## HTTP Transports

For clients that support streamable HTTP:

```bash
uvx nber-cli mcp-server --transport streamable-http --port 8000
```

`--port` only applies to HTTP transports. When set to a non-default value, pass `--yes` to confirm:

```bash
uvx nber-cli mcp-server --transport streamable-http --port 9000 --yes
```

The server binds to the local interface; treat the bound socket as a local-only service and front it with a reverse proxy (or SSH tunnel) if you need remote access. There is no built-in authentication: anyone who can reach the bound port can call all three tools and trigger PDF downloads on the host filesystem. Do not expose the port on a public network without putting it behind a trusted authenticating proxy.

When the client connects over HTTP, use the standard MCP client URL (the `--port` value):

```text
http://127.0.0.1:8000/mcp
```

For the legacy SSE transport, start the server with `--transport sse` and connect to:

```text
http://127.0.0.1:8000/sse
```

The endpoint path depends on the selected transport: streamable HTTP uses `/mcp`, while SSE uses `/sse`. Adjust the host and path according to the reverse proxy you front the server with.

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
| `paper_id` | `string` | Required | Paper ID such as `w34567` or `34567`. The tool normalizes both forms to `w34567`. |
| `output_path` | `string` or `null` | `null` | Explicit PDF output path. It must resolve inside the server process's current working directory. If omitted, the normalized file name, such as `w34567.pdf`, is saved in that directory. |

Returns `{"success": true}` when the download succeeds. Validation, path, network, and filesystem failures are returned as `{"error": "..."}` rather than raised to the MCP caller. Callers must inspect which key is present.

## Agent Usage Notes

- Prefer `search_papers` before `download_paper` when the paper ID is unknown.
- Use `get_paper_info` before downloading when a workflow needs title, author, or abstract confirmation.
- Pass an explicit `output_path` for downloads when the MCP client has a known path inside the server process's working directory.
- NBER may restrict access to newly released papers during the first week; those downloads can return HTTP 403.

## Security Notes

The MCP server performs network requests to NBER and can write PDFs to disk through `download_paper`. Configure the server only in trusted clients and use explicit download paths when you need predictable file placement.

### Local Persistence and Caching

`get_paper_info` honors the same `info_cache` toggle and TTL as the CLI. When the cache is enabled, the tool reads from `info_cache` on a hit and writes a new row on a miss, mirroring the CLI behavior. Every call also appends a row to `info_log` so the local database records the lookup; the SQLModel/SQLAlchemy-backed local database is shared with the CLI at the path or `sqlite:///...` URL configured in `~/.nber-cli/config.json`. Tool responses do not flag whether the result came from the cache; if the caller needs that signal it must look at its own call history or use the CLI directly.

### Differences From the CLI

- `get_paper_info` does not accept a per-call `--refresh` argument. To force a fresh fetch, the caller can disable the cache, call `get_paper_info`, and re-enable the cache, or wait for the TTL to expire.
- Neither `get_paper_info` nor the CLI prints a cache-hit hint to stderr.
- The MCP `search_papers` and `download_paper` tools do not currently write to `query_log` or `download_log`; the CLI is the only surface that records those tables in this version.
- MCP tool return values are plain Python dictionaries; they do not use `DownloadBatchResult`. Tool failures are represented by an `error` key instead of being raised to the MCP caller.

### Returned Object Shapes

The tool docstrings describe the public shape. In summary:

- `get_paper_info` returns the same `info(...)` dictionary as the CLI `--format json` path, plus `related(...)` fields when `include_all=True`. `published_version` is only present when truthy and `include_all=True`.
- `search_papers` returns the `search_results(...)` dictionary.
- `download_paper` returns `{"success": True}` on success and `{"error": "..."}` on failure.

### Download Path Rules

When `output_path` is omitted, the file is saved to `<cwd>/<normalized-paper-id>.pdf`, where `cwd` is the **server process** working directory. The server is typically launched by the MCP client, so this directory may differ from the user's interactive shell directory. An explicit path is accepted only when it resolves inside that same working directory; attempts to escape it return an `error` dictionary. The download module writes the entire response body to disk in one call and overwrites any existing file at the target path. There is no atomic-rename guarantee; an interrupted write can leave a partial file at the target path.
