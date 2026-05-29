# CLI 参考

可执行命令是 `nber-cli`。

```bash
nber-cli [--version] <command> [options]
```

## 全局选项

| 选项 | 说明 |
| --- | --- |
| `-v`, `--version` | 打印已安装的 NBER-CLI 版本。 |
| `-h`, `--help` | 显示命令帮助。 |

不带子命令运行 `nber-cli` 会打印顶层帮助并成功退出。

## 命令

| 命令 | 用途 |
| --- | --- |
| `download` | 下载一篇或多篇论文 PDF。 |
| `info` | 显示单篇论文的元数据和摘要。 |
| `search` | 搜索 NBER 工作论文。 |
| `mcp-server` | 启动给 Agent 使用的 MCP server。 |

## download

下载单篇论文：

```bash
nber-cli download w34567
```

下载到明确文件：

```bash
nber-cli download w34567 --file ~/papers/w34567.pdf
nber-cli download w34567 -f ~/papers/w34567.pdf
```

下载到目标目录：

```bash
nber-cli download w34567 --save-base ~/papers/nber
nber-cli download w34567 -s ~/papers/nber
```

批量下载：

```bash
nber-cli download --batch w34567 w25000 w32000 --save-base ~/papers/nber
nber-cli download -b w34567 w25000 w32000 -s ~/papers/nber
```

### download 选项

| 选项 | 说明 |
| --- | --- |
| `paper_id` | 单篇下载时可选的位置参数，例如 `w34567`。 |
| `--file`, `-f` | 单篇下载的明确 PDF 输出路径。 |
| `--save-base`, `-s` | 生成 `<paper_id>.pdf` 文件的目标目录，默认是当前工作目录。 |
| `--batch`, `-b` | 要并发下载的一组论文编号。 |

### download 规则

- 单篇位置参数不能和 `--batch` 同时使用。
- `--file` 只支持单篇论文。
- 批量模式只支持 `--save-base`。
- 如果没有传入 `--file` 或 `--save-base`，PDF 会保存到当前工作目录。
- 如果论文不可下载，NBER-CLI 会以退出码 `1` 退出，并打印可读错误信息。

## info

显示论文元数据：

```bash
nber-cli info w25000
```

显示全部可用字段：

```bash
nber-cli info w25000 --all
```

返回 JSON：

```bash
nber-cli info w25000 --format json
nber-cli info w25000 -f json
```

### info 选项

| 选项 | 说明 |
| --- | --- |
| `paper_id` | 必填论文编号，可以带 `w` 前缀，也可以不带。 |
| `--all`, `-a` | 如果可用，包含相关字段和 published-version 信息。 |
| `--format`, `-f` | 输出格式：`list` 或 `json`，默认是 `list`。 |

## search

按查询词搜索：

```bash
nber-cli search "Labor Economic"
```

使用日期筛选：

```bash
nber-cli search "minimum wage" --start-date 2024-01-01 --end-date 2024-12-31
```

调整分页：

```bash
nber-cli search "inflation" --page 2 --per-page 50
```

返回 JSON：

```bash
nber-cli search "inflation" --format json
nber-cli search "inflation" -f json
```

### search 选项

| 选项 | 说明 |
| --- | --- |
| `query` | 必填搜索词，可以是标题、编号、作者、摘要片段或关键词。 |
| `--start-date`, `--start` | 只包含该日期及之后的论文，格式为 `YYYY-MM-DD`。 |
| `--end-date`, `--end` | 只包含该日期及之前的论文，格式为 `YYYY-MM-DD`。 |
| `--page` | 要获取的结果页，默认是 `1`。 |
| `--per-page` | 每页结果数量，允许值为 `20`、`50`、`100`，默认是 `20`。 |
| `--format`, `-f` | 输出格式：`list` 或 `json`，默认是 `list`。 |

只提供 `--start-date` 时，NBER-CLI 会自动使用当前日期作为结束日期。

## mcp-server

启动默认 stdio MCP server：

```bash
nber-cli mcp-server
```

启动 HTTP transport：

```bash
nber-cli mcp-server --transport streamable_http --port 8000
```

### mcp-server 选项

| 选项 | 说明 |
| --- | --- |
| `--transport` | 传输机制：`stdio` 或 `streamable_http`，默认是 `stdio`。 |
| `--port` | `streamable_http` 使用的端口，默认是 `8000`。 |

客户端配置和工具详情见 [MCP Server](mcp.md)。

## 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 命令成功完成，或帮助信息已打印。 |
| `1` | 运行时失败，例如下载失败。 |
| `2` | 命令行参数无效。 |

## 输出格式

`info` 和 `search` 默认使用 `list`，这是一种适合人阅读的文本格式。需要把输出交给脚本或 Agent 工作流时，请使用 `--format json`。
