# Codex

这页写给需要把 NBER-CLI 安装进 Codex 的 Agent。不要猜，按步骤做。

## 要安装什么

使用 NBER-CLI 的 Codex plugin。

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

Codex marketplace 文件是：

```text
.agents/plugins/marketplace.json
```

Codex plugin manifest 是：

```text
plugins/nber-cli/.codex-plugin/plugin.json
```

这个 plugin 包含：

- `NBER-CLI` skill
- `.mcp.json` MCP server 配置
- 启动 MCP server 的 `uvx nber-cli mcp-server` 命令

## 从 GitHub 安装

当 Codex 可以访问 GitHub 时，使用这个路径。

运行：

```bash
codex plugin marketplace add sepinetam/nber-cli
codex plugin add nber-cli@nber-cli
```

每条命令的含义：

- `codex plugin marketplace add sepinetam/nber-cli` 把这个 GitHub 仓库添加为 Codex marketplace source。
- `codex plugin add nber-cli@nber-cli` 从 `nber-cli` marketplace 安装 `nber-cli` plugin。

如果仓库刚刚更新，而 Codex 已经知道这个 marketplace，刷新后重新安装：

```bash
codex plugin marketplace upgrade
codex plugin add nber-cli@nber-cli
```

## 从本地 checkout 安装

只有用户已经 clone 本仓库时，才使用这个路径。

在任意位置运行：

```bash
codex plugin marketplace add /absolute/path/to/nber-cli
codex plugin add nber-cli@nber-cli
```

把 `/absolute/path/to/nber-cli` 替换成真实仓库根目录。仓库根目录是包含 `.agents/plugins/marketplace.json` 的目录。

## 验证 Plugin

列出 marketplaces：

```bash
codex plugin marketplace list
```

列出 plugins：

```bash
codex plugin list
codex plugin list --marketplace nber-cli
```

预期结果：

- 可以看到 `nber-cli` marketplace
- 可以看到 `nber-cli` plugin
- 执行 `codex plugin add nber-cli@nber-cli` 后，`nber-cli` plugin 已安装

如果看不到 plugin，说明 marketplace source 错了或过期。重新添加仓库，或运行：

```bash
codex plugin marketplace upgrade
```

## 验证 MCP Server

安装后的 plugin 应提供名为下面这个的 MCP server：

```text
nber-cli-mcp
```

检查 MCP servers：

```bash
codex mcp list
codex mcp list --json
```

查看 server 详情：

```bash
codex mcp get nber-cli-mcp
codex mcp get nber-cli-mcp --json
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

然后让 Codex 执行：

```text
Use NBER-CLI to show the abstract for NBER paper w25000.
```

预期行为：

- Codex 应使用 NBER-CLI skill 或 MCP server。
- 不应该要求用户 clone 仓库。
- 不应该假设用户已经安装了 `nber-cli`。
- 可以使用 `uvx nber-cli ...`。

## 如果 Plugin 安装失败

只有 plugin 路径不可用时，才使用这个备用方案。

手动添加 MCP server：

```bash
codex mcp add nber-cli-mcp -- uvx nber-cli mcp-server
```

然后给 Codex 提供这个 skill 的内容：

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

顺序很重要：先添加 `sepinetam/nber-cli` marketplace，再安装 plugin。如果使用本地 checkout，marketplace source 必须是仓库根目录，也就是包含 `.agents/plugins/marketplace.json` 的目录。不要为了运行 CLI 而 clone 仓库；使用 `uvx nber-cli ...`。

## 访问策略

NBER-CLI 不绕过 NBER 访问控制。如果 NBER 返回 `403`、`404`、access denied 页面或 download limit 响应，向用户报告这个结果。不要轮换代理、共享凭据、绕过 CAPTCHA 或伪装流量。
