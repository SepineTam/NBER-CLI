# OpenClaw

除非当前 OpenClaw 运行环境已经提供专门的 plugin 集成，否则使用 MCP 加 NBER-CLI skill。

## MCP Server

把 NBER-CLI MCP server 加到 OpenClaw 的 MCP 配置中：

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

这个配置会通过 `uvx` 运行已发布的 `nber-cli` 包，所以不要求用户 checkout 本仓库。

## Skill

如果 OpenClaw 支持导入 skill 或指令文件，读取：

```text
plugins/nber-cli/skills/nber-cli/SKILL.md
```

这个 skill 包含使用策略、命令示例、JSON 输出建议，以及常见错误解释。

## 验证

让 OpenClaw 运行：

```bash
uvx nber-cli info w25000 --format json
```

如果命令可运行但 PDF 下载失败，应向用户报告 HTTP 状态或 NBER 响应，不要尝试绕过访问限制。

