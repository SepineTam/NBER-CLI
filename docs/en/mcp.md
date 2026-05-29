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
    "nber-cli": {
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
    "nber-cli": {
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
| `paper_id` | `string` | Required | Paper ID such as `w34567` or `34567`. |
| `output_path` | `string` or `null` | `null` | Explicit PDF output path. If omitted, the file is saved as `<paper_id>.pdf` in the server's current working directory. |

Returns `true` when the download succeeds. If the download fails, the underlying exception is returned to the MCP caller.

## Agent Usage Notes

- Prefer `search_papers` before `download_paper` when the paper ID is unknown.
- Use `get_paper_info` before downloading when a workflow needs title, author, or abstract confirmation.
- Pass an explicit `output_path` for downloads when the MCP client has a known workspace directory.
- NBER may restrict access to newly released papers during the first week; those downloads can return HTTP 403.

## Security Notes

The MCP server performs network requests to NBER and can write PDFs to disk through `download_paper`. Configure the server only in trusted clients and use explicit download paths when you need predictable file placement.
