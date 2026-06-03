# 配置

NBER-CLI 的大多数运行时行为使用内置默认值。feed 缓存还会使用一个小型用户配置文件，用来记住 `nber-cli feed init` 或 `nber-cli feed migrate` 选择的 SQLite 数据库路径。

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

目前配置文件用于 feed 缓存设置：

```json
{
  "feed": {
    "db-path": "/Users/name/.nber-cli/feed.db"
  }
}
```

`feed.db-path` 指向 `nber-cli feed fetch` 和 `nber-cli feed clean` 使用的 SQLite 数据库。

## Feed 缓存数据库

默认 feed 缓存数据库路径：

```text
~/.nber-cli/feed.db
```

初始化默认缓存：

```bash
nber-cli feed init
```

初始化到自定义路径：

```bash
nber-cli feed init --db-path ~/data/nber-feed.db
```

移动已有缓存并更新配置：

```bash
nber-cli feed migrate ~/data/nber-feed.db
```

feed 缓存会存储已经见过的 RSS 条目。`feed fetch` 使用这个缓存判断哪些条目是新的。`feed clean` 删除的是本地缓存记录；如果被删除的记录仍然出现在 RSS feed 中，后续可能会再次作为新条目被获取。

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
