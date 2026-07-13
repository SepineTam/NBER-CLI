# Codex

这页说明当前版本如何把 NBER-CLI 接入 Codex。

## 准备工作

安装 [`uv`](https://docs.astral.sh/uv/getting-started/installation/)，并确认下面两个命令可用：

```bash
uvx --version
codex --version
```

不需要 clone 本仓库，也不需要全局安装 NBER-CLI。`uvx` 会在隔离环境中下载并运行已发布的软件包。

## 添加 MCP Server

把 NBER-CLI 注册为本地 stdio MCP server：

```bash
codex mcp add nber-cli-mcp -- uvx nber-cli mcp-server
```

Codex 需要使用时会执行 `uvx nber-cli mcp-server`。这里不会启动可选的 HTTP API，因此不需要安装 `server` extra。

## 验证配置

确认 MCP server 已注册：

```bash
codex mcp list
codex mcp get nber-cli-mcp
```

再单独检查底层 CLI：

```bash
uvx nber-cli --help
uvx nber-cli info w25000 --format json
uvx nber-cli search "labor economics" --format json
```

然后让 Codex 执行：

```text
Use NBER-CLI to show the abstract for NBER paper w25000.
```

如果启动失败，直接运行 `uvx nber-cli mcp-server` 并查看完整错误。如果找不到 `uvx`，请安装 `uv` 或修复 `PATH`。

## 可选的 Skill 指令

仓库中还提供了可复用的操作指令：

```text
plugins/nber-cli/skills/NBER-CLI/SKILL.md
```

如果本地没有 checkout 仓库，可以读取 GitHub 上被追踪的文件：

```text
https://github.com/sepinetam/nber-cli/blob/master/plugins/nber-cli/skills/NBER-CLI/SKILL.md
```

不复制这个 skill 文件也能使用 MCP server；它只是为 Codex 补充操作流程指导。

## Plugin 可用性

仓库目前追踪了 Codex plugin manifest：

```text
plugins/nber-cli/.codex-plugin/plugin.json
```

但是，当前版本没有追踪把仓库作为 Codex marketplace 所需的 `.agents/plugins/marketplace.json` 清单。因此，当前版本不要执行下面这些命令：

```bash
codex plugin marketplace add sepinetam/nber-cli
codex plugin add nber-cli@nber-cli
```

在未来版本加入 marketplace 清单之前，请使用上面的 MCP 配置方式。

## 移除配置

```bash
codex mcp remove nber-cli-mcp
```

## 访问策略

NBER-CLI 不绕过 NBER 访问控制。如果 NBER 返回 `403`、`404`、access denied 页面或 download limit 响应，请如实向用户报告。不要轮换代理、共享凭据、绕过 CAPTCHA 或伪装流量。
