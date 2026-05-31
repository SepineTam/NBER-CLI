# OpenClaw

Use MCP plus the NBER-CLI skill for OpenClaw unless a dedicated plugin integration is available in your runtime.

## MCP Server

Add the NBER-CLI MCP server to OpenClaw's MCP configuration:

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

This runs the published `nber-cli` package with `uvx`, so a checked-out copy of this repository is not required.

## Skill

If OpenClaw supports skill or instruction imports, load:

```text
plugins/nber-cli/skills/nber-cli/SKILL.md
```

The skill gives the agent the usage policy, command examples, JSON output guidance, and common error interpretation.

## Verify

Ask OpenClaw to run:

```bash
uvx nber-cli info w25000 --format json
```

If the command works but a PDF download fails, report the HTTP status or NBER response instead of retrying with access-circumvention behavior.

