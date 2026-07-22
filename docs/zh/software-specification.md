# 软件规格说明

本文记录 NBER-CLI **0.10.0** 的功能与技术基线，供维护、评审、版本证据留存和未来软件登记材料准备使用。内容只描述可以从本仓库追溯的行为；申请人身份、权属证明、源代码交存、软件截图和特定地区表格需要另行准备。

## 1. 软件标识

| 项目 | 基线 |
| --- | --- |
| 软件名称 | NBER-CLI |
| Desktop 产品名称 | NBER-CLI Desktop |
| 版本 | 0.10.0 |
| Python 包名 | `nber-cli` |
| Desktop 标识符 | `com.sepinetam.nber-cli-desktop` |
| 许可证 | Apache-2.0 |
| 开发状态 | Beta |
| 主要用户入口 | Desktop |
| AI 与自动化入口 | CLI 与 MCP Server |
| 其他集成入口 | Python API 与可选 loopback HTTP API |
| 默认本地数据根目录 | `~/.nber-cli/` |

NBER 是第三方注册商标。本项目是独立项目，不属于 NBER，也不是 NBER 官方认可的集成。

### 技术与环境概况

| 层次 | 基线技术或环境 |
| --- | --- |
| Desktop 界面 | TypeScript 5.8、React 18、Zustand 5、Vite 6 |
| Desktop 原生外壳 | Rust、Tauri 2、通过 `rusqlite` 使用 SQLite |
| 共用应用核心 | Python 3.11+、`aiohttp`、SQLModel/SQLAlchemy、`defusedxml` |
| Agent 接口 | Python MCP SDK / FastMCP |
| 可选本地集成 | FastAPI、Uvicorn、Alembic |
| 持久化格式 | JSON 配置、SQLite 数据库、PDF 下载文件、轮转文本日志 |
| 自动化验证 | Pytest、Vitest、TypeScript compiler、Cargo 测试、MkDocs strict 构建 |
| CI 基线 | Python 3.11、Node.js 20、stable Rust toolchain、`uv`、npm |
| 发布目标 | macOS arm64/x64、Windows x64、Linux x64 |
| 特殊硬件 | 除受支持的通用计算机和网络连接外，无特殊硬件要求 |

源代码行数、文件数量、构建主机版本和安装包校验值属于特定快照证据，不是永久产品属性。软件登记或审计时应从准确的发布 tag 重新计算并存档，不能从持续变化的开发分支复制数量。

## 2. 用途与范围

软件支持围绕 NBER 公开工作论文信息的本地研究流程：

1. 从 NBER 公开端点获取 Feed、搜索、元数据和 PDF 响应。
2. 将响应解析为结构化论文模型。
3. 在本机保存部分 Feed、元数据、已读状态、标签和操作数据。
4. 向研究者提供 Desktop 研究工作台。
5. 向 AI Agent 提供结构化 MCP 工具和可脚本化 CLI 命令。
6. 提供明确的 Python 与 loopback HTTP 集成接口。

### 不在当前范围内

- 托管或重新分发 NBER 论文库。
- 提供账号、订阅、凭据或绕过访问控制。
- 修改 NBER 来源记录，或把 Desktop 标签写回 NBER。
- 自动安装 Desktop 更新。
- 在 0.10.0 中提供 Desktop 远程搜索或应用内 PDF 下载流程。
- 保证第三方页面和端点始终完整或可用。

## 3. 参与者与入口

| 参与者 | 入口 | 主要目的 |
| --- | --- | --- |
| 研究者 | Desktop | 跟踪本地 Feed、阅读摘要、管理已读状态与标签、复制引用。 |
| AI Agent | MCP | 调用结构化搜索、查询和带路径检查的下载工具。 |
| AI Agent / 脚本 | CLI | 执行确定的命令并读取文本或 JSON。 |
| Python 开发者 | Python API | 复用异步获取、解析、下载、缓存和数据库函数。 |
| 本地应用 | HTTP API | 通过显式启动的 loopback JSON 服务使用 Feed、论文、已读状态和设置。 |
| 维护者 | 仓库工具 | 测试、构建、打包、校验和发布版本一致的产物。 |

## 4. 功能矩阵

“是”表示 0.10.0 的公开入口提供该能力；“内部”表示代码可供共用，但该入口没有把它作为用户命令或工具开放。

