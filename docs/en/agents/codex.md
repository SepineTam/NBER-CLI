# Codex

This page is written for an agent that needs to install NBER-CLI into Codex without guessing.

## What to Install

Use the NBER-CLI Codex plugin.

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

The Codex marketplace file is:

```text
.agents/plugins/marketplace.json
```

The Codex plugin manifest is:

```text
plugins/nber-cli/.codex-plugin/plugin.json
```

The plugin includes:

- the `NBER-CLI` skill
- the `.mcp.json` MCP server configuration
- the `uvx nber-cli mcp-server` command used to start the MCP server

## Install from GitHub

Use this path when Codex can reach GitHub.

Run:

```bash
codex plugin marketplace add sepinetam/nber-cli
codex plugin add nber-cli@nber-cli
```

What each command means:

- `codex plugin marketplace add sepinetam/nber-cli` adds this GitHub repository as a Codex marketplace source.
- `codex plugin add nber-cli@nber-cli` installs the `nber-cli` plugin from the `nber-cli` marketplace.

If the repository was just updated and Codex already knows the marketplace, refresh it:

```bash
codex plugin marketplace upgrade
codex plugin add nber-cli@nber-cli
```

## Install from a Local Checkout

Use this path only when the user has already cloned the repository.

Run from anywhere:

```bash
codex plugin marketplace add /absolute/path/to/nber-cli
codex plugin add nber-cli@nber-cli
```

Replace `/absolute/path/to/nber-cli` with the real path to the repository root. The repository root is the directory that contains `.agents/plugins/marketplace.json`.

## Verify the Plugin

List marketplaces:

```bash
codex plugin marketplace list
```

List plugins:

```bash
codex plugin list
codex plugin list --marketplace nber-cli
```

Expected result:

- marketplace `nber-cli` is visible
- plugin `nber-cli` is visible
- plugin `nber-cli` is installed after `codex plugin add nber-cli@nber-cli`

If the plugin does not appear, the marketplace source is wrong or stale. Add the repository again or run:

```bash
codex plugin marketplace upgrade
```

## Verify the MCP Server

The installed plugin should provide an MCP server named:

```text
nber-cli-mcp
```

Check configured MCP servers:

```bash
codex mcp list
codex mcp list --json
```

If you need details for the server:

```bash
codex mcp get nber-cli-mcp
codex mcp get nber-cli-mcp --json
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

Then ask Codex:

```text
Use NBER-CLI to show the abstract for NBER paper w25000.
```

Expected behavior:

- Codex should use the NBER-CLI skill or MCP server.
- It should not ask the user to clone the repository.
- It should not assume that `nber-cli` is already installed.
- It may use `uvx nber-cli ...`.

## If Plugin Installation Fails

Use this fallback only when the plugin path above is unavailable.

Add the MCP server manually:

```bash
codex mcp add nber-cli-mcp -- uvx nber-cli mcp-server
```

Then provide Codex with the skill content from:

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

Order matters: add the `sepinetam/nber-cli` marketplace before installing the plugin. If using a local checkout, use the repository root as the marketplace source; it is the directory containing `.agents/plugins/marketplace.json`. Do not clone the repository just to run the CLI; use `uvx nber-cli ...`.

## Access Policy

NBER-CLI does not bypass NBER access controls. If NBER returns `403`, `404`, an access-denied page, or a download-limit response, report that result to the user. Do not rotate proxies, share credentials, bypass CAPTCHA, or disguise traffic.
