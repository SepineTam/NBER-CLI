# 使用政策

## NBER 与 NBER-CLI

National Bureau of Economic Research（NBER，美国国家经济研究局）是一家独立、非营利、无党派的经济研究机构，通过 [nber.org](https://www.nber.org) 发布和传播工作论文、研究元数据、通讯及相关研究材料。

**NBER** 是 National Bureau of Economic Research 的注册商标。NBER-CLI 是独立的开源项目，不隶属于 NBER，亦未获得 NBER 的认可、背书、赞助或运营授权。

NBER-CLI 是一个命令行、MCP、本地 HTTP 与 Desktop 工具，用于帮助用户搜索 NBER 工作论文、读取公开展示的论文元数据、追踪公开 RSS Feed，并从 NBER 托管的 URL 请求 PDF 下载。它不托管 NBER 内容，不提供替代分发服务，也不为用户创造任何独立于 NBER 之外的访问资格。使用 NBER-CLI 始终受 NBER 的[网站隐私政策](https://www.nber.org/nber-website-privacy-policy)、[工作论文访问与授权规则](https://www.nber.org/nber-help-working-papers-general-information)、[版权与许可规则](https://www.nber.org/nber-help-working-papers-general-information)、[订阅使用条款](https://www.nber.org/subscribe/information-libraries)，以及 NBER 已发布或未来更新的其他政策和访问条件约束。

## 项目边界

- **不进行项目侧存储**：NBER-CLI 不运营用于存储 NBER 论文或元数据的服务器、缓存、镜像、CDN 或其他基础设施。请求直接从用户的设备或 Agent 运行环境发往 NBER 网站。
- **用户机器上的默认本地持久化**：NBER-CLI 会在用户机器上保留一个本地 SQLite 数据库，默认位于 `~/.nber-cli/nber.db`（或 `nber-cli db init` / `db migrate` 配置的路径 / `sqlite:///...` URL），并保留一个用户配置文件 `~/.nber-cli/config.json`。数据库通过 SQLModel/SQLAlchemy 访问，除非用户自行复制或导出，否则它只留在用户机器上。下列命令和工具会在没有额外用户输入的情况下默认写入该数据库：
  - `nber-cli search` 会把每次查询的关键词、筛选条件和结果数量记录到 `query_log` 表。
  - `nber-cli download` 会把每次下载尝试的论文编号、成功或失败状态、保存的 PDF 路径以及失败时的错误信息记录到 `download_log` 表。单篇下载和批量下载都会按尝试次数逐条写入。
  - `nber-cli info` 与 MCP `get_paper_info` 工具会把每次查询的论文编号写入 `info_log` 表。
  - `nber-cli info` 与 MCP `get_paper_info` 工具在 `info_cache` 开启时还会写入并刷新 `info_cache` 表（详见 [配置](configuration.md)）。
  - `nber-cli feed fetch` 会把所有获取到的 RSS 条目写入 `feed_items`，并把一次抓取的摘要写入 `feed_fetches`。
  - Desktop 会启动只监听 loopback 的 sidecar、读取本地 Feed，在数据库为空时自动请求 RSS，并在应用处于活动状态时按设置的间隔刷新。
  - 在 Desktop 中打开论文可能会向 NBER 请求元数据、更新 `info_cache`，并把已读状态写入 `read_status`；手动切换已读或未读也会更新该表。
  - Desktop 会创建或更新 `~/.nber-cli/config.json`，并把 sidecar 输出写入 `~/.nber-cli/logs/sidecar.stdout.log` 和 `sidecar.stderr.log`。Desktop 0.8.0 当前即使配置了自定义数据库路径，也会使用默认的 `~/.nber-cli/nber.db`；详见 [Desktop 指南](desktop.md)。
- **本地数据清理**：`feed clean` 和 `info cache clear` 在交互式确认后会删除缓存记录。`query_log`、`download_log`、`info_log` 表目前没有专门的 CLI 清理命令；目前只能通过 `nber-cli db migrate` 切到新数据库、手动 `sqlite3` 操作，或直接删除 `nber.db` 来清空这些日志。`feed clean --all` 只删除 `feed_items`，不会动会持续累积的 `feed_fetches` 历史。
- **本地文件由用户控制**：当用户执行下载命令时，PDF 只会保存到用户选择的本地路径。本项目不会接收、保留、索引或再分发该文件。
- **不绕过访问限制**：NBER-CLI 不绕过订阅、付费墙、账号要求、基于 IP 的授权、新近论文或首周访问限制、访问额度，或 NBER 设置的其他控制措施。如果 NBER 返回拒绝、错误、跳转或不可用响应，本工具会将该响应视为有效结果。
- **不隐藏或伪装流量**：NBER-CLI 使用标准 Python HTTP 库和常规请求头，不提供代理池、IP 轮换、凭据共享、验证码绕过、请求签名篡改或其他规避机制。
- **不授予再分发权利**：安装或使用 NBER-CLI 不代表用户获得转载、镜像、销售、再授权、训练模型，或以其他方式复用 NBER 内容的许可；相关使用仍以 NBER、相应作者及适用法律允许的范围为准。

## 访问、版权与用户责任

NBER 决定其网站上哪些内容可访问，以及在什么条件下可访问。访问资格可能取决于论文发布时间、订阅状态、机构资格、地区资格、账号授权，或 NBER 设置的其他规则。用户在下载、复制、引用、分享或以其他方式使用任何 NBER 材料前，应自行确认相关使用是否被允许。

NBER 说明其 Working Papers 的版权由相应作者持有，而非由 NBER 持有。NBER-CLI 不拥有任何论文内容，也无权授予超出 NBER 已开放访问范围或法律允许范围之外的使用许可。涉及合理使用或其他法定例外之外的许可请求，应由用户向相应权利人确认。

NBER-CLI 的目标用途是合法的个人研究、教育和可复现研究流程。它不适用于系统性批量抓取、公开镜像、转载、转售、未经授权的商业使用，或任何旨在规避 NBER 访问决定的流程。

## 运行透明性

搜索和元数据功能使用 NBER 网页，以及 nber.org 正常运行过程中使用的网站端点。PDF 下载会请求由 NBER 提供的文件 URL。本项目不声称这些接口是官方 API、稳定 API 或经 NBER 批准的集成方式。

元数据、摘要、链接、可访问性和文件均由 NBER 提供，可能存在不完整、延迟、修订、移除、限流或其他变更。若 NBER 更改网站结构、访问政策、端点、授权校验或文件位置，NBER-CLI 可能无法继续工作。

## 风险归属

NBER-CLI 作为独立开源工具，按“现状”和“可用时”提供。维护者不控制 NBER 的网站、内容、版权许可、访问决定、服务可用性或政策，也不承诺用户可以持续访问任何 NBER 材料。

使用 NBER-CLI 即表示用户自行承担其请求、下载、本地存储选择，以及后续使用 NBER 材料所产生的责任。维护者不对访问被拒、账号或网络受限、版权或许可争议、数据丢失、服务中断、政策违反，或因用户使用 NBER-CLI 而产生的其他后果承担责任。
