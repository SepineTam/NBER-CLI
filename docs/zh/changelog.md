# 更新日志

这里记录项目的重要变更。

本页是仓库根 `CHANGELOG.md` 的中文镜像，英文镜像在 `docs/en/changelog.md`。每次发布提交都会同步更新三份内容。

## 未发布

### 修复

- `feed fetch` 现在可以容忍 RSS 标题和摘要文本中后接空白或数字的未转义 `<`，其他格式错误仍使用严格 XML 解析。
- RSS 解析失败时会在可用情况下报告行号和列号；`feed fetch` 的运行时解析错误会以退出码 `1` 返回，不再打印命令 usage。

## 0.4.0 - 2026-06-04

### Added

- 新增 `nber-cli info --refresh`，跳过本地 `info_cache` 并直接从 NBER 重新拉取论文元数据。缓存开启时，新数据会写回缓存。
- 新增 `nber-cli info cache --turn-on` 和 `--turn-off`，全局开关 `info_cache` 读取行为，状态会持久化到 `~/.nber-cli/config.json`。
- 新增 `nber-cli info cache --set-refresh <N>`，设置缓存刷新间隔（天）。该值会持久化到 `~/.nber-cli/config.json`，并在后续每次 `info` 调用中作为 TTL 生效，默认 `30` 天。
- 新增 `nber-cli info cache clear`，参数集与 `feed clean` 一致：`--days`、`--all`、`--start-date`、`--end-date`，使用 `info_cache` 表的 `last_fetched_at` 字段过滤。`nber-cli info cache clean` 是 `clear --all` 的便利别名。
- 新增 `nber-cli info cache`（不带子动作），用于打印当前缓存状态、TTL 和已缓存行数。
- 新增 `nber_cli.config_store` 模块，集中处理 `~/.nber-cli/config.json` 的读写，包含 `InfoCacheSettings` 数据类及 `get_info_cache_settings`、`set_info_cache_enabled`、`set_info_cache_ttl_days` 等辅助函数。
- 新增 `nber_cli.info_cache.get_paper_with_info_cache_result` 异步辅助函数（位于 `nber_cli.info_cache` 模块），返回包含 `NBER` 论文对象和 `from_cache` 标志的 `InfoCacheLookupResult`。
- 新增包顶层的 Python API 导出：`InfoCacheSettings`、`clear_info_cache`、`count_info_cache`、`get_info_cache_settings`、`get_info_cache_ttl_days`、`is_info_cache_enabled`、`is_info_cache_expired`、`set_info_cache_enabled`、`set_info_cache_ttl_days`、`NBERInfoCacheClearResult`。`InfoCacheLookupResult` 和 `get_paper_with_info_cache_result` 由 `nber_cli.info_cache` 模块导出，而不是从包顶层；导入路径是 `from nber_cli.info_cache import ...`。

### Changed

- `~/.nber-cli/config.json` 现在携带 `info` 段：`info.cache_enabled`（默认 `true`）和 `info.cache_ttl_days`（默认 `30`）。字段缺失或类型错误时回退到默认值。
- `info` 命令在从本地缓存命中时，会通过 stderr 打印一行提示，并指向 `nber-cli info <id> --refresh` 用于强制刷新。

## 0.3.1 - 2026-06-03

### Added

- 添加 `nber-cli db init` 和 `nber-cli db migrate`，用于初始化和迁移本地数据库，替代原先的 `feed init` 和 `feed migrate`。
- 添加 `info_cache` 表，重复执行 `nber-cli info` 或 MCP `get_paper_info` 时直接从缓存返回。
- 添加 `query_log`、`download_log`、`info_log` 表，记录搜索关键词、下载结果和 info 查询。
- 在 `~/.nber-cli/config.json` 中写入 `schema_version` 字段，便于后续的 schema 升级。

### Changed

- 默认数据库文件从 `feed.db` 改名为 `nber.db`。已经安装了 `~/.nber-cli/feed.db` 的用户无需手动迁移。
- 数据库 schema 从版本 1 升级到版本 2，下次启动时自动完成升级。
- 公共数据库代码迁移到 `nber_cli.db`,原先的 `init_feed_database` 和 `migrate_feed_database` 作为薄薄的兼容层保留。

## 0.3.0 - 2026-06-03

### Added

- 添加 `nber-cli feed init`，用于创建本地 SQLite feed 缓存。
- 添加 `nber-cli feed fetch`，用于获取 NBER 最新工作论文 RSS feed 并显示新缓存的条目。
- 添加 `nber-cli feed fetch --max-items`，用于限制 feed 输出数量。
- 添加 `nber-cli feed migrate`，用于移动 feed 缓存数据库并更新用户配置。
- 添加 `nber-cli feed clean`，用于在确认后清理 feed 缓存数据库记录。
- 补充 feed 缓存辅助函数和 feed 数据模型的 Python API 文档。

### Changed

- 添加 `~/.nber-cli/config.json` 和 `feed.db-path` 的用户配置文档。
- 扩展中英文 CLI、快速开始、配置和 Python API 页面中的 feed 缓存文档。

## 0.2.0 - 2026-05-31

### Changed

- 将 CLI 重构为 `nber-cli download ...` 子命令语法。
- 添加 `--file/-f` 和 `--save-base/-s` 路径处理行为。
- 添加 `--batch/-b` 多编号下载模式。
- 移除基于数据库的下载状态跟踪。
- 将下载器简化为直接异步 HTTP PDF 获取。
- 更新 v0.2 命令模型文档。
- 移除旧 web UI 模块和脚本入口。

## 0.1.4 - 2025-08-09

### Added

- 添加 `--version` / `-v` 参数用于显示当前版本。
- 添加更完整的帮助信息和示例。
- 添加 `__main__.py` 以支持 `python -m nber_cli`。
- 添加参数分组以改善 CLI 结构。
- 不带参数运行时自动显示帮助信息。
