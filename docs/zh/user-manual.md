# 用户操作手册

本手册说明 NBER-CLI **0.10.0** 已发布代码的实际行为：Desktop 是研究者的日常入口，CLI/MCP 是 AI Agent 和自动化入口。如果手册与某个命令的 `--help` 不一致，以已安装版本的帮助输出为准。

## 1. 软件用途与使用者

NBER-CLI 用于跟踪 NBER 公开工作论文元数据、阅读摘要、整理本地论文 Feed、生成引用文字，并通过 Agent 接口获取 PDF。

| 使用者 | 推荐入口 | 是否需要开发工具 |
| --- | --- | --- |
| 研究者 | Desktop | 不需要 |
| 支持 MCP 的 AI Agent | MCP Server | 需要 `uvx` 或已安装的 Python 包 |
| 可以执行终端命令的 AI Agent | CLI | 需要 `uvx` 或已安装的 Python 包 |
| 应用开发者 | Python API 或可选 HTTP API | Python 3.11+ 及相应依赖 |

本项目独立于 NBER，不提供订阅、账号、凭据，也不能绕过 NBER 的访问限制。

## 2. 运行要求

### Desktop

- 从官方 GitHub Release 下载的 macOS arm64/x64、Windows x64 或 Linux x64 对应安装包。
- 同步 Feed 和准备论文元数据时可以访问 NBER。
- 手动检查更新时可以访问 GitHub Releases API；此项不是日常阅读的必要条件。
- 允许在用户 home 目录下创建文件，默认是 `~/.nber-cli/`。
- 窗口至少 920 × 620 px；初始窗口为 1120 × 760 px。

Desktop 已经包含工作程序运行环境，不要为了运行 Desktop 单独安装 Python。

### Agent 入口

- 直接安装 Python 包时需要 Python 3.11 或更高版本。
- 使用 `uvx`、`uv tool`、`pipx` 或 `pip`。
- MCP 模式需要支持 MCP 的客户端；CLI 模式需要能够执行终端命令。

## 3. 安装并启动 Desktop

