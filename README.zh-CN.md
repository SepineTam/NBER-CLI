# NBER-CLI
一个用于下载 National Bureau of Economic Research (NBER) 工作论文的命令行界面。

[![Pytest](https://github.com/SepineTam/NBER-CLI/actions/workflows/pytest.yml/badge.svg)](https://github.com/SepineTam/NBER-CLI/actions/workflows/pytest.yml)
[![Lint](https://github.com/SepineTam/NBER-CLI/actions/workflows/lint.yml/badge.svg)](https://github.com/SepineTam/NBER-CLI/actions/workflows/lint.yml)
[![Docs](https://github.com/SepineTam/NBER-CLI/actions/workflows/docs.yml/badge.svg)](https://github.com/SepineTam/NBER-CLI/actions/workflows/docs.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

[English](README.md) | [中文文档](docs/zh-CN/index.md)

> **NBER** 是 [美国国家经济研究局](https://www.nber.org)（National Bureau of Economic Research）的注册商标。本项目是独立的开源工具，与美国国家经济研究局**不存在任何附属、认可或赞助关系**。使用本项目即视为同意[使用政策](docs/zh/policy.md)。

## 功能特性

- 按标题、论文编号、作者、摘要或关键词搜索 NBER 工作论文。
- 通过 `w25000` 这样的论文编号获取结构化元数据和摘要。
- 下载单篇或批量论文 PDF。
- 通过 MCP 工具把核心能力暴露给 AI Agent。
- 默认输出适合阅读的文本，也支持 JSON 输出用于自动化流程。

## 快速开始

直接通过 `uvx` 运行：

```bash
uvx nber-cli search "Labor Economic"
uvx nber-cli info w25000
uvx nber-cli download w34567
```

也可以先安装命令：

```bash
uv tool install nber-cli
nber-cli search "Labor Economic"
nber-cli info w25000
nber-cli download w34567
```

## 给 Agent 使用的 MCP Server

NBER-CLI 可以作为 stdio MCP server 运行：

```bash
uvx nber-cli mcp-server
```

MCP 客户端配置示例：

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

MCP server 提供论文查询、搜索和 PDF 下载工具。

## 文档

更完整的用法、命令参考、MCP 配置、Python API 示例、开发说明和发布记录请见 [中文文档](docs/zh-CN/index.md)。

## 开发

```bash
uv sync --dev --group docs
uv run pytest
uv run ruff check .
uv run --group docs mkdocs serve
```

## 许可证

NBER-CLI 使用 [Apache-2.0 License](LICENSE) 发布。
