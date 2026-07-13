# 持久化层

NBER-CLI 使用一个本地 SQLite 数据库和一个 JSON 配置文件。数据库保存缓存和操作日志；配置文件保存用户选择的运行设置，例如数据库路径、info cache 行为和下载默认值。

## 文件

| 文件 | 默认路径 | 用途 |
| --- | --- | --- |
| 配置 | `~/.nber-cli/config.json` | 保存 `schema_version`、数据库路径、缓存、下载和 Desktop 设置。 |
| 数据库 | `~/.nber-cli/nber.db` | 保存 feed 缓存、论文信息缓存和行为日志。 |
| 旧数据库 | `~/.nber-cli/feed.db` | 仅在从旧版本升级且没有 `nber.db` 时作为回退使用。 |
| 调试日志 | `~/.nber-cli/debug.log` | 轮转日志文件；默认记录 warning/error，开启调试后记录 debug。 |
| Desktop sidecar 日志 | `~/.nber-cli/logs/sidecar.stdout.log`、`sidecar.stderr.log` | 内置本地 HTTP 服务的输出和错误。 |

## 数据库表

| 表 | 主要用途 | 写入方 | 清理方式 |
| --- | --- | --- | --- |
| `feed_items` | 按论文编号缓存 RSS 论文条目。 | `feed fetch` | `feed clean` |
| `feed_fetches` | RSS 获取次数和数量的审计记录。 | `feed fetch` | 没有 CLI 清理命令。 |
| `read_status` | 本地 HTTP API 和 Desktop 使用的逐篇已读/未读状态。 | Desktop / HTTP API | 没有 CLI 清理命令。 |
| `info_cache` | `info` 和 `get_paper_info` 使用的论文元数据缓存。 | `info`、MCP `get_paper_info` | `info cache clear` |
| `query_log` | CLI 搜索关键词和结果数量历史。 | CLI `search` | 没有 CLI 清理命令。 |
| `download_log` | CLI 下载成功与失败记录。 | CLI `download` | 没有 CLI 清理命令。 |
| `info_log` | 论文信息查询历史。 | CLI `info`、MCP `get_paper_info` | 没有 CLI 清理命令。 |

Schema 版本保存在 SQLite 的 `PRAGMA user_version` 中。当前 schema 版本是 `3`。已有 v1、v2 数据库会在下一次执行数据库相关 CLI 操作或启动本地 HTTP server 时自动升级。v2 到 v3 的迁移只新增 `read_status`，不会删除已有的 feed、缓存或日志记录。如果数据库来自更新的 schema 版本，NBER-CLI 会拒绝写入。

## Info Cache 行为

Info cache 由以下配置控制：

```json
{
  "info": {
    "cache_enabled": true,
    "cache_ttl_days": 30
  }
}
```

缓存开启时，`info` 和 MCP `get_paper_info` 会先检查 `info_cache`。新鲜的缓存命中会返回本地数据，并更新 `last_fetched_at` 和 `fetch_count`。这意味着 TTL 是滑动的：经常查询的论文元数据会以“最近一次本地命中”为基准继续保持新鲜。

CLI 可以用 `--refresh` 对单次 `info` 调用跳过缓存：

```bash
nber-cli info w25000 --refresh
```

MCP 工具没有逐次调用的 refresh 参数。需要强制实时查询时，需要临时关闭缓存，或等待 TTL 到期。

## Feed Cache 行为

`feed fetch` 会保存每个获取到的 RSS 条目，然后按选项返回“只返回新条目”或“返回所有本次获取条目”：

```bash
nber-cli feed fetch
nber-cli feed fetch --display-all true
nber-cli feed fetch --max-items 5
```

`feed_items` 以论文编号作为主键。已有行会更新标题、摘要、URL、source URL、GUID、作者和 `last_seen_at`。新行会保留自己的 `first_seen_at`。

`feed_fetches` 是追加式审计表。`feed clean` 不会清理它。

## 日志与软失败

搜索、下载和 info 操作会尝试追加行为日志。这些写入不是关键路径：数据库异常可以输出 warning，但不应阻止主搜索、下载或元数据查询完成。

缓存读取也会尽量软失败。如果缓存读取无法安全完成，命令会回退到网络路径，或在对应辅助函数中返回空缓存计数。

## 迁移与路径规则

初始化或迁移数据库：

```bash
nber-cli db init
nber-cli db init --db-path ~/data/nber.db
nber-cli db init --db-path sqlite:////Users/name/data/nber.db
nber-cli db migrate ~/data/nber.db
```

在 macOS 和 Linux 上，数据库路径必须位于用户 home 目录内。这个限制可以避免误写系统目录或共享目录。`db migrate` 的目标路径不能已经存在，`-wal`、`-shm`、`-journal` 等 sidecar 文件会随数据库一起移动。

## 清理覆盖范围

```bash
nber-cli feed clean --days 30
nber-cli feed clean --all
nber-cli info cache clear --days 30
nber-cli info cache clear --all
```

两个清理命令都会先显示预览，并在删除前要求确认。`feed clean` 只删除 `feed_items`。`info cache clear` 只删除 `info_cache`。日志表和 `feed_fetches` 需要手动 SQLite 维护，或换用新数据库。

## 备份

安全备份时，先关闭 Desktop，并停止正在运行的 CLI、MCP 或本地 HTTP server 进程，然后复制 `nber.db` 以及存在的 `nber.db-wal`、`nber.db-shm`。必须保持数据库在线时，可以使用 SQLite 备份命令：

```bash
sqlite3 ~/.nber-cli/nber.db ".backup '/path/to/nber-backup.db'"
```
