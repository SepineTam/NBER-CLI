# MCP Server

NBER-CLI 内置 MCP server，让 Agent 无需解析命令行文本，就能搜索 NBER、查看论文元数据和下载 PDF。

MCP server 如何与 CLI 共用核心模块，见 [系统架构](architecture.md)。

## 启动服务

默认传输方式是 stdio：

```bash
uvx nber-cli mcp-server
```

已安装的命令也一样：

```bash
nber-cli mcp-server
```

## MCP 客户端配置

适用于启动 stdio server 的 MCP 客户端：

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

如果机器上已经安装了 `nber-cli`，也可以直接调用：

```json
{
  "mcpServers": {
    "nber-cli-mcp": {
      "command": "nber-cli",
      "args": ["mcp-server"]
    }
  }
}
```

## HTTP Transport

如果客户端支持 streamable HTTP：

```bash
uvx nber-cli mcp-server --transport streamable-http --port 8000
```

`--port` 只对 HTTP transport 生效。当端口设为非默认值时，需要加 `--yes` 确认：

```bash
uvx nber-cli mcp-server --transport streamable-http --port 9000 --yes
```

server 绑定到本地接口；应将其视为本地服务，如需远程访问请接入反向代理（或 SSH 隧道）。server 不内置身份认证：任何能访问该端口的网络位置都可以调用全部三个工具，并在宿主机文件系统中触发 PDF 下载。未经可信的反向代理认证，不要把该端口暴露在公网上。

客户端通过 HTTP 连接时使用标准 MCP 客户端 URL（端口与 `--port` 一致）：

```text
http://127.0.0.1:8000/mcp
```

使用旧版 SSE transport 时，通过 `--transport sse` 启动，并连接：

```text
http://127.0.0.1:8000/sse
```

端点路径取决于所选 transport：streamable HTTP 使用 `/mcp`，SSE 使用 `/sse`。实际主机和路径请按所接入的反向代理进行调整。

## 可用工具

### get_paper_info

获取单篇 NBER 工作论文的元数据和摘要。

参数：

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `paper_id` | `string` | 必填 | 论文编号，例如 `w25000` 或 `25000`。 |
| `include_all` | `boolean` | `true` | 如果可用，包含相关字段和 published-version 数据。 |

返回包含 `id`、`title`、`authors`、`date`、`abstract`、`url` 等字段的字典。

### search_papers

搜索 NBER 工作论文。

参数：

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `query` | `string` | 必填 | 标题、编号、作者、摘要片段或关键词。 |
| `start_date` | `string` 或 `null` | `null` | 最早论文日期，格式为 `YYYY-MM-DD`。 |
| `end_date` | `string` 或 `null` | `null` | 最晚论文日期，格式为 `YYYY-MM-DD`。 |
| `page` | `integer` | `1` | 要获取的结果页。 |
| `per_page` | `integer` | `20` | 每页结果数量，支持 `20`、`50` 和 `100`。 |

返回搜索元数据和论文列表。

### download_paper

下载单篇论文 PDF。

参数：

| 名称 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `paper_id` | `string` | 必填 | 论文编号，例如 `w34567` 或 `34567`；两种形式都会被规范化为 `w34567`。 |
| `output_path` | `string` 或 `null` | `null` | 明确的 PDF 输出路径，解析后必须位于 server 进程当前工作目录内。省略时会使用规范化后的文件名，例如 `w34567.pdf`。 |

下载成功时返回 `{"success": true}`。参数、路径、网络或文件系统错误会返回 `{"error": "..."}`，不会向 MCP 调用方抛出底层异常；调用方必须检查返回值中出现的是哪个 key。

## Agent 使用建议

- 不知道论文编号时，先用 `search_papers`。
- 工作流需要确认标题、作者或摘要时，下载前先用 `get_paper_info`。
- 需要明确文件位置时传入 `output_path`，但该路径必须位于 server 进程当前工作目录内。
- NBER 可能会限制新发布论文第一周的访问，这类下载可能返回 HTTP 403。

## 安全说明

MCP server 会向 NBER 发起网络请求，并可以通过 `download_paper` 写入 PDF 文件。请只在可信客户端中配置该 server；需要可预测文件位置时，请传入明确下载路径。

### 本地持久化与缓存

`get_paper_info` 遵守与 CLI 相同的 `info_cache` 开关和 TTL。缓存开启时，命中会从 `info_cache` 读取，未命中会写入新行，行为与 CLI 一致。每次调用还会向 `info_log` 追加一行，使本地数据库记录这次查询；这个由 SQLModel/SQLAlchemy 访问的本地数据库与 CLI 共用，由 `~/.nber-cli/config.json` 中配置的路径或 `sqlite:///...` URL 决定。工具的返回值不会标明结果是否来自缓存；调用方需要该信号时，应自己检查调用历史或直接使用 CLI。

### 与 CLI 的差异

- `get_paper_info` 不接受每次调用的 `--refresh` 参数。要强制刷新，可以先关闭缓存、调用 `get_paper_info`，再打开缓存，或等待 TTL 到期后自然刷新。
- `get_paper_info` 和 CLI 都不会向 stderr 输出缓存命中提示。
- 当前版本的 MCP `search_papers` 与 `download_paper` 工具**不**写 `query_log` 或 `download_log`；只有 CLI 会在这两个版本中写入。
- MCP 工具的返回值就是普通 Python 字典，不会包装为 `DownloadBatchResult`。工具失败通过 `error` key 返回，而不是向 MCP 调用方抛出异常。

### 返回对象结构

工具的 docstring 已经描述了公开的返回值形状。简而言之：

- `get_paper_info` 返回的字典与 CLI `--format json` 路径下的 `info(...)` 一致；当 `include_all=True` 时还会并入 `related(...)` 字段。`published_version` 仅在 `include_all=True` 且非空时出现。
- `search_papers` 返回 `search_results(...)` 字典。
- `download_paper` 成功时返回 `{"success": True}`，失败时返回 `{"error": "..."}`。

### 下载路径规则

省略 `output_path` 时，文件会保存到 `<cwd>/<规范化论文编号>.pdf`，其中 `cwd` 是 **server 进程**的工作目录。server 通常由 MCP 客户端启动，因此该目录可能不同于用户交互式 shell 的当前目录。明确路径只有在解析后仍位于同一工作目录内时才会被接受；试图跳出该目录会返回 `error` 字典。下载模块会一次性把整段响应体写入磁盘，并覆盖目标路径上的已有文件。不保证原子 rename；写入被打断可能在目标路径上留下部分文件。
