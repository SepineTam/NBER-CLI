# Claude Code

This page is written for an agent that needs to install NBER-CLI into Claude Code without guessing.

## What to Install

Use the NBER-CLI Claude Code plugin.

Repository:

```text
https://github.com/sepinetam/nber-cli
```

Marketplace name:

```text
nber-cli
```

Plugin name:

```text
nber-cli
```

MCP server name:

```text
nber-cli-mcp
```

The Claude Code marketplace file is:

```text
.claude-plugin/marketplace.json
```

The Claude Code plugin manifest is:

```text
plugins/nber-cli/.claude-plugin/plugin.json
```

The plugin includes:

- the `NBER-CLI` skill
- the `.mcp.json` MCP server configuration
- the `uvx nber-cli mcp-server` command used to start the MCP server

## Install from GitHub

Use this path when Claude Code can reach GitHub.

### In a Claude Code Session

Run these slash commands inside Claude Code:

```text
/plugin marketplace add sepinetam/nber-cli
/plugin install nber-cli@nber-cli
/reload-plugins
```

What each command means:

- `/plugin marketplace add sepinetam/nber-cli` adds this GitHub repository as a plugin marketplace.
- `/plugin install nber-cli@nber-cli` installs the `nber-cli` plugin from the `nber-cli` marketplace.
- `/reload-plugins` reloads plugins in the current session so the newly installed skill and MCP server are available without restarting Claude Code.

### From a Terminal

Run these commands in a normal shell:

```bash
claude plugin marketplace add sepinetam/nber-cli
claude plugin install nber-cli@nber-cli --scope user
```

Then open or return to Claude Code and run:

```text
/reload-plugins
```

Scope choices:

- `--scope user` installs for the current user across projects.
- `--scope project` installs for everyone using the current repository settings.
- `--scope local` installs only for the current user in the current repository.

Use `--scope user` unless the user explicitly asks for project-shared or local-only installation.

## Verify the Plugin

Inside Claude Code:

```text
/plugin
```

Then check:

- the `nber-cli` marketplace is present
- the `nber-cli` plugin is installed
- the plugin is enabled
- the plugin details show the `NBER-CLI` skill
- the plugin details show an MCP server named `nber-cli-mcp`

You can also inspect installed plugins from a terminal:

```bash
claude plugin list --json
claude plugin details nber-cli
```

## Verify the MCP Server

Inside Claude Code:

```text
/mcp
```

Check that `nber-cli-mcp` exists. If Claude Code asks whether to approve a project-scoped MCP server, approve it only after confirming that the command is:

```bash
uvx nber-cli mcp-server
```

From a terminal, you can also run:

```bash
claude mcp list
claude mcp get nber-cli-mcp
```

If the server fails to start, run:

```bash
uvx nber-cli --help
uvx nber-cli mcp-server
```

If `uvx nber-cli --help` fails, install `uv` first or fix PATH. If `uvx nber-cli mcp-server` fails, report the exact error.

## Verify NBER-CLI Behavior

Run direct CLI checks:

```bash
uvx nber-cli --help
uvx nber-cli info w25000 --format json
uvx nber-cli search "labor economics" --format json
```

Then ask Claude Code:

```text
Use NBER-CLI to show the abstract for NBER paper w25000.
```

Expected behavior:

- Claude Code should use the NBER-CLI skill or MCP server.
- It should not ask the user to clone the repository.
- It should not assume that `nber-cli` is already installed.
- It may use `uvx nber-cli ...`.

## If Plugin Installation Fails

Use this fallback only when the plugin path above is unavailable.

Add the MCP server manually:

```bash
claude mcp add nber-cli-mcp -- uvx nber-cli mcp-server
```

Then provide Claude Code with the skill content from:

```text
plugins/nber-cli/skills/NBER-CLI/SKILL.md
```

If the user does not have this repository checked out, tell them to read the skill from:

```text
https://github.com/sepinetam/nber-cli/blob/master/plugins/nber-cli/skills/NBER-CLI/SKILL.md
```

Manual MCP JSON equivalent:

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

## Common Mistakes

Use these exact values:

| Setting | Value |
| --- | --- |
| Repository | `https://github.com/sepinetam/nber-cli` |
| Marketplace | `nber-cli` |
| Plugin | `nber-cli` |
| MCP server | `nber-cli-mcp` |

Order matters: add the `sepinetam/nber-cli` marketplace before installing the plugin. Do not clone the repository just to run the CLI; use `uvx nber-cli ...`.

## Access Policy

NBER-CLI does not bypass NBER access controls. If NBER returns `403`, `404`, an access-denied page, or a download-limit response, report that result to the user. Do not rotate proxies, share credentials, bypass CAPTCHA, or disguise traffic.
