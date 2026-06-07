# Other Agents

For agents that do not have a dedicated NBER-CLI plugin, use MCP plus the NBER-CLI skill.

## Preferred Setup

Add this MCP server:

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

Then load or paste the skill from:

```text
plugins/nber-cli/skills/NBER-CLI/SKILL.md
```

## If MCP Is Not Supported

Use direct commands:

```bash
uvx nber-cli search "labor economics"
uvx nber-cli info w25000 --format json
uvx nber-cli download w34567 --save-base ./papers
```

Use JSON output when another program or agent needs to consume the result.

## Access Limits

Do not bypass NBER restrictions. Surface 403, 404, timeout, access-denied, and download-limit responses clearly to the user.

