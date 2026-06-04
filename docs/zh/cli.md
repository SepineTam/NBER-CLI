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
| `db` | 管理本地 SQLite 数据库。 |
| `feed` | 管理 NBER 最新工作论文 RSS feed 的本地缓存。 |
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
| `--refresh` | 跳过本地 `info_cache` 并直接从 NBER 重新拉取。缓存开启时，新数据会写回缓存。 |

当缓存开启且缓存条目尚未超过配置的 TTL 时，重复执行 `info` 会从本地数据库返回。TTL 到期后的第一次 `info` 调用，或任何携带 `--refresh` 的调用，都会执行实时网络拉取。

MCP 的 `get_paper_info` 工具遵循相同的缓存行为，也支持 `--refresh`。

## info cache

管理 `info_cache` 的读取行为并清理缓存记录。

显示当前缓存状态、TTL 和已缓存行数：

```bash
nber-cli info cache
```

全局开关缓存：

```bash
nber-cli info cache --turn-on
nber-cli info cache --turn-off
```

设置缓存刷新间隔（天）：

```bash
nber-cli info cache --set-refresh 7
nber-cli info cache --set-refresh 30
```

`--set-refresh` 必须是正整数。新值会写入 `~/.nber-cli/config.json`，并在后续每次 `info` 调用中作为 TTL 生效。

清理 30 天内没有刷新的缓存记录：

```bash
nber-cli info cache clear
nber-cli info cache clear --days 30
```

清理全部缓存记录：

```bash
nber-cli info cache clear --all
nber-cli info cache clean
```

`info cache clean` 是 `info cache clear --all` 的便利别名。

按 `last_fetched_at` 日期清理缓存记录：

```bash
nber-cli info cache clear --end-date 2026-06-01
nber-cli info cache clear --start-date 2026-05-01 --end-date 2026-06-01
```

只提供 `--end-date` 时，会从最早的缓存记录清理到该结束日期。`--start-date` 和 `--end-date` 都是前后包含的。只提供 `--start-date` 是无效的。

删除前，`info cache clear` 会先打印匹配到的缓存记录数量，并要求确认：

```text
This operation is irreversible.
Deleted info cache records may be fetched again from NBER.
Continue? [y/N]:
```

只有输入 `y` 或 `Y` 才会继续。其他输入都会中止，不删除记录。

### info cache 选项

| 子命令 | 选项 | 说明 |
| --- | --- | --- |
| (无) | `--turn-on` | 全局启用 info cache。 |
| (无) | `--turn-off` | 全局禁用 info cache。 |
| (无) | `--set-refresh` | 设置 info cache 刷新间隔（天），必须是正整数。 |
| `clear` | `--days` | 清理这么多天没有刷新的缓存记录，默认是 `30`。 |
| `clear` | `--all` | 清理全部 info cache 记录。 |
| `clear` | `--start-date` | 清理 `last_fetched_at` 在该日期及之后的缓存记录，格式为 `YYYY-MM-DD`。 |
| `clear` | `--end-date` | 清理 `last_fetched_at` 在该日期及之前的缓存记录，格式为 `YYYY-MM-DD`。 |
| `clean` | — | `clear --all` 的别名。 |

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

## feed

`feed` 用于处理 NBER 最新工作论文 RSS feed 和本地 SQLite 数据库。数据库会记录哪些 RSS 条目已经见过，因此 `feed fetch` 默认只显示新发现的论文。

### feed fetch

获取 RSS feed，把所有获取到的条目写入缓存，并默认只显示新的条目：

```bash
nber-cli feed fetch
```

显示所有获取到的 RSS 条目，包括缓存中已经存在的条目：

```bash
nber-cli feed fetch --display-all true
nber-cli feed fetch --display-all
```

限制输出数量：

```bash
nber-cli feed fetch --max-items 5
```

当提供 `--max-items` 且没有提供 `--display-all` 时，`--display-all` 默认会变成 `true`。因此 `nber-cli feed fetch --max-items 5` 会显示本次获取到的前 5 个 RSS 条目，而不是在没有新条目时显示空结果。

返回 JSON：

```bash
nber-cli feed fetch --format json
nber-cli feed fetch -f json
```

### feed clean

清理 feed 缓存数据库记录。这个操作删除的是本地缓存记录，不会影响 NBER。被删除的缓存记录如果仍然出现在 RSS feed 中，后续可能会再次作为新条目被获取。

清理 30 天没有再次出现的记录：

```bash
nber-cli feed clean
nber-cli feed clean --days 30
```

清理全部缓存记录：

```bash
nber-cli feed clean --all
```

按 last-seen 日期清理记录：

```bash
nber-cli feed clean --end-date 2026-05-31
nber-cli feed clean --start-date 2026-05-01 --end-date 2026-05-31
```

只提供 `--end-date` 时，会从最早的缓存记录清理到该结束日期。`--start-date` 和 `--end-date` 都是前后包含的。只提供 `--start-date` 是无效的。

删除前，`feed clean` 会先打印匹配到的缓存记录数量，并要求确认：

```text
This operation is irreversible.
Deleted cache records may be fetched again as new items if they still appear in the RSS feed.
Continue? [y/N]:
```

只有输入 `y` 或 `Y` 才会继续。其他输入都会中止，不删除记录。

### feed 选项

| 子命令 | 选项 | 说明 |
| --- | --- | --- |
| `fetch` | `--display-all [true|false]` | 显示所有获取到的 RSS 条目，而不是只显示新条目。 |
| `fetch` | `--format`, `-f` | 输出格式：`list` 或 `json`，默认是 `list`。 |
| `fetch` | `--max-items` | 最多显示多少个 feed 条目。 |
| `clean` | `--days` | 清理这么多天没有再次出现的缓存记录，默认是 `30`。 |
| `clean` | `--all` | 清理全部 feed 缓存记录。 |
| `clean` | `--start-date` | 清理 last-seen 日期在该日期及之后的缓存记录，格式为 `YYYY-MM-DD`。 |
| `clean` | `--end-date` | 清理 last-seen 日期在该日期及之前的缓存记录，格式为 `YYYY-MM-DD`。 |

## db

`db` 用于管理本地 SQLite 数据库，`info`、`search`、`download` 和 `feed` 会用这个数据库存放缓存和行为日志。

### db init

初始化数据库，并把数据库路径写入用户配置：

```bash
nber-cli db init
nber-cli db init --db-path ~/.nber-cli/nber.db
```

如果省略 `--db-path`，默认数据库路径是 `~/.nber-cli/nber.db`。

如果用户原来使用 0.3.0 留下的 `~/.nber-cli/feed.db`，并且还没有 `nber.db`，NBER-CLI 会沿用这个旧文件。首次使用时 schema 会自动从版本 1 升级到版本 2。

### db migrate

把数据库移到新路径并更新用户配置：

```bash
nber-cli db migrate ~/data/nber.db
```

迁移会移动 SQLite 数据库文件，以及 `-wal`、`-shm`、`-journal` 等 SQLite sidecar 文件。目标路径不能已经存在。

### db 选项

| 子命令 | 选项 | 说明 |
| --- | --- | --- |
| `init` | `--db-path` | SQLite 数据库路径，默认是 `~/.nber-cli/nber.db`。 |
| `migrate` | `new_db_path` | 新的 SQLite 数据库路径。 |

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

`info`、`search` 和 `feed fetch` 默认使用 `list`，这是一种适合人阅读的文本格式。需要把输出交给脚本或 Agent 工作流时，请使用 `--format json`。
