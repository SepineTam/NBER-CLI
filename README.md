# NBER-CLI
A command line interface for downloading the National Bureau of Economic Research (NBER) paper without brower.

[![Pytest](https://github.com/SepineTam/NBER-CLI/actions/workflows/pytest.yml/badge.svg)](https://github.com/SepineTam/NBER-CLI/actions/workflows/pytest.yml)
[![Lint](https://github.com/SepineTam/NBER-CLI/actions/workflows/lint.yml/badge.svg)](https://github.com/SepineTam/NBER-CLI/actions/workflows/lint.yml)
[![Docs](https://github.com/SepineTam/NBER-CLI/actions/workflows/docs.yml/badge.svg)](https://github.com/SepineTam/NBER-CLI/actions/workflows/docs.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

[简体中文](README.zh-CN.md) | [Documentation](docs/index.md)

> **NBER** is a registered trademark of the [National Bureau of Economic Research](https://www.nber.org). This project is an independent open-source tool and is **not affiliated with, endorsed by, or sponsored by** the National Bureau of Economic Research. By using this project, you agree to the [Usage Policy](docs/en/policy.md).

## Features

- Search NBER working papers by title, paper number, author, abstract, or keyword.
- Fetch structured metadata and abstracts for a paper ID such as `w25000`.
- Download single papers or batches as PDF files.
- Expose the same core workflows as MCP tools for AI agents.
- Return human-readable output by default, with JSON output for automation.

## Quick Start

Run commands directly with `uvx`:

```bash
uvx nber-cli search "Labor Economic"
uvx nber-cli info w25000
uvx nber-cli download w34567
```

Or install the command first:

```bash
uv tool install nber-cli
nber-cli search "Labor Economic"
nber-cli info w25000
nber-cli download w34567
```

## MCP Server for Agents

NBER-CLI can run as a stdio MCP server:

```bash
uvx nber-cli mcp-server
```

Example MCP client configuration:

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

The MCP server exposes tools for paper lookup, search, and PDF download.

## Documentation

More usage details, command references, MCP setup, Python API examples, development notes, and release history are available in the [documentation](docs/index.md).

## Development

```bash
uv sync --dev --group docs
uv run pytest
uv run ruff check .
uv run --group docs mkdocs serve
```

## License

NBER-CLI is released under the [Apache-2.0 License](LICENSE).
