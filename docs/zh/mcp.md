# MCP Server

NBER-CLI 内置 MCP server，让 Agent 无需解析命令行文本，就能搜索 NBER、查看论文元数据和下载 PDF。

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

## Streamable HTTP Transport

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

实际的主机和路径请按所接入的反向代理进行调整。

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
| `paper_id` | `string` | 必填 | 论文编号字符串，按字面值用于构造 NBER PDF URL（`https://www.nber.org/papers/{paper_id}.pdf`），并在省略 `output_path` 时作为默认输出文件名。NBER 标准的论文编号带 `w` 前缀，例如 `w34567`。请传入 `w34567` 而不是 `34567`，请求才能命中 NBER PDF 端点，默认文件名也才是 `w34567.pdf`。 |
| `output_path` | `string` 或 `null` | `null` | 明确的 PDF 输出路径。如果省略，文件会保存为 server 当前工作目录下的 `<paper_id>.pdf`。 |

下载成功时返回 `true`。如果下载失败，底层异常会传给 MCP 调用方。

## Agent 使用建议

- 不知道论文编号时，先用 `search_papers`。
- 工作流需要确认标题、作者或摘要时，下载前先用 `get_paper_info`。
- 下载时尽量传入明确的 `output_path`，让文件位置可预测。
- NBER 可能会限制新发布论文第一周的访问，这类下载可能返回 HTTP 403。

## 安全说明

MCP server 会向 NBER 发起网络请求，并可以通过 `download_paper` 写入 PDF 文件。请只在可信客户端中配置该 server；需要可预测文件位置时，请传入明确下载路径。

### 本地持久化与缓存

`get_paper_info` 遵守与 CLI 相同的 `info_cache` 开关和 TTL。缓存开启时，命中会从 `info_cache` 读取，未命中会写入新行，行为与 CLI 一致。每次调用还会向 `info_log` 追加一行，使本地数据库记录这次查询；这个由 SQLModel/SQLAlchemy 访问的本地数据库与 CLI 共用，由 `~/.nber-cli/config.json` 中配置的路径或 `sqlite:///...` URL 决定。工具的返回值不会标明结果是否来自缓存；调用方需要该信号时，应自己检查调用历史或直接使用 CLI。

### 与 CLI 的差异

- `get_paper_info` 不接受每次调用的 `--refresh` 参数。要强制刷新，可以先关闭缓存、调用 `get_paper_info`，再打开缓存，或等待 TTL 到期后自然刷新。
- `get_paper_info` 不会输出 CLI 那种缓存命中 stderr 提示。
- 当前版本的 MCP `search_papers` 与 `download_paper` 工具**不**写 `query_log` 或 `download_log`；只有 CLI 会在这两个版本中写入。
- MCP 工具的返回值就是普通 Python 字典；不会包装为 `DownloadBatchResult` 这类对象。失败时会把底层异常抛给 MCP 调用方。

### 返回对象结构

工具的 docstring 已经描述了公开的返回值形状。简而言之：

- `get_paper_info` 返回的字典与 CLI `--format json` 路径下的 `info(...)` 一致；当 `include_all=True` 时还会并入 `related(...)` 字段。`published_version` 仅在 `include_all=True` 且非空时出现。
- `search_papers` 返回 `search_results(...)` 字典。
- `download_paper` 成功时返回布尔值 `True`；失败时把底层 `aiohttp` 或网络异常抛给调用方。

### 下载路径规则

省略 `output_path` 时，文件会保存到 `<cwd>/<paper_id>.pdf`，其中 `cwd` 是 **server 进程**的工作目录。server 通常由 MCP 客户端（例如 Claude Code 会话）启动，因此该工作目录与用户 shell 当前目录不同。需要把文件落到确定位置时，请始终传入 `output_path`。下载模块会一次性把整段响应体写入磁盘，并覆盖目标路径上的已有文件。不保证原子 rename；写入被打断可能在目标路径上留下部分文件。
