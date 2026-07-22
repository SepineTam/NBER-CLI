# 术语表

## NBER 论文编号

类似 `w25000` 的工作论文编号。多数面向用户的命令同时接受带 `w` 和不带 `w` 的形式，但 URL 和默认 PDF 文件名使用带 `w` 前缀的规范形式。

## CLI

由 `src/nber_cli/cli.py` 实现的 `nber-cli` 命令。它面向人和脚本：默认输出文本，在支持的地方输出 JSON，并在失败时使用稳定的非零退出码。

## MCP Server

由 `src/nber_cli/mcp/mcp.py` 基于 FastMCP 实现的 Agent 入口。它暴露三个工具：`get_paper_info`、`search_papers` 和 `download_paper`。

## Info Cache

`info_cache` 表和 `info_cache.py` 中的辅助流程。它保存论文元数据，使重复的 `info` 和 `get_paper_info` 调用在 TTL 内可以避免再次访问 NBER 页面。

## 滑动 TTL

Info cache 的刷新模型。缓存命中时，NBER-CLI 会更新 `last_fetched_at` 并递增 `fetch_count`，所以过期时间按最近一次本地命中计算，而不只按最初的网络拉取计算。

## Feed System

`feed.py` 中的 RSS 流程。它读取 `https://www.nber.org/rss/new.xml`，用 `defusedxml` 解析条目，存入 `feed_items`，并根据命令选项返回新条目或全部条目。

## 本地数据库

由 `db.get_database_path()` 解析得到的 SQLite 数据库。默认位置是 `~/.nber-cli/nber.db`。它保存 Feed 与元数据缓存、已读状态、行为日志和四张 Desktop 标签表。

## 配置文件

位于 `~/.nber-cli/config.json` 的 JSON 文件。它保存数据库路径、数据库 schema 版本、info cache 与下载设置，以及 Desktop 刷新间隔和详情字号。

## SQLModel

`db.py` 使用的类型化 ORM 层，底层建立在 SQLAlchemy 之上。`FeedItem`、`InfoCache`、`QueryLog`、`DownloadLog` 和 `InfoLog` 等表都用 SQLModel model 声明。

## 行为日志

记录本地操作事件的表：

- `query_log` 记录 CLI 搜索关键词和结果数量。
- `download_log` 记录 CLI 下载结果。
- `info_log` 记录 CLI 和 MCP 的论文信息查询。

这些日志不会发送到项目服务器。

## 软失败

不会打断主操作的非关键数据库写入失败。例如 `query_log` 写入失败不应阻止搜索结果打印。

## 下载限制

当前用于下载目标的工作目录字面检查。CLI 默认启用，可用 `--restrict false` 关闭；MCP 始终启用。0.10.0 不会解析 `..` 或符号链接，因此该检查不是安全沙箱。

## `display_all`

Feed fetch 选项。为 false 时，`feed fetch` 只显示新发现的 RSS 条目。为 true 时，显示本次获取到的全部 RSS 条目，包括缓存中已经存在的条目。

## `include_all`

MCP `get_paper_info` 的选项。为 true 时，返回字典会包含相关字段，并在 NBER 提供时包含 `published_version`。

## `--refresh`

CLI `info` 标志。它会在本次调用中跳过本地 info cache，重新从 NBER 获取论文页面。MCP 当前没有等价的逐次调用参数。

## 第一周访问限制

NBER 可能对新发布论文返回 HTTP 403，表示它暂时还不能公开下载。NBER-CLI 会把它报告为权限/访问问题，而不是论文不存在。

## 未来 Schema

SQLite `PRAGMA user_version` 高于当前已安装 NBER-CLI 支持版本的数据库。包会拒绝写入这类数据库，以避免旧版本程序破坏新结构。
