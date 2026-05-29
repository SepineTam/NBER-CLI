# 配置

NBER-CLI 当前使用内置运行时默认值，而不是用户配置文件。这些默认值刻意保持保守，适合 CLI 和 MCP 两种用法。

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
