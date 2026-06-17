# Use of MCP Server

NBER-CLI can expose its commands through the Model Context Protocol (MCP). This lets MCP clients call `search`, `info`, `download`, and `feed` as tools without shelling out to `uvx` manually.

## Run the stdio server

```bash
uvx nber-cli mcp-server
```

This is the default transport. Most MCP clients expect stdio and read the server's tools from this command.

## Run the HTTP server

```bash
uv run nber-cli mcp-server --transport streamable-http --port 8000 --yes
```

The HTTP transport has no built-in authentication. Do not expose it to an untrusted network. `--port` exists in published `0.4.0`; the source tree additionally requires `--yes` for a custom port.

## Example MCP client configuration

For clients that read a `mcpServers` block:

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

## Using the exposed tools

Once connected, clients can call tools such as:

- `nber_search`: keyword search with optional date range.
- `nber_info`: metadata lookup by paper ID.
- `nber_download`: PDF download to a configured base path.
- `nber_feed_fetch`: incremental RSS feed fetch.

## Security notes

- The download tool writes files to the filesystem. Configure `--save-base` or sandbox the server if the client is untrusted.
- The HTTP transport should bind to `localhost` only unless you have placed it behind authenticated reverse proxy.
- Do not configure the server to bypass NBER access controls.
