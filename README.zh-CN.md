# NBER-CLI
一个无需浏览器即可访问 National Bureau of Economic Research (NBER) 论文的命令行界面。

[![Pytest](https://github.com/sepinetam/nber-cli/actions/workflows/pytest.yml/badge.svg)](https://github.com/sepinetam/nber-cli/actions/workflows/pytest.yml)
[![Lint](https://github.com/sepinetam/nber-cli/actions/workflows/lint.yml/badge.svg)](https://github.com/sepinetam/nber-cli/actions/workflows/lint.yml)
[![Docs](https://github.com/sepinetam/nber-cli/actions/workflows/docs.yml/badge.svg)](https://github.com/sepinetam/nber-cli/actions/workflows/docs.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/nber-cli.svg)](https://pypi.org/project/nber-cli/)
[![PyPI Downloads](https://static.pepy.tech/badge/nber-cli)](https://pepy.tech/projects/nber-cli)
[English](README.md) | [中文文档](docs/zh/index.md)

> **NBER** 是 [美国国家经济研究局](https://www.nber.org)（National Bureau of Economic Research）的注册商标。本项目是独立的开源工具，与美国国家经济研究局**不存在任何附属、认可或赞助关系**。使用本项目即视为同意[使用政策](docs/zh/policy.md)。

## 功能特性

- 按标题、论文编号、作者、摘要或关键词搜索 NBER 工作论文。
- 通过 `w25000` 这样的论文编号获取结构化元数据和摘要。
- 下载单篇或批量论文 PDF。
- 通过本地 RSS feed 缓存追踪 NBER 新发布的工作论文（`nber-cli feed fetch` / `feed clean`）。
- 本地缓存论文元数据（`nber-cli info` 会写入 `info_cache`），采用滑动 TTL；同时为 `search`、`download` 和 `info` 查询记录行为日志。
- 把缓存、RSS 条目和行为日志统一存放在本地 SQLite 数据库 `~/.nber-cli/nber.db`，由 SQLModel/SQLAlchemy 管理，路径可用普通文件路径或 `sqlite:///...` URL 配置。
- 通过 MCP 工具把核心能力暴露给 AI Agent。
- 提供可选的 loopback-only HTTP server，供 Desktop 应用和本地集成使用。
- 提供 macOS 和 Windows Desktop 论文工作台，支持 Feed 同步、未读状态、论文详情和引用复制。
- 默认输出适合阅读的文本，也支持 JSON 输出用于自动化流程。
- 提供 `--verbose` 调试日志与轮转日志文件，便于排查问题。
- 通过 `-c/--config <path>` 可在单次运行中临时指定配置文件。

完整可配置项和本地数据库结构请见[配置](docs/zh/configuration.md)，默认写入磁盘的内容请见[使用政策](docs/zh/policy.md)。

## 快速开始

### 在 Agent 中使用

NBER-CLI 可以通过 plugin、MCP server 和 skill 给 Agent 使用。Claude Code 和 Codex 优先安装 NBER-CLI plugin；OpenClaw 和其他 Agent 使用 MCP server 加 skill。

如果你希望让 Agent 自动安装和检查 NBER-CLI，可以把下面这段话发给它：

```text
Install NBER-CLI globally for yourself from https://github.com/sepinetam/nber-cli, and check the status.
```

安装成功后，可以用下面任意一句话验证：

```text
我记得在 2025 年，Anton 在 NBER 上有一篇关于 Agent for Econ 的文章，帮我下载到当前目录。
```

```text
我记得 w25000 这篇论文很有意思，把摘要发给我看看。
```

如果你是 Agent，请访问 [Agent 指南](docs/zh/agents/index.md)。

### 命令行模式
直接通过 `uvx` 运行：

```bash
uvx nber-cli search "Labor Economic"
uvx nber-cli info w25000
uvx nber-cli download w34567
```

如果提示命令不存在或报错请先通过 `uvx nber-cli -v` 检查当前运行的版本，如果不是最新版本可以通过如下命令将缓存更新至最新版本：

```bash
uvx --refresh nber-cli -v
```

也可以先安装命令：

```bash
uv tool install nber-cli
nber-cli search "Labor Economic"
nber-cli info w25000
nber-cli download w34567
```

### MCP Server 模式

NBER-CLI 可以作为 stdio MCP server 运行：

```bash
uvx nber-cli mcp-server
```

MCP 客户端配置示例：

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

MCP server 提供论文查询、搜索和 PDF 下载工具。

### 本地 HTTP Server

HTTP API 属于可选依赖，不会进入普通 CLI 环境。可以直接运行：

```bash
uvx --from "nber-cli[server]" nber-server --host 127.0.0.1 --port 31527
```

Server 启动时会把本地 SQLite 数据库升级到 schema v3，并在 `/api/v1` 下提供健康检查、feed、论文详情、已读状态和设置接口。

### Desktop 应用

从 [GitHub Releases](https://github.com/sepinetam/nber-cli/releases) 下载 macOS 或 Windows 安装包。当前安装包尚未签名；在绕过 macOS Gatekeeper 或 Windows SmartScreen 警告前，请先阅读 [Desktop 指南](docs/zh/desktop.md)。其中也说明了支持平台、本地文件、设置、备份方式和当前自定义数据库路径限制。

## 文档

更完整的用法、命令参考、MCP 配置、Python API 示例、开发说明和发布记录请见 [中文文档](docs/zh/index.md)。

## 开发

```bash
uv sync --dev --group docs
uv run pytest
uv run ruff check .
uv run --group docs mkdocs serve
```

## 许可证

NBER-CLI 使用 [Apache-2.0 License](LICENSE) 发布。
