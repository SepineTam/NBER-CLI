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
uvx nber-cli mcp-server --transport streamable_http --port 8000
```

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
| `paper_id` | `string` | 必填 | 论文编号，例如 `w34567` 或 `34567`。 |
| `output_path` | `string` 或 `null` | `null` | 明确的 PDF 输出路径。如果省略，文件会保存为 server 当前工作目录下的 `<paper_id>.pdf`。 |

下载成功时返回 `true`。如果下载失败，底层异常会传给 MCP 调用方。

## Agent 使用建议

- 不知道论文编号时，先用 `search_papers`。
- 工作流需要确认标题、作者或摘要时，下载前先用 `get_paper_info`。
- 下载时尽量传入明确的 `output_path`，让文件位置可预测。
- NBER 可能会限制新发布论文第一周的访问，这类下载可能返回 HTTP 403。

## 安全说明

MCP server 会向 NBER 发起网络请求，并可以通过 `download_paper` 写入 PDF 文件。请只在可信客户端中配置该 server；需要可预测文件位置时，请传入明确下载路径。
