# 更新日志

这里记录项目的重要变更。

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

## 0.2.0 - 2026-05-27

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
