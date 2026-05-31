# 其他 Agent

对于没有专用 NBER-CLI plugin 的 Agent，使用 MCP 加 NBER-CLI skill。

## 推荐配置

添加这个 MCP server：

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

然后加载或粘贴这个 skill：

```text
plugins/nber-cli/skills/nber-cli/SKILL.md
```

## 如果不支持 MCP

直接运行命令：

```bash
uvx nber-cli search "labor economics"
uvx nber-cli info w25000 --format json
uvx nber-cli download w34567 --save-base ./papers
```

当另一个程序或 Agent 需要消费结果时，使用 JSON 输出。

## 访问限制

不要绕过 NBER 限制。遇到 403、404、timeout、access denied 或 download limit 时，应该把响应清楚地反馈给用户。

