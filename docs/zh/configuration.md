# 配置

NBER-CLI 的大多数运行时行为使用内置默认值。本地数据库还会使用一个小型用户配置文件，用来记住 `nber-cli db init` 或 `nber-cli db migrate` 选择的 SQLite 数据库路径。

## 运行时默认值

| 设置 | 默认值 | 说明 |
| --- | --- | --- |
| 请求超时 | `60` 秒 | 网络请求的总超时时间。 |
| 重试次数 | `3` | 合适的失败请求会在暴露错误前重试。 |
| 请求尝试次数 | `4` | 由重试次数加首次请求得出。 |
| 下载连接上限 | `100` | 最大并发下载连接数。 |
| 单 host 连接上限 | `10` | 对同一 host 的最大并发连接数。 |
| 搜索分页大小 | `20`、`50`、`100` | `--per-page` 接受的值。 |

这些值位于 `NBERCLIConfig` 和 `NBER_CLI_CONFIG`。它们是**编译期常量**：既不会写入 `~/.nber-cli/config.json`，也没有对应的环境变量，也不能通过 CLI 参数修改。要调整这些值必须修改源码并重新安装包。

如果你在运行时需要不同的网络行为，目前支持的做法是直接调用 Python API，并传入自定义的 `aiohttp.ClientSession`（或 `aiohttp_retry.RetryClient`），把超时、连接器限制和重试策略设置为你需要的值。包自带的 retry 客户端和连接器只有在函数自己创建 session 时才会使用。

## 目前可以配置的项

下面的清单是完整的——没有列在这里的都是常量。

| 入口 | 可配置？ | 位置 |
| --- | --- | --- |
| `info.cache_enabled` | 是 | `~/.nber-cli/config.json`；用 `nber-cli info cache --turn-on/--off` 切换 |
| `info.cache_ttl_days` | 是 | `~/.nber-cli/config.json`；用 `nber-cli info cache --set-refresh <N>` 设置 |
| `feed.db-path`（SQLite 路径） | 是 | `~/.nber-cli/config.json`；用 `nber-cli db init --db-path ...` 或 `nber-cli db migrate ...` 设置 |
| 请求超时 | **否** | `NBERCLIConfig` 中的代码常量 |
| 重试次数 / 请求尝试次数 | **否** | `NBERCLIConfig` 中的代码常量 |
| 下载连接上限 | **否** | `NBERCLIConfig` 中的代码常量 |
| 单 host 连接上限 | **否** | `NBERCLIConfig` 中的代码常量 |
| 搜索分页大小 | **否** | `NBERCLIConfig` 中的代码常量 |
| User-Agent 字符串 | **否** | 每次请求由 `fake_useragent.UserAgent` 生成 |
| HTTP 请求头（除 UA 外） | **否** | 硬编码在 download 模块中 |

## 用户配置文件

用户配置文件路径是：

```text
~/.nber-cli/config.json
```

当前结构：

```json
{
  "schema_version": 2,
  "feed": {
    "db-path": "/Users/name/.nber-cli/nber.db"
  },
  "info": {
    "cache_enabled": true,
    "cache_ttl_days": 30
  }
}
```

`feed.db-path` 指向 `info`、`search`、`download` 和 `feed` 都会使用的 SQLite 数据库。`feed` 这个 key 名称保留以保持向后兼容，数据库本身是通用的。

`schema_version` 记录当前数据库 schema 的版本。NBER-CLI 在 `db init` 或 schema 升级后更新该字段。

`info.cache_enabled` 全局控制 `info_cache` 的读取行为。设为 `false` 时，每次 `info` 调用（以及 MCP `get_paper_info` 工具）都会直接访问 NBER。默认是 `true`。

`info.cache_ttl_days` 设置刷新间隔（天）。该 TTL 是**滑动**的：每次缓存命中都会通过 `touch_info_cache` 更新对应行的 `last_fetched_at` 并把 `fetch_count` 加 1，所以被反复查询的论文，其缓存副本会从“最近一次命中”起继续保留至少 `cache_ttl_days` 天。`last_fetched_at` 早于 TTL 阈值的缓存条目会被视为未命中，并在下一次 `info` 调用时重新拉取。必须是正整数。默认是 `30`。

两个 `info` 字段由 `nber-cli info cache --turn-on/--off/--set-refresh <N>` 维护。字段缺失或类型错误时一律回退到默认值，不会导致 NBER-CLI 失败。

## 本地数据库

默认数据库路径：

```text
~/.nber-cli/nber.db
```

初始化默认数据库：

```bash
nber-cli db init
```

初始化到自定义路径：

```bash
nber-cli db init --db-path ~/data/nber.db
```

移动已有数据库并更新配置：

```bash
nber-cli db migrate ~/data/nber.db
```

如果你从 0.3.0 升级过来,本地还存有 `~/.nber-cli/feed.db`,在没有 `nber.db` 的情况下 NBER-CLI 会继续使用这个旧文件。首次运行时会自动完成 schema 升级。

数据库包含以下内容：