| 能力 | Desktop | CLI | MCP | HTTP API | Python API |
| --- | --- | --- | --- | --- | --- |
| 浏览已同步 Feed | 是 | 否 | 否 | 是 | 否 |
| 刷新 NBER Feed | 是 | 是 | 否 | 是 | 是 |
| 清理 Feed 缓存 | 否 | 是 | 否 | 否 | 是 |
| 远程搜索论文 | 否 | 是 | 是 | 否 | 是 |
| 获取论文元数据 | 查看本地缓存 | 是 | 是 | 是 | 是 |
| 强制刷新元数据 | 否 | 是 | 否 | 否 | 是 |
| 下载 PDF | 否 | 是 | 是 | 否 | 是 |
| 已读/未读状态 | 是 | 否 | 否 | 是 | 仅内部数据库包 |
| NBER 来源标签与本地标签 | 是 | 否 | 否 | 否 | 否 |
| 引用格式化 | 是 | 否 | 否 | 否 | 否 |
| 查看/修改配置 | 部分 Desktop 设置 | 是 | 否 | 部分 Server 设置 | 是 |
| 初始化/迁移数据库 | 第一次刷新时初始化 | 是 | 否 | 自动升级 | 是 |
| 诊断/版本修复 | 手动检查更新 | 是 | 否 | 健康检查 | 否 |

该矩阵用于防止把一个入口的实现错误宣传到另一个入口。新增功能时，应在同一版本中同步更新矩阵、接口参考、测试和更新日志。

## 5. 功能要求

| 编号 | 要求 | 主要验证方式 |
| --- | --- | --- |
| FR-01 | Desktop 应在不启动监听服务的前提下校验已有共用 schema-v3 SQLite 数据库；数据库不存在时，应在第一次成功刷新 Feed 时初始化。 | Desktop 运行、worker 与发布 smoke test。 |
| FR-02 | Desktop 应通过内置单次 Python 工作程序刷新 Feed，操作后退出该程序。 | Worker 与安装包测试。 |
| FR-03 | Feed 刷新应保存 Feed 并记录刷新；`info.cache_enabled` 为 true 时还应准备论文元数据，为 false 时跳过预取；结果应报告获取/新增/准备/失败数量。 | Python 与 Rust 测试。 |
| FR-04 | Desktop 应分页显示本地 Feed，并按已读状态、文字和可见标签筛选已加载记录。 | React 组件与页面测试。 |
| FR-05 | 打开论文应读取本地元数据并标记已读；手动修改已读状态应持久化。 | Tauri 数据库与前端 store 测试。 |
| FR-06 | Desktop 应分别保存 NBER 原始标签、用户标签和本机隐藏的原始标签。 | Rust 数据库测试。 |
| FR-07 | Desktop 应根据本地可用元数据复制六种支持的引用格式。 | 引用单元测试。 |
| FR-08 | Desktop 应保存刷新间隔和 14/16/18 px 字号，并在本机记住预览宽度。 | 配置、自动刷新和布局测试。 |
| FR-09 | CLI 应提供 download、info、search、db、feed、mcp-server、config 和 doctor 命令，以及有文档的退出/输出行为。 | CLI 测试与 `--help`。 |
| FR-10 | MCP 应提供 `get_paper_info`、`search_papers` 和 `download_paper`，规范化论文编号，并对下载执行文档说明的字面路径检查。 | MCP 测试。 |
| FR-11 | 可选 HTTP API 应默认绑定 loopback，并在 `/api/v1` 下返回已处理结果。 | Server 测试。 |
| FR-12 | 非关键行为日志或缓存写入失败，不应无必要地阻止主要获取、搜索或下载结果。 | 数据库与流程测试。 |
| FR-13 | 软件应准确公开当前下载路径检查及其 `..`/符号链接局限，并拒绝写入不支持的未来数据库 schema。 | 下载/数据库测试与文档评审。 |
| FR-14 | 中英文公开文档应描述同一发布行为和版本。 | MkDocs strict 构建与发布评审。 |

## 6. 核心流程

### Desktop Feed 流程

```text
用户刷新
  -> Tauri command
  -> 内置单次 worker
  -> Python 获取 Feed
  -> 仅在 info cache 开启时预取元数据
  -> 共用 SQLite 数据库
  -> Rust 同步原始标签
  -> React 重新读取分页本地记录
```

启动和日常打开论文都直接读取本地 SQLite，不会为每篇论文启动 worker。刷新时始终请求 NBER RSS；info cache 开启时还可能请求论文详情页面。

### Agent 查询流程

```text
Agent
  -> MCP tool 或 CLI command
  -> 共用 Python 获取/缓存函数
  -> 在适用时读写本地 SQLite 缓存和操作日志
  -> 结构化 dictionary/JSON 或可读文本
```

### 下载流程

```text
验证论文编号和目标路径
  -> 启用时执行字面路径检查
  -> 按重试策略请求 NBER PDF
  -> 写入文件
  -> 在适用时记录 CLI 行为日志
  -> 返回成功路径或可理解错误
```

## 7. 数据规格

### 共用文件

