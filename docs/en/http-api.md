# Local HTTP API

The optional FastAPI service powers NBER-CLI Desktop and can also be used by trusted local integrations. It reuses the CLI's configuration and persistence modules, feed implementation, and metadata cache.

## Install and Start

Keep the HTTP dependencies out of the normal CLI environment by using the `server` extra:

```bash
uvx --from "nber-cli[server]" nber-server --host 127.0.0.1 --port 31527
```

From a development checkout:

```bash
uv sync --dev --extra server
uv run nber-server --host 127.0.0.1 --port 31527
```

| Option | Default | Description |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Interface to bind. Keep the loopback default. |
| `--port` | `31527` | Local HTTP port. |
| `--db-path` | `~/.nber-cli/nber.db` | SQLite database used by this server process. |
| `--log-dir` | `~/.nber-cli/logs` | Directory exposed in settings and used by the Desktop sidecar. |

The server creates or upgrades the database to schema v3 during startup.

!!! warning "Custom database paths"
    Without `--db-path`, the server currently uses `~/.nber-cli/nber.db`; it does not resolve a custom `feed.db-path` from the CLI config. Pass the same database explicitly when a local integration must share a migrated database, for example `--db-path ~/data/nber.db`.

## Security Boundary

The API has no authentication, authorization, or CSRF token. Anyone who can reach it can refresh the feed, read cached paper data, change read status, and edit Desktop settings. Keep it bound to `127.0.0.1`; do not bind it to `0.0.0.0` or expose it through a public tunnel or proxy without adding authentication and performing a security review.

The default browser origins are limited to the Desktop and local Vite development origins. CORS is not an authentication mechanism and does not protect the API from non-browser clients.

## Response Envelope

Handled successes and application errors use the same top-level shape:

```json
{
  "code": 0,
  "data": {},
  "message": ""
}
```

| `code` | Meaning |
| --- | --- |
| `0` | Success |
| `1` | Invalid parameter or requested paper not available in the local feed |
| `2` | Reserved for internal errors |
| `3` | NBER or another external operation failed |

HTTP status codes remain meaningful: validation commonly returns `400` or `422`, a paper missing from the local feed returns `404`, and NBER/network failures return `503`.

!!! note "Unhandled errors"
    The stable envelope currently covers explicit API errors and request validation. An unexpected internal exception can still use FastAPI's default HTTP 500 response instead of this envelope.

## Endpoint Summary

| Method | Path | Purpose | Writes local state |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | Service and database status | No |
| `GET` | `/api/v1/feed` | List cached feed items | May initialize/upgrade the database |
| `POST` | `/api/v1/feed/refresh` | Fetch and store the current RSS feed | Yes |
| `GET` | `/api/v1/papers/{paper_id}` | Load details for a feed paper | Marks it read; may update metadata cache |
| `POST` | `/api/v1/papers/{paper_id}/mark-read` | Set read/unread status | Yes |
| `GET` | `/api/v1/settings` | Read Desktop settings and local paths | No |
| `PATCH` | `/api/v1/settings` | Update Desktop port or refresh interval | Yes |

## Health

```bash
curl http://127.0.0.1:31527/api/v1/health
```

The `data` object contains `status`, package `version`, and the active `db_path`.

## List Feed

```bash
curl "http://127.0.0.1:31527/api/v1/feed?limit=50&offset=0&unread_only=false"
```

| Query | Default | Rules |
| --- | --- | --- |
| `limit` | `50` | Integer from `1` through `200` |
| `offset` | `0` | Non-negative integer |
| `unread_only` | `false` | Boolean |

The returned `data` contains `items`, `total_count`, the applied `limit` and `offset`, and `last_successful_fetch_at`. Each item contains its paper ID, title, authors, abstract, NBER URLs, first/last seen timestamps, and `is_read` state.

## Refresh Feed

```bash
curl -X POST http://127.0.0.1:31527/api/v1/feed/refresh
```

This makes a network request to NBER, updates `feed_items`, appends to `feed_fetches`, and returns `new_count`, `total_count`, `fetched_count`, and `last_successful_fetch_at`. External failures return HTTP `503` with `code: 3`.

## Get Paper Details

```bash
curl http://127.0.0.1:31527/api/v1/papers/w25000
```

Both `w25000` and `25000` are normalized to `w25000`. This endpoint only accepts papers that already exist in the local `feed_items` table; it is not a general-purpose lookup for any NBER ID. Refresh the feed first when necessary.

A successful request returns metadata, `pdf_url`, optional publication fields, `from_cache`, and `is_read: true`. It also marks the paper as read and can fetch/cache metadata from NBER. A valid ID that is absent from the local feed returns HTTP `404` with `code: 1`.

## Set Read Status

Mark unread:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"is_read": false}' \
  http://127.0.0.1:31527/api/v1/papers/w25000/mark-read
```

The body is optional; omitting it defaults to `is_read: true`. This endpoint writes `read_status` even when the paper is not currently present in `feed_items`.

## Read Settings

```bash
curl http://127.0.0.1:31527/api/v1/settings
```

The response contains `server_port`, `feed_refresh_interval_minutes`, `config_path`, `db_path`, and `log_dir`.

## Update Settings

```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -d '{"server_port": 31528, "feed_refresh_interval_minutes": 30}' \
  http://127.0.0.1:31527/api/v1/settings
```

| Field | Rules | Effect |
| --- | --- | --- |
| `server_port` | Integer from `1024` through `65535` | Saved immediately; the running server keeps its current port until restart |
| `feed_refresh_interval_minutes` | Positive integer | Used by Desktop automatic refresh |

Unknown fields are rejected with HTTP `422` and `code: 1`. This endpoint cannot change the database or log path.
