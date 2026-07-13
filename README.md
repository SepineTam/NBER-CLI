# NBER-CLI
A command line interface for reaching the National Bureau of Economic Research (NBER) paper without brower.

[![Pytest](https://github.com/sepinetam/nber-cli/actions/workflows/pytest.yml/badge.svg)](https://github.com/sepinetam/nber-cli/actions/workflows/pytest.yml)
[![Lint](https://github.com/sepinetam/nber-cli/actions/workflows/lint.yml/badge.svg)](https://github.com/sepinetam/nber-cli/actions/workflows/lint.yml)
[![Docs](https://github.com/sepinetam/nber-cli/actions/workflows/docs.yml/badge.svg)](https://github.com/sepinetam/nber-cli/actions/workflows/docs.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/nber-cli.svg)](https://pypi.org/project/nber-cli/)
[![PyPI Downloads](https://static.pepy.tech/badge/nber-cli)](https://pepy.tech/projects/nber-cli)

[简体中文](README.zh-CN.md) | [Documentation](docs/en/index.md)

> **NBER** is a registered trademark of the [National Bureau of Economic Research](https://www.nber.org). This project is an independent open-source tool and is **not affiliated with, endorsed by, or sponsored by** the National Bureau of Economic Research. By using this project, you agree to the [Usage Policy](docs/en/policy.md).

## Features

- Search NBER working papers by title, paper number, author, abstract, or keyword.
- Fetch structured metadata and abstracts for a paper ID such as `w25000`.
- Download single papers or batches as PDF files.
- Track newly released NBER working papers through a local RSS feed cache (`nber-cli feed fetch` / `feed clean`).
- Cache paper metadata locally (`nber-cli info` writes to `info_cache`) with a sliding TTL, plus a behavior log for `search`, `download`, and `info` lookups.
- Store the cache, RSS items, and behavior logs in a local SQLite database at `~/.nber-cli/nber.db`, managed through SQLModel/SQLAlchemy and configurable with a filesystem path or `sqlite:///...` URL.
- Expose the same core workflows as MCP tools for AI agents.
- Provide an optional loopback-only HTTP server for the Desktop app and local integrations.
- Provide a macOS and Windows Desktop research workspace with feed sync, unread tracking, paper details, and citation copying.
- Return human-readable output by default, with JSON output for automation.
- Provide `--verbose` debug logging and a rotating log file for troubleshooting.
- Use `-c/--config <path>` to temporarily override the config file for a single run.

See [Configuration](docs/en/configuration.md) for the full list of configurable values and the local database layout, and [Usage Policy](docs/en/policy.md) for what NBER-CLI writes to disk by default.

## Quick Start

### Use in Agents

NBER-CLI can be used by agents through plugins, the MCP server, and the skill. Claude Code and Codex should install the NBER-CLI plugin first; OpenClaw and other agents should use the MCP server plus the skill.

If you want an agent to install and check NBER-CLI automatically, send it this prompt:

```text
Install NBER-CLI globally for yourself from https://github.com/sepinetam/nber-cli, and check the status.
```

After installation, verify it with either prompt:

```text
I remember that in 2025, Anton had a paper on NBER about Agent for Econ. Download it to the current directory.
```

```text
I remember that paper w25000 was interesting. Show me its abstract.
```

If you are an agent, visit the [Agent Guides](docs/en/agents/index.md).

### CLI Mode
Run commands directly with `uvx`:

```bash
uvx nber-cli search "Labor Economic"
uvx nber-cli info w25000
uvx nber-cli download w34567
```

If the command is not found or fails, run `uvx nber-cli -v` to check the current version. If it is not the latest version, update the cache with:

```bash
uvx --refresh nber-cli -v
```

Or install the command first:

```bash
uv tool install nber-cli
nber-cli search "Labor Economic"
nber-cli info w25000
nber-cli download w34567
```

### MCP Server Mode

NBER-CLI can run as a stdio MCP server:

```bash
uvx nber-cli mcp-server
```

Example MCP client configuration:

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

The MCP server exposes tools for paper lookup, search, and PDF download.

### Local HTTP Server

The HTTP API is an optional extra. Run it without installing the server dependencies into the normal CLI environment:

```bash
uvx --from "nber-cli[server]" nber-server --host 127.0.0.1 --port 31527
```

The server upgrades the local SQLite database to schema v3 on startup and exposes health, feed, paper, read-status, and settings endpoints under `/api/v1`. See the [Local HTTP API reference](docs/en/http-api.md) for parameters, response envelopes, side effects, and the loopback-only security boundary.

### Desktop App

Download the macOS or Windows installer from [GitHub Releases](https://github.com/sepinetam/nber-cli/releases). Current installers are unsigned, so read the [Desktop guide](docs/en/desktop.md) before overriding any macOS Gatekeeper or Windows SmartScreen warning. The guide also documents supported platforms, local files, settings, backup, and the current custom-database limitation.

## Documentation

More usage details, command references, MCP setup, Python API examples, development notes, and release history are available in the [documentation](docs/en/index.md).

## Development

```bash
uv sync --dev --group docs
uv run pytest tests
uv run ruff check .
uv run --group docs mkdocs serve
```

## License

NBER-CLI is released under the [Apache-2.0 License](LICENSE).
