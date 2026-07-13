# 本地 HTTP API

可选的 FastAPI 服务为 NBER-CLI Desktop 提供后端，也可以用于可信的本地集成。它复用 CLI 的配置与持久化模块、Feed 实现和论文元数据缓存。

## 安装与启动

通过 `server` extra 运行，避免把 HTTP 依赖装进普通 CLI 环境：

```bash
uvx --from "nber-cli[server]" nber-server --host 127.0.0.1 --port 31527
```

从开发仓库启动：

```bash
uv sync --dev --extra server
uv run nber-server --host 127.0.0.1 --port 31527
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--host` | `127.0.0.1` | 监听接口；应保留 loopback 默认值。 |
| `--port` | `31527` | 本地 HTTP 端口。 |
| `--db-path` | `~/.nber-cli/nber.db` | 当前 server 进程使用的 SQLite 数据库。 |
| `--log-dir` | `~/.nber-cli/logs` | 设置接口展示的目录，也是 Desktop sidecar 日志目录。 |

Server 启动时会创建数据库或把它升级到 schema v3。

!!! warning "自定义数据库路径"
    未传 `--db-path` 时，server 当前固定使用 `~/.nber-cli/nber.db`，不会从 CLI 配置中解析自定义 `feed.db-path`。本地集成需要共用迁移后的数据库时，请明确传入同一路径，例如 `--db-path ~/data/nber.db`。

## 安全边界

API 没有身份认证、权限控制或 CSRF token。任何可以访问它的程序都能刷新 Feed、读取本地论文数据、修改已读状态和 Desktop 设置。请保持监听 `127.0.0.1`；未经额外认证和安全审查，不要绑定 `0.0.0.0`，也不要通过公网隧道或代理暴露它。

默认浏览器 Origin 仅包含 Desktop 和本地 Vite 开发地址。CORS 不是身份认证，也不能阻止非浏览器客户端访问 API。

## 响应 Envelope

已处理的成功和应用错误使用同一顶层结构：

```json
{
  "code": 0,
  "data": {},
  "message": ""
}
```

| `code` | 含义 |
| --- | --- |
| `0` | 成功 |
| `1` | 参数错误，或请求的论文不在本地 Feed 中 |
| `2` | 为内部错误预留 |
| `3` | NBER 或其他外部操作失败 |

HTTP 状态码仍然有意义：参数校验通常返回 `400` 或 `422`，论文不在本地 Feed 时返回 `404`，NBER 或网络失败返回 `503`。

!!! note "未处理异常"
    稳定 envelope 当前只覆盖明确的 API 错误和请求参数校验。未预期的内部异常仍可能返回 FastAPI 默认 HTTP 500 结构，而不是上述 envelope。

## 端点总览

| 方法 | 路径 | 用途 | 是否写入本地状态 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | 服务和数据库状态 | 否 |
| `GET` | `/api/v1/feed` | 列出缓存的 Feed 条目 | 可能初始化或升级数据库 |
| `POST` | `/api/v1/feed/refresh` | 获取并保存当前 RSS Feed | 是 |
| `GET` | `/api/v1/papers/{paper_id}` | 加载 Feed 中论文的详情 | 标为已读，可能更新元数据缓存 |
| `POST` | `/api/v1/papers/{paper_id}/mark-read` | 设置已读或未读状态 | 是 |
| `GET` | `/api/v1/settings` | 读取 Desktop 设置和本地路径 | 否 |
| `PATCH` | `/api/v1/settings` | 修改 Desktop 端口或刷新间隔 | 是 |

## 健康检查

```bash
curl http://127.0.0.1:31527/api/v1/health
```

`data` 中包含 `status`、包 `version` 和当前 `db_path`。

## 列出 Feed

```bash
curl "http://127.0.0.1:31527/api/v1/feed?limit=50&offset=0&unread_only=false"
```

| 查询参数 | 默认值 | 规则 |
| --- | --- | --- |
| `limit` | `50` | `1` 至 `200` 的整数 |
| `offset` | `0` | 非负整数 |
| `unread_only` | `false` | 布尔值 |

返回的 `data` 包含 `items`、`total_count`、实际使用的 `limit` 和 `offset`，以及 `last_successful_fetch_at`。每个条目包含论文编号、标题、作者、摘要、NBER URL、首次/最近发现时间和 `is_read` 状态。

## 刷新 Feed

```bash
curl -X POST http://127.0.0.1:31527/api/v1/feed/refresh
```

该操作会向 NBER 发起网络请求、更新 `feed_items`、向 `feed_fetches` 追加记录，并返回 `new_count`、`total_count`、`fetched_count` 和 `last_successful_fetch_at`。外部操作失败时返回 HTTP `503` 和 `code: 3`。

## 获取论文详情

```bash
curl http://127.0.0.1:31527/api/v1/papers/w25000
```

`w25000` 和 `25000` 都会被规范化为 `w25000`。该端点只接受已经存在于本地 `feed_items` 表中的论文，不能用来查询任意 NBER 编号；需要时请先刷新 Feed。

成功响应包含论文元数据、`pdf_url`、可选的出版字段、`from_cache` 和 `is_read: true`。该请求还会把论文标为已读，并可能从 NBER 获取和缓存元数据。格式正确但不在本地 Feed 的编号会返回 HTTP `404` 和 `code: 1`。

## 设置已读状态

标为未读：

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"is_read": false}' \
  http://127.0.0.1:31527/api/v1/papers/w25000/mark-read
```

Body 可以省略；省略时默认使用 `is_read: true`。即使论文当前不在 `feed_items` 中，该端点也会写入 `read_status`。

## 读取设置

```bash
curl http://127.0.0.1:31527/api/v1/settings
```

响应包含 `server_port`、`feed_refresh_interval_minutes`、`config_path`、`db_path` 和 `log_dir`。

## 修改设置

```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"server_port": 31528, "feed_refresh_interval_minutes": 30}' \
  http://127.0.0.1:31527/api/v1/settings
```

| 字段 | 规则 | 效果 |
| --- | --- | --- |
| `server_port` | `1024` 至 `65535` 的整数 | 立即保存；当前 server 在重启前仍继续使用旧端口 |
| `feed_refresh_interval_minutes` | 正整数；Desktop 请使用 `1`–`65535` | 供 Desktop 自动刷新使用。API 会接受更大的值，但当前 Rust 外壳下次启动时会回退到 `60`。 |

未知字段会返回 HTTP `422` 和 `code: 1`。该端点不能修改数据库或日志路径。
