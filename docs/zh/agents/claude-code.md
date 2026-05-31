# Claude Code

这页写给需要把 NBER-CLI 安装进 Claude Code 的 Agent。不要猜，按步骤做。

## 要安装什么

使用 NBER-CLI 的 Claude Code plugin。

仓库地址：

```text
https://github.com/sepinetam/nber-cli
```

marketplace 名称：

```text
nber-cli
```

plugin 名称：

```text
nber-cli
```

MCP server 名称：

```text
nber-cli-mcp
```

Claude Code marketplace 文件是：

```text
.claude-plugin/marketplace.json
```

Claude Code plugin manifest 是：

```text
plugins/nber-cli/.claude-plugin/plugin.json
```

这个 plugin 包含：

- `NBER-CLI` skill
- `.mcp.json` MCP server 配置
- 启动 MCP server 的 `uvx nber-cli mcp-server` 命令

## 从 GitHub 安装

当 Claude Code 可以访问 GitHub 时，使用这个路径。

### 在 Claude Code 会话里

在 Claude Code 内运行这些 slash commands：

```text
/plugin marketplace add sepinetam/nber-cli
/plugin install nber-cli@nber-cli
/reload-plugins
```

每条命令的含义：

- `/plugin marketplace add sepinetam/nber-cli` 把这个 GitHub 仓库添加为 plugin marketplace。
- `/plugin install nber-cli@nber-cli` 从 `nber-cli` marketplace 安装 `nber-cli` plugin。
- `/reload-plugins` 在当前会话里重新加载 plugin，让新的 skill 和 MCP server 不重启也能生效。

### 在终端里

在普通 shell 里运行：

```bash
claude plugin marketplace add sepinetam/nber-cli
claude plugin install nber-cli@nber-cli --scope user
```

然后打开或回到 Claude Code，运行：

```text
/reload-plugins
```

scope 选择：

- `--scope user`：安装给当前用户，跨项目可用。
- `--scope project`：写入当前项目设置，给这个仓库的协作者共用。
- `--scope local`：只给当前用户、当前仓库使用。

除非用户明确要求项目共享或仅当前仓库使用，否则使用 `--scope user`。

## 验证 Plugin

在 Claude Code 内运行：

```text
/plugin
```

检查：

- `nber-cli` marketplace 存在
- `nber-cli` plugin 已安装
- plugin 已启用
- plugin 详情里有 `NBER-CLI` skill
- plugin 详情里有名为 `nber-cli-mcp` 的 MCP server

也可以在终端里检查：

```bash
claude plugin list --json
claude plugin details nber-cli
```

## 验证 MCP Server

在 Claude Code 内运行：

```text
/mcp
```

检查是否存在 `nber-cli-mcp`。如果 Claude Code 要求批准 project-scoped MCP server，先确认命令是下面这个，再批准：

```bash
uvx nber-cli mcp-server
```

也可以在终端里运行：

```bash
claude mcp list
claude mcp get nber-cli-mcp
```

如果 server 启动失败，运行：

```bash
uvx nber-cli --help
uvx nber-cli mcp-server
```

如果 `uvx nber-cli --help` 失败，先安装 `uv` 或修复 PATH。如果 `uvx nber-cli mcp-server` 失败，向用户报告完整错误。

## 验证 NBER-CLI 行为

运行直接 CLI 检查：

```bash
uvx nber-cli --help
uvx nber-cli info w25000 --format json
uvx nber-cli search "labor economics" --format json
```

然后让 Claude Code 执行：

```text
Use NBER-CLI to show the abstract for NBER paper w25000.
```

预期行为：

- Claude Code 应使用 NBER-CLI skill 或 MCP server。
- 不应该要求用户 clone 仓库。
- 不应该假设用户已经安装了 `nber-cli`。
- 可以使用 `uvx nber-cli ...`。

## 如果 Plugin 安装失败

只有 plugin 路径不可用时，才使用这个备用方案。

手动添加 MCP server：

```bash
claude mcp add nber-cli-mcp -- uvx nber-cli mcp-server
```

然后给 Claude Code 提供这个 skill 的内容：

```text
plugins/nber-cli/skills/NBER-CLI/SKILL.md
```

如果用户没有 checkout 本仓库，让它读取：

```text
https://github.com/sepinetam/nber-cli/blob/master/plugins/nber-cli/skills/NBER-CLI/SKILL.md
```

等价的手动 MCP JSON：

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

## 常见错误

使用这些精确值：

| 配置项 | 值 |
| --- | --- |
| 仓库 | `https://github.com/sepinetam/nber-cli` |
| Marketplace | `nber-cli` |
| Plugin | `nber-cli` |
| MCP server | `nber-cli-mcp` |

顺序很重要：先添加 `sepinetam/nber-cli` marketplace，再安装 plugin。不要为了运行 CLI 而 clone 仓库；使用 `uvx nber-cli ...`。

## 访问策略

NBER-CLI 不绕过 NBER 访问控制。如果 NBER 返回 `403`、`404`、access denied 页面或 download limit 响应，向用户报告这个结果。不要轮换代理、共享凭据、绕过 CAPTCHA 或伪装流量。
