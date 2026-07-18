# Desktop 应用

NBER-CLI Desktop 是用于追踪 NBER 新工作论文的本地研究工作台。从 0.9.1 开始，安装包内置一个由现有 Python CLI 代码打包而成的单次工作程序。用户无需安装 Python 或 uv，Desktop 也不会启动本地 Web 服务或长期运行的 sidecar。

## 下载哪个安装包

只从项目官方 [GitHub Releases](https://github.com/sepinetam/nber-cli/releases) 页面下载安装包。

| 平台 | 文件标识 | 适用设备 |
| --- | --- | --- |
| macOS Apple silicon | `macOS-arm64.dmg` | M 系列芯片 Mac |
| macOS Intel | `macOS-x64.dmg` | Intel 芯片 Mac |
| Windows | `Windows-x64.exe` | 64 位 Windows |
| Linux | `Linux-x64.AppImage` 或 `.deb` | 64 位 Linux 桌面 |

Desktop 与 Python 包使用同一个版本号，并发布在同一个 GitHub Release 中。

## 未签名提示

项目目前没有付费的 Apple 和 Windows 证书，因此安装包没有代码签名或 macOS notarization。macOS Gatekeeper 或 Windows SmartScreen 可能在首次启动时警告。

放行前，请确认文件来自官方 `SepineTam/NBER-CLI` Release，并检查版本、系统和 CPU 架构是否匹配。不要运行来自镜像、聊天附件或其他不可信来源的文件。

## 首次启动与本地数据

Desktop 会打开配置中的本地数据库。首次启动时，内置工作程序会初始化与 CLI 相同的数据库结构。

| 路径 | 用途 |
| --- | --- |
| `~/.nber-cli/config.json` | 数据库路径、缓存设置和自动刷新间隔 |
| `~/.nber-cli/nber.db` | Feed、论文缓存、历史记录和已读/未读状态 |
| `~/.nber-cli/logs/` | 本地诊断目录；不会生成长期运行的 sidecar 日志 |

Desktop 会读取 CLI 共享配置中的 `feed.db-path`，因此 `nber-cli db migrate` 设置的自定义数据库可直接使用。在 macOS 和 Linux 上，路径必须位于用户 home 目录内。

如果 `config.json` 无法解析，Desktop 会报错并停止，不会用默认值覆盖原文件。修复或恢复配置后再打开应用。

## 主要操作

- **刷新 Feed**：为这一次操作启动内置工作程序，直接调用现有 Python `fetch_feed`，更新数据库后立即退出。
- **打开论文**：在同一个单次工作程序中使用现有 Python 论文详情与缓存逻辑，然后由 Rust 标记为已读。
- **标记已读或未读**：直接更新共享数据库中的 `read_status` 表。
- **在 NBER 打开**：打开公开论文页面。
- **复制引用**：支持 BibTeX、APA、MLA、Harvard、Chicago 和 GB/T 7714。
- **加载更多**：从本地 Feed 缓存继续分页。

## 设置

设置页提供自动刷新间隔，以及配置、数据库和日志目录的位置。Desktop 已不再运行本地 HTTP 进程，因此没有服务端口设置。只有在你主动运行可选的 `nber-server` 时，服务器端口配置才有意义。

## 故障排查

| 情况 | 怎么处理 |
| --- | --- |
| Feed 刷新失败 | 检查能否访问 `nber.org` 后重试；已有本地数据不会丢失。 |
| 论文详情加载失败 | 论文可能被移除、受限或暂时不可用；Feed 摘要仍保存在本地。 |
| 找不到自定义数据库 | 检查 `~/.nber-cli/config.json` 中的 `feed.db-path`；macOS/Linux 下必须在 home 目录内。 |
| 提示数据库版本更高 | 升级 Desktop；旧版本会拒绝写入较新的数据库结构。 |

Desktop 不会自动安装更新。请从官方 GitHub Release 下载新版本并覆盖安装。

备份或删除本地数据前，先关闭 Desktop，并停止单独运行的 CLI、MCP 或 HTTP 进程。如果存在 `nber.db-wal` 和 `nber.db-shm`，备份 `nber.db` 时也要一起保存。在线备份方法见[持久化层](persistence.md#_6)。
