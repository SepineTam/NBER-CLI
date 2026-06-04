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

这些值位于 `NBERCLIConfig` 和 `NBER_CLI_CONFIG`。

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

`info.cache_ttl_days` 设置刷新间隔（天）。超过该阈值的缓存条目会被视为未命中，并在下一次 `info` 调用时重新拉取。必须是正整数。默认是 `30`。

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
