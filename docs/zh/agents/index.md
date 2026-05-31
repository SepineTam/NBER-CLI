# Agent 指南

这一组文档给需要为自己安装或配置 NBER-CLI 的 Agent 使用。

## 选择路径

优先使用当前运行环境支持的第一种方式：

| 运行环境 | 推荐方式 | 备用方式 |
| --- | --- | --- |
| Claude Code | 安装 NBER-CLI plugin | MCP server 加 skill |
| Codex | 安装 NBER-CLI plugin | MCP server 加 skill |
| OpenClaw | MCP server 加 skill | 直接运行 `uvx nber-cli ...` |
| 其他 Agent | MCP server 加 skill | 直接运行 `uvx nber-cli ...` |

## 通用 MCP 配置

支持 MCP 的 Agent 可以直接运行已发布的 NBER-CLI 包，不需要用户提前 checkout 本仓库：

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

## 通用 Skill

支持 skill 的 Agent 应读取 NBER-CLI skill：

```text
plugins/nber-cli/skills/nber-cli/SKILL.md
```

这个 skill 会告诉 Agent 什么时候使用 NBER-CLI、如何运行 `uvx nber-cli ...`、如何配置 MCP，以及如何解释访问错误。

## 安全规则

NBER-CLI 不绕过 NBER 的访问控制。如果 NBER 拒绝请求、返回限制页面或阻止 PDF 下载，应把这个响应视为权威结果。

