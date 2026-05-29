# NBER-CLI

NBER-CLI 是一个命令行工具包，用于搜索 NBER 工作论文、查看论文元数据、下载 PDF，并通过 MCP 把这些能力提供给 AI Agent。

## 它能做什么

NBER-CLI 聚焦 NBER 工作论文的常见研究流程：

- 按关键词、作者、标题、摘要或论文编号搜索论文。
- 查看论文标题、作者、日期、摘要、URL 和相关元数据。
- 通过论文编号下载 PDF。
- 将多篇论文批量下载到指定目录。
- 作为 MCP server 向 Agent 提供论文搜索、查询和下载能力。

## 快速开始

无需安装即可运行：

```bash
uvx nber-cli search "Labor Economic"
uvx nber-cli info w25000
uvx nber-cli download w34567
```

安装成可复用命令：

```bash
uv tool install nber-cli
nber-cli search "Labor Economic"
nber-cli info w25000
nber-cli download w34567
```

## 一分钟配置 MCP

启动默认 stdio MCP server：

```bash
uvx nber-cli mcp-server
```

添加到 MCP 客户端：

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

## 文档导航

- [快速开始](getting-started.md)：安装方式和第一组命令。
- [CLI 参考](cli.md)：命令语法、选项、输出格式和示例。
- [MCP Server](mcp.md)：Agent 配置、传输方式和可用工具。
- [Python API](python-api.md)：异步函数和数据模型。
- [配置](configuration.md)：运行时默认值和操作行为。
- [开发](development.md)：本地环境、测试、文档、CI 和发布流程。
- [贡献指南](contributing.md)：贡献标准和评审期望。
- [更新日志](changelog.md)：项目重要变更。

## 项目状态

当前公开命令模型是 `nber-cli` v0.2.0。CLI 保持小而清晰：默认文本输出适合人读，需要结构化输出时可以使用 `--format json`。
