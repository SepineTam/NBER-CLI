# Agent Guides

This section is for agents that need to install or configure NBER-CLI for their own runtime.

## Choose a Path

Use the first path your runtime supports:

| Runtime | Preferred path | Fallback |
| --- | --- | --- |
| Claude Code | Install the NBER-CLI plugin | MCP server plus skill |
| Codex | Install the NBER-CLI plugin | MCP server plus skill |
| OpenClaw | MCP server plus skill | Direct `uvx nber-cli ...` commands |
| Other agents | MCP server plus skill | Direct `uvx nber-cli ...` commands |

## Shared MCP Config

Agents that support MCP can run NBER-CLI without a checked-out repository:

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

## Shared Skill

Agents that support skills should load the NBER-CLI skill from:

```text
plugins/nber-cli/skills/NBER-CLI/SKILL.md
```

The skill tells the agent when to use NBER-CLI, how to run `uvx nber-cli ...`, how to configure MCP, and how to interpret access errors.

## Safety Rule

NBER-CLI does not bypass NBER access controls. If NBER denies a request, returns a limit page, or blocks a PDF download, treat that response as authoritative.