- `feed_items` 和 `feed_fetches`：`feed fetch` 和 `feed clean` 使用的 RSS 缓存。
- `info_cache`：`info` 和 MCP `get_paper_info` 工具使用的论文元数据缓存。读取行为受 `info.cache_enabled` 控制，并受 `info.cache_ttl_days` 的 TTL 约束。
- `query_log`、`download_log`、`info_log`：搜索关键词、下载结果和 info 查询的行为日志。

## 数据库操作

数据库会在首次运行任何触及它的命令时自动创建并完成 schema 升级。`info`、`search`、`download` 和 `feed` 的使用者**不必**先执行 `nber-cli db init`；该命令的存在是为了让调用方可以预创建文件或指定非默认路径。`db init` 执行后（或首次成功运行后），schema 版本会写入 `~/.nber-cli/config.json` 的 `schema_version` 字段。

### 表参考

| 表 | 写入入口 | 读取入口 | 清理方式 |
| --- | --- | --- | --- |
| `feed_items` | `feed fetch` | `feed fetch`（`display_all=False` 时只取新条目） | `feed clean`（需要确认） |
| `feed_fetches` | `feed fetch` | 暂无 | 无 |
| `info_cache` | `info` 和 `get_paper_info`（缓存开启时） | `info` 和 `get_paper_info` | `info cache clear`（需要确认） |
| `query_log` | `search` | 暂无 | 无 |
| `download_log` | `download`（单篇和批量） | 暂无 | 无 |
| `info_log` | `info` 和 `get_paper_info` | 暂无 | 无 |

### CLI 与 MCP 写入差异

- CLI 与 MCP `get_paper_info` 在缓存开启时都会写 `info_log` 与 `info_cache`。CLI 在缓存命中时会额外向 stderr 输出单行提示，MCP 不会。
- `feed fetch` 在两种入口下行为一致；当前 MCP 层尚未暴露该命令。
- 只有 CLI 会写 `query_log`（通过 `search`）和 `download_log`（通过 `download`）。当前版本的 MCP `search_papers` 和 `download_paper` 工具**不**写这两张表。

### 迁移与重置

`nber-cli db migrate <new_db_path>` 把数据库移至新路径，包括所有 SQLite `-wal`、`-shm`、`-journal` sidecar 文件，并更新用户配置中的 `feed.db-path`。目标路径不能已经存在；该命令会拒绝覆盖现有文件。

目前没有“直接清空数据库”的内建命令。可行的重置方式有：

- 用 `nber-cli db migrate` 把现有文件移走，或
- 停止 CLI 后直接删除 `nber.db`（以及 sidecar 文件），再用 `nber-cli db init` 指向新路径。

### 备份

数据库就是单个 SQLite 文件加它的 sidecar 文件。要安全备份：

1. 先停止任何可能持有写事务的 `nber-cli` 或 MCP server 进程。
2. 把 `nber.db` 以及 `nber.db-wal`、`nber.db-shm`（存在时）一起复制到备份位置。
3. 也可以在不停止 CLI 的情况下使用 `sqlite3 nber.db ".backup '<backup_path>'"` 拿到一个崩溃一致的快照，这是面向在线系统的推荐做法。

### 当前的清理覆盖

- `feed clean` 只删除 `feed_items` 表中的行。`feed_fetches` 是持续累积的审计日志，**不会**被 `feed clean --all` 清理。修剪它需要手动 `DELETE FROM feed_fetches WHERE ...`，或直接用 `sqlite3` 操作。
- `info cache clear` 只删除 `info_cache` 表中的行，`info_log` 不会被清理。
- `query_log`、`download_log`、`info_log` 目前**没有**对应的 CLI 清理命令。唯一能清空它们的途径是 `nber-cli db migrate` 到新数据库、手动 `sqlite3` 操作，或直接删除 `nber.db`。

## 输出路径

单篇下载默认行为：

```bash
nber-cli download w34567
```

创建：

```text
./w34567.pdf
```

按目录下载：

```bash
nber-cli download w34567 --save-base ~/papers/nber
```

创建：

```text
~/papers/nber/w34567.pdf
```

明确文件下载：

```bash
nber-cli download w34567 --file ~/papers/custom-name.pdf
```

会创建你指定的路径，并在可能时创建父目录。

## 日期筛选

搜索日期使用 `YYYY-MM-DD`。

```bash
nber-cli search "trade" --start-date 2024-01-01 --end-date 2024-12-31
```

如果只提供 `--start-date` 而没有提供 `--end-date`，NBER-CLI 会使用当前日期作为结束日期。

## 网络行为

NBER-CLI 会发送类似浏览器的 user agent，对临时失败进行重试，并为常见下载失败返回可读错误：

- HTTP 403 可能表示新发布论文仍处于 NBER 第一周访问限制中。
- HTTP 404 表示找不到论文 PDF。
- 超时和连接失败会报告为网络错误。

## 不需要凭据

NBER-CLI 不需要 API key。它使用公开的 NBER 网页和公开的工作论文搜索端点。
