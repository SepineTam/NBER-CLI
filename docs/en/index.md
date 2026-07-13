# NBER-CLI

NBER-CLI is a command-line toolkit for searching NBER working papers, reading paper metadata, downloading PDFs, and exposing those workflows to AI agents through MCP.

## What It Does

NBER-CLI focuses on the common research loop around NBER working papers:

- Search for papers by keyword, author, title, abstract, or paper number.
- Inspect a paper's title, authors, date, abstract, URL, and related metadata.
- Follow new working papers through NBER's RSS feed and a local cache.
- Download a PDF by paper ID.
- Run batch downloads into a target directory.
- Serve paper search, lookup, and download operations as MCP tools.

## Quick Start

Run without installing:

```bash
uvx nber-cli search "Labor Economic"
uvx nber-cli info w25000
uvx nber-cli feed fetch --max-items 5
uvx nber-cli download w34567
```

If the command is not found or fails, run `uvx nber-cli -v` to check the current version. If it is not the latest version, update the cache with:

```bash
uvx --refresh nber-cli -v
```

Install as a reusable command:

```bash
uv tool install nber-cli
nber-cli search "Labor Economic"
nber-cli info w25000
nber-cli feed fetch --max-items 5
nber-cli download w34567
```

## MCP in One Minute

Start the stdio MCP server:

```bash
uvx nber-cli mcp-server
```

Add it to an MCP client:

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

## Documentation Map

- [Getting Started](getting-started.md): install options and first commands.
- [Agent Guides](agents/index.md): plugin, MCP, and skill setup for Claude Code, Codex, OpenClaw, and other agents.
- [CLI Reference](cli.md): command syntax, options, output formats, and examples.
- [MCP Server](mcp.md): agent configuration, transports, and available tools.
- [Python API](python-api.md): async functions and data models.
- [Configuration](configuration.md): runtime defaults and operational behavior.
- [Persistence Layer](persistence.md): local SQLite schema, cache behavior, logs, migration, and cleanup limits.
- [System Architecture](architecture.md): how the CLI, MCP server, network layer, download engine, feed system, and persistence layer fit together.
- [Glossary](glossary.md): project-specific terms, table names, error models, and paper ID conventions.
- [Development](development.md): local setup, tests, docs, CI, and release workflow.
- [Test Infrastructure](testing.md): fixtures, mocking strategy, async tests, and robustness coverage.
- [Contributing](contributing.md): contribution standards and review expectations.
- [Changelog](changelog.md): notable project changes.

## Project Status

The current public command model is `nber-cli` v0.8.0. The CLI is intentionally small and script-friendly: text output is optimized for human reading, and `--format json` is available where structured output matters.