| 文件 | 内容 |
| --- | --- |
| `~/.nber-cli/config.json` | Schema 标记、数据库路径、缓存、下载和 Desktop 设置。 |
| `~/.nber-cli/nber.db` | 共用 schema-v3 SQLite 数据与 Desktop 扩展表。 |
| `~/.nber-cli/debug.log` | 轮转的 Python/CLI 警告、错误和可选 debug 记录。 |
| `~/.nber-cli/logs/` | Desktop 诊断目录。 |

### 共用 schema-v3 表

`feed_items`、`feed_fetches`、`read_status`、`info_cache`、`query_log`、`download_log` 和 `info_log` 由 Python 数据库层创建和管理版本。

### Desktop 扩展表

`desktop_raw_tags`、`desktop_user_tags`、`desktop_hidden_raw_tags` 和 `desktop_raw_tag_sync_state` 由 Desktop 幂等创建，不增加 `PRAGMA user_version`。这样可以保持 CLI schema v3 兼容，同时把 Desktop 专用标签状态分开保存。

准确字段、写入者、清理行为和备份规则见[持久化层](persistence.md)。

## 8. 配置与状态规则

- 共用持久化配置使用用户 home 目录下的 JSON。
- Desktop 支持正整数刷新间隔，以及 14、16、18 px 三档详情字号。
- 预览宽度是设备本机的 WebView 偏好，不进入共用 `config.json`。
- macOS 与 Linux 上，Desktop 数据库路径规范化后必须位于用户 home 目录内。
- Desktop 遇到损坏 JSON 时初始化失败，不会静默覆盖。
- CLI 配置读取对缺失或错误的受支持字段使用文档默认值；`config verify` 报告 schema 类型和范围错误。
- SQLite `PRAGMA user_version` 当前为 3；旧代码拒绝写入更新版本。

## 9. 外部依赖与边界

| 边界 | 行为 |
| --- | --- |
| NBER Web/Search/RSS/PDF 端点 | 第三方来源；网络、结构、可用性和访问政策可能变化。 |
| GitHub Releases API | Desktop 只在手动检查更新后访问。 |
| 本地文件系统 | 保存配置、数据库、日志和用户要求的下载文件。 |
| 剪贴板 | 用户明确执行 Desktop 复制操作后接收引用文字。 |
| 系统浏览器 | 用户明确操作后打开 NBER 或 GitHub 页面。 |
| MCP HTTP 传输 | 没有内置认证，必须限制在本地或由外部认证保护。 |
| 可选 HTTP API | 默认 loopback，Desktop 不使用它。 |

软件不需要项目 API Key 或用户凭据。应用代码不会把本地研究数据发送到项目方拥有的基础设施。

## 10. 非功能要求

### 安全与隐私

- CLI 默认启用文档所述的字面路径检查，MCP 始终启用；对不可信路径，应把操作系统隔离而不是该检查作为安全边界。
- 默认 Desktop 路径不开放监听服务。
- 保留损坏配置供手动恢复，不自动覆盖。
- 拒绝写入不支持的未来 schema。
- 分别保存来源标签、用户标签和隐藏偏好。

### 可靠性

- 对符合条件的网络失败执行重试。
- 必要的多步骤更新使用 SQLite 事务。
- 后续网络刷新失败时保留已有本地 Feed。
- 部分日志和缓存操作采用软失败。
- 校验 Desktop 安装包包含 worker，并拒绝旧的 HTTP sidecar。

### 易用性与可访问性

- CLI 默认输出可读文本，并在自动化需要的位置提供 JSON。
- Desktop 提供快捷键和可用键盘操作的分隔条。
- 主窗口可调整大小并设置最小支持尺寸。
- 显示可理解的错误与完成状态。

### 可移植性

- Python 包要求 Python 3.11+。
- Desktop 发布流程面向 macOS arm64/x64、Windows x64 和 Linux x64。
- 共用持久化数据采用 JSON 与 SQLite。

## 11. 源码追溯

