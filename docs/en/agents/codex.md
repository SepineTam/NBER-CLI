# Codex

This page shows the currently supported way to connect NBER-CLI to Codex.

## Prerequisites

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) and make sure both commands are available:

```bash
uvx --version
codex --version
```

You do not need to clone this repository or install NBER-CLI globally. `uvx` downloads and runs the published package in an isolated environment.

## Add the MCP Server

Register NBER-CLI as a local stdio MCP server:

```bash
codex mcp add nber-cli-mcp -- uvx nber-cli mcp-server
```

This configuration starts `uvx nber-cli mcp-server` when Codex needs the server. It does not start the optional HTTP API, so the `server` extra is not required.

## Verify the Setup

Confirm that the server is registered:

```bash
codex mcp list
codex mcp get nber-cli-mcp
```

Check the underlying CLI separately:

```bash
uvx nber-cli --help
uvx nber-cli info w25000 --format json
uvx nber-cli search "labor economics" --format json
```

Then ask Codex:

```text
Use NBER-CLI to show the abstract for NBER paper w25000.
```

If startup fails, run `uvx nber-cli mcp-server` directly and report its exact error. If `uvx` is not found, install `uv` or fix `PATH`.

## Optional Skill Instructions

The repository also contains reusable instructions at:

```text
plugins/nber-cli/skills/NBER-CLI/SKILL.md
```

Without a local checkout, read the tracked file on GitHub:

```text
https://github.com/sepinetam/nber-cli/blob/master/plugins/nber-cli/skills/NBER-CLI/SKILL.md
```

The MCP server works without copying this skill file; the skill only gives Codex additional workflow guidance.

## Plugin Availability

The repository tracks a Codex plugin manifest at:

```text
plugins/nber-cli/.codex-plugin/plugin.json
```

However, the current release does not track the `.agents/plugins/marketplace.json` catalog required to use the repository as a Codex marketplace. Therefore, do not use these commands with the current release:

```bash
codex plugin marketplace add sepinetam/nber-cli
codex plugin add nber-cli@nber-cli
```

Use the MCP setup above until a marketplace catalog is included in a future release.

## Remove the Integration

```bash
codex mcp remove nber-cli-mcp
```

## Access Policy

NBER-CLI does not bypass NBER access controls. If NBER returns `403`, `404`, an access-denied page, or a download-limit response, report that result to the user. Do not rotate proxies, share credentials, bypass CAPTCHA, or disguise traffic.
