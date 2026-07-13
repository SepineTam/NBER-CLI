# Desktop 应用

NBER-CLI Desktop 提供一个本地论文工作台，用来追踪新发布的 NBER 工作论文。安装包已经内置 Python HTTP sidecar，不需要用户另行安装 Python；配置、数据库和日志都保存在本机。

## 选择安装包

只从项目的 [GitHub Releases](https://github.com/sepinetam/nber-cli/releases) 页面下载安装包。

| 平台 | 安装包标识 | 适用设备 |
| --- | --- | --- |
| macOS Apple 芯片 | `macOS-arm64.dmg` | M 系列芯片 Mac |
| macOS Intel | `macOS-x64.dmg` | Intel 芯片 Mac |
| Windows | `Windows-x64.exe` | 64 位 Windows |

目前不提供 Linux 安装包。Desktop 与 Python 包使用同一版本号，并发布在同一个 GitHub Release 中。

## 未签名版本说明

项目目前没有付费的 Apple 和 Windows 证书，因此 Desktop 安装包尚未进行代码签名或 macOS notarization。首次启动时，macOS Gatekeeper 或 Windows SmartScreen 可能显示警告。系统出现警告并不代表文件一定安全。

决定继续运行前，请先确认：

1. 安装包来自官方 `SepineTam/NBER-CLI` GitHub Release。
2. 文件名、版本、平台和 CPU 架构与所选 Release 一致。
3. 如果文件来自镜像、聊天附件或其他不可信来源，不要绕过警告。

macOS 首次拦截后，可以进入**系统设置 → 隐私与安全性**；只有完成上述检查后，才使用**仍要打开**。Windows SmartScreen 中也只有在确认文件可信后，才展开**更多信息**并选择**仍要运行**。

## 首次启动会发生什么

Desktop 会启动一个只监听 `127.0.0.1` 的本地 HTTP 服务，然后读取本地 feed 数据库。如果数据库中没有 feed 条目，应用会自动请求当前的 NBER RSS feed。

以下本地文件或目录可能被创建或更新：

| 路径 | 用途 |
| --- | --- |
| `~/.nber-cli/config.json` | Desktop 端口与自动刷新间隔 |
| `~/.nber-cli/nber.db` | Feed、论文元数据缓存、日志与已读状态 |
| `~/.nber-cli/logs/sidecar.stdout.log` | 本地服务标准输出 |
| `~/.nber-cli/logs/sidecar.stderr.log` | 本地服务错误与诊断信息 |

正常退出 Desktop 时，本地服务会随之停止。

!!! warning "当前数据库路径限制"
    Desktop 0.8.0 启动 sidecar 时固定使用 `~/.nber-cli/nber.db`，暂时不会读取 `nber-cli db migrate` 产生的自定义 `feed.db-path`，启动时还可能把默认路径写回 `config.json`。如果你使用自定义或旧版数据库路径，请在打开 Desktop 前备份配置和数据库。

## 主要功能

- **刷新 Feed**：获取最新 NBER 工作论文 RSS 条目。
- **打开论文**：加载论文元数据，并把它标记为已读。
- **标记已读或未读**：状态保存在本地 `read_status` 表。
- **在 NBER 打开**：用系统浏览器访问 NBER 论文页面。
- **复制引用**：支持 BibTeX、APA、MLA、Harvard、Chicago 和 GB/T 7714。
- **加载更多**：分页查看本地缓存的 Feed 条目。

论文元数据未命中缓存时，打开论文会向 NBER 发起网络请求。应用不会自动下载 PDF。

## 设置

设置页提供：

- **本地服务端口**：默认 `31527`，有效范围 `1024`–`65535`；修改后需要重启 Desktop。
- **Feed 刷新间隔**：默认 `60` 分钟。只有应用正在运行、本地服务正常且窗口可见时才会自动刷新。
- **本地路径**：显示数据库与配置文件位置，并可打开 sidecar 日志目录。

所有配置都保留在本机。完整说明见[配置](configuration.md)和[持久化层](persistence.md)。

## 故障排查

| 现象 | 检查方法 |
| --- | --- |
| 本地服务不可用 | 确认设置的端口没有被其他程序占用，然后重启 Desktop。 |
| Feed 为空 | 检查能否访问 `nber.org`，然后点击刷新。 |
| 论文详情加载失败 | 论文可能已移除、受限或暂时不可用；检查 sidecar 日志。 |
| 修改端口后没有变化 | 端口在重启 Desktop 后生效。 |
| 找不到预期的自定义数据库 | 查看上面的数据库路径限制；当前 Desktop 固定使用默认数据库。 |

日志位于 `~/.nber-cli/logs/`。其中可能包含错误细节和本地路径，分享前请先检查内容。

## 升级、备份与卸载

Desktop 目前不会自动更新。请从官方 GitHub Release 下载新版本安装包，并覆盖安装现有应用。

备份或删除本地数据前，先关闭 Desktop，并停止单独运行的 `nber-server` 或 MCP 进程。备份 `nber.db` 时，如果存在 `nber.db-wal` 和 `nber.db-shm`，也要一起保存。在线 SQLite 备份命令见[持久化层](persistence.md#_6)。

卸载应用不会自动删除 `~/.nber-cli`。只有在确认不再需要配置、数据库、日志和阅读历史后，才单独删除这个目录。