| 模块或证据 | 仓库主要路径 |
| --- | --- |
| 包标识与依赖 | `pyproject.toml` |
| CLI 命令模型 | `src/nber_cli/cli.py` |
| Python 公开导出 | `src/nber_cli/__init__.py` |
| 搜索与元数据解析 | `src/nber_cli/fetch/fetcher.py` |
| Feed 解析与同步 | `src/nber_cli/fetch/feed.py` |
| PDF 下载引擎 | `src/nber_cli/fetch/download.py` |
| 共用数据模型 | `src/nber_cli/core/models.py` |
| 共用 SQLite 层 | `src/nber_cli/db/db.py`、`src/nber_cli/db/info_cache.py` |
| 配置 | `src/nber_cli/config/config_store.py`、`src/nber_cli/config/config.schema.json` |
| MCP 工具 | `src/nber_cli/mcp/mcp.py` |
| 可选 HTTP API | `src/nber_server/main.py`、`src/nber_server/routers/` |
| Desktop worker 入口 | `src/nber_cli/desktop_worker.py` |
| Desktop React 应用 | `desktop/src/App.tsx`、`desktop/src/pages/`、`desktop/src/components/`、`desktop/src/stores/` |
| Desktop 原生命令/配置/数据 | `desktop/src-tauri/src/commands.rs`、`config.rs`、`database.rs`、`worker.rs` |
| Desktop 包标识 | `desktop/package.json`、`desktop/src-tauri/tauri.conf.json`、`desktop/src-tauri/Cargo.toml` |
| 自动化测试 | `tests/`、`desktop/src/**/*.test.*`、Rust `#[cfg(test)]` 模块 |
| CI 与发布证据 | `.github/workflows/`、`scripts/`、`release/`、`CHANGELOG.md` |
| 视觉与交互设计 | `DESIGN.md`、`DESKTOP_UX.md` |
| 公开文档导航 | `mkdocs.yml`、`docs/en/`、`docs/zh/` |

## 12. 验证基线

发布或正式固化文档前运行：

```bash
uv run ruff check .
uv run pytest
uv run mypy src
uv run --group docs mkdocs build --strict
cd desktop
npm run lint
npm run test
npm run build
cd src-tauri
cargo test --locked
```

安装包还要执行仓库中的 Desktop 产物检查和 smoke test。完整发布清单与平台命令见[开发指南](development.md)。

## 13. 软件登记证据维护

应为实际申请所使用的 Release 固化一份文档控制记录，不能从持续变化的分支填写快照字段：

| 控制字段 | 本持续维护文档的值 | 登记快照动作 |
| --- | --- | --- |
| 产品基线 | NBER-CLI 0.10.0 | 记录准确的已发布版本和 tag。 |
| 文档修订 | 仓库持续维护文档 | 分配带日期、不可变的修订编号。 |
| 源码修订 | 当前工作树 | 记录固化 tag 对应的完整 commit hash。 |
| 验证日期 | 未固定 | 记录日期、执行人、操作系统和结果包。 |
| 构建标识 | 未固定 | 存档安装包/软件包文件名和 SHA-256 校验值。 |
| 权属/申请人记录 | 不属于仓库技术文档范围 | 附上申请地区要求的权威证明。 |

应建立功能到证据的索引，保证每一项界面和行为声明都能由同一源码版本复现：

| 功能组 | 主要源码 | 自动化证据 | 快照应采集的证据 |
| --- | --- | --- | --- |
| Desktop Feed 与详情 | `desktop/src/pages/FeedPage.tsx`、Tauri commands、Desktop worker | React、Rust、Feed、缓存测试 | 第一次刷新、Feed 列表、详情区、完成提示。 |
| 已读状态与标签 | Desktop stores/components 与 Rust 数据库层 | React 与 Rust 数据库测试 | 未读筛选、标签创建/编辑/隐藏、重启后持久化。 |
| 引用与设置 | Desktop 详情/设置组件 | 引用、布局、配置测试 | 六种引用选项、字号、刷新间隔、本地路径。 |
| CLI | `src/nber_cli/cli.py` | CLI 与发布测试 | `--help`、代表性 JSON/文本输出、失败退出码。 |
| MCP | `src/nber_cli/mcp/mcp.py` | MCP 测试 | 工具 schema，以及每个工具的一次成功结构化响应。 |
| 持久化与恢复 | Python/Rust 数据库和配置层 | 数据库、迁移、配置、smoke 测试 | 数据库版本、备份流程、损坏配置行为。 |

截图只是辅助证据，不能代替源码和测试追溯。截图前应遮盖个人路径、本地研究历史、凭据，以及超出功能识别所需范围的第三方论文内容。

未来准备软件著作权或类似登记快照时：

1. 固定一个已发布 tag，记录准确版本、commit、日期和支持平台。
2. 保持 Python 包、Desktop、Rust、plugin、更新日志、发布说明和文档版本一致。
3. 从同一 tag 导出源代码材料，排除依赖、生成产物、本地数据库、秘密信息和无关规划文件。
4. 使用同一 tag 构建的安装包截图，并给每张截图标注其证明的功能。
5. 保留构建日志、测试结果、发布校验值、许可证、贡献/权属记录和第三方声明。
6. 以本规格和[用户操作手册](user-manual.md)为技术基线，在仓库外补充申请人和地区特定声明。
7. 提交前重新运行源码路径、内部链接、中英文一致性和 strict 站点检查。

仓库文档可以帮助保证技术内容一致，但不构成法律意见，也不能单独证明权属或满足某个登记机关的全部要求。