1. 打开[最新官方 Release](https://github.com/sepinetam/nber-cli/releases/latest)。
2. 选择与操作系统和 CPU 架构一致的安装包。
3. 按操作系统的正常流程安装。
4. 如果系统提示发布者未知，先确认来源再决定是否放行；准确操作见 [Desktop 指南](desktop.md#_2)。
5. 启动 **NBER-CLI Desktop**。

首次启动时，Desktop 会把支持的默认值写入 `~/.nber-cli/config.json`，并校验配置中已经存在的数据库。如果数据库尚不存在，第一次成功执行“同步最新论文”时才会创建数据库和 schema。Desktop 不会启动本地服务器。

## 4. 界面区域

| 区域 | 用途 |
| --- | --- |
| 左侧导航 | 在论文 Feed 与设置之间切换，并显示本地数据是否就绪。 |
| Feed 标题区 | 显示本地论文数量和最近一次成功同步时间。 |
| 搜索与筛选 | 按文字、已读状态或可见标签筛选已加载记录。 |
| 论文列表 | 显示本地 Feed，并继续加载下一页本地记录。 |
| 详情区 | 显示元数据、摘要、标签、已读控制、引用控制和 NBER 页面入口。 |
| 设置页 | 修改刷新间隔和详情字号，查看本地路径，手动检查更新。 |

## 5. 第一次同步

**前提：** Desktop 已打开，并且可以访问 NBER。

1. 打开 Feed 页面。
2. 点击“同步最新论文”。
3. 等待刷新状态结束。
4. 阅读完成提示。

**预期结果：** Feed 保存到 SQLite，提示显示新增数量和详情准备数量，列表从本地数据重新加载。`info.cache_enabled` 为 false 时，准备数量保持为零，并跳过元数据预取。

**本地副作用：** `feed_items`、`feed_fetches`、`info_cache` 和 Desktop 原始标签同步表可能新增或更新记录；不会下载 PDF。

## 6. Desktop 日常操作

| 任务 | 操作 | 预期结果 | 持久化影响 |
| --- | --- | --- | --- |
| 查找已加载论文 | 在搜索框输入标题、作者、编号或标签。 | 只保留匹配的已加载记录。 | 无。 |
| 查看未读论文 | 选择“未读”。 | 隐藏已加载的已读记录。 | 无。 |
| 按标签筛选 | 选择一个可见标签。 | 只保留带该标签的已加载记录。 | 无。 |
| 阅读详情 | 选择一条 Feed。 | 右侧打开缓存元数据。 | 自动标记已读。 |
| 修改已读状态 | 点击眼睛按钮。 | 列表和详情状态更新。 | 更新 `read_status`。 |
| 添加标签 | 输入标签并点击“添加”。 | 标签显示在详情和 Feed 中。 | 更新 `desktop_user_tags`。 |
| 编辑来源标签 | 编辑 Topic/Program 标签。 | 本机隐藏原标签，以用户标签显示新文字。 | 更新来源隐藏表和用户标签表。 |
| 删除标签 | 点击删除按钮。 | 删除用户标签，或在本机隐藏来源标签。 | 更新 Desktop 标签表。 |
| 复制引用 | 选择格式并点击复制。 | 引用文字进入剪贴板。 | 无。 |
| 打开来源页面 | 点击“NBER 页面”。 | 系统浏览器打开公开论文 URL。 | 无。 |
| 加载更多 | 点击“加载更多”。 | 追加下一页本地记录。 | 无。 |

Desktop 搜索是本地筛选，只处理已经加载到列表中的记录。AI Agent 需要远程查询 NBER 时，应使用 CLI `search` 或 MCP `search_papers`。

## 7. 阅读控制

- 拖动详情分隔条可在 360 至 640 px 之间调整宽度。
- 双击分隔条恢复 420 px。
- 分隔条获得焦点后可使用 Left/Right、Shift+Left/Right、Home 或 End。
- 在设置中选择 14、16 或 18 px 的论文详情字号。
- `Command/Ctrl+F` 或 `Command/Ctrl+K` 聚焦 Feed 搜索。
- `Command/Ctrl+R` 同步，`Command/Ctrl+1` 返回 Feed。

分隔条宽度保存在 WebView local storage；其他 Desktop 设置保存在 `config.json`。

## 8. 配置自动刷新

1. 打开“设置”。
2. 输入一个正整数分钟数。
3. 选择论文详情字号。
4. 点击“保存设置”。

只有 Desktop 已打开、本地初始化成功、页面可见且当前没有刷新任务时，自动刷新才会运行。它不是操作系统后台服务。

## 9. 给 AI Agent 使用

### MCP

把 Agent 配置为运行：

```bash
uvx nber-cli mcp-server
```

Agent 会得到 `get_paper_info`、`search_papers` 和 `download_paper` 三个工具。0.10.0 对 MCP 下载路径执行的是工作目录字面检查，不是安全沙箱；请把 server 运行在隔离的工作目录中，并使用简单的相对文件名。参数和返回对象见 [MCP Server](mcp.md)。

### CLI

可以执行终端命令的 Agent 可使用：

```bash
uvx nber-cli search "minimum wage" --format json
uvx nber-cli info w25000 --format json
uvx nber-cli download w34567
```

CLI 还可以管理 Feed、缓存、配置、数据库路径和诊断信息。准确选项见 [CLI 参考](cli.md)。普通研究者使用 Desktop 时不需要执行这些命令。

## 10. 数据、备份与恢复

默认数据位置：

| 数据 | 默认位置 |
| --- | --- |
| 共用配置 | `~/.nber-cli/config.json` |
| 共用 SQLite 数据库 | `~/.nber-cli/nber.db` |
| CLI 轮转诊断日志 | `~/.nber-cli/debug.log` |
| Desktop 诊断目录 | `~/.nber-cli/logs/` |
| 详情区宽度 | WebView local storage |

进行文件级备份时，应关闭所有使用该数据库的 Desktop、CLI、MCP 和 HTTP 进程。如果存在 `nber.db-wal` 和 `nber.db-shm`，应与 `nber.db` 一起复制。在线数据库请使用[持久化层](persistence.md)说明的 SQLite `.backup` 命令。

如果 `config.json` 损坏，Desktop 会停止，不会自动替换。请恢复已知可用的配置或修复 JSON。如果数据库 schema 比应用支持的版本更新，应安装新版 Desktop，不要强迫旧版写入。

## 11. 更新与卸载

Desktop 不会自动更新。在设置中点击“检查更新”；发现新版本后，打开官方 Release，关闭 Desktop，再覆盖安装匹配的安装包。

卸载步骤：

1. 关闭 Desktop，并停止 CLI/MCP/HTTP 进程。
2. 通过操作系统删除应用程序。
3. 如果以后还要使用本地论文库，保留 `~/.nber-cli/`。
4. 只有确定不再需要数据库、标签、设置、缓存和日志时，才单独删除 `~/.nber-cli/`。

没有备份时，删除数据目录无法恢复。

## 12. 已知边界

- Desktop 浏览已经同步的 Feed，不提供 NBER 远程全文检索界面。
- Desktop 能打开 NBER 页面，但没有应用内 PDF 下载按钮。
- 引用根据现有元数据生成，正式使用前必须核对。
- Desktop 标签只保存在本机，不会修改 NBER。
- 更新检查和安装都需要手动执行。
- 当前公开安装包可能没有签名。
- NBER 的来源页面、搜索端点和 PDF 可能不可用、受限或发生变化。
- 非 stdio MCP 传输和可选 HTTP API 在暴露到本机以外前，必须单独评估网络安全。

## 13. 验收检查

安装或升级后确认：

- Desktop 能打开，且没有启动本地服务器。
- Feed 刷新成功，或返回可理解的网络错误且不删除已有记录。
- 论文能从本地数据打开，并可标记已读/未读。
- 可以添加、编辑和删除一个本地标签。
- 至少一种引用格式可以复制文字。
- 刷新间隔和字号在重启后保留。
- 手动检查更新能返回版本结果，或给出可理解的 GitHub 连接错误。

开发者还应运行[测试](testing.md)和[开发指南](development.md)中的仓库检查。
