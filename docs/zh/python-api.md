# Python API

NBER-CLI 暴露了与 CLI 相同核心能力的 Python 函数。由于查询、搜索和下载都涉及网络 I/O，这些 API 是异步的。

feed 缓存辅助函数是同步的，因为它们主要执行本地数据库操作和同步 RSS 获取。

## API 边界

NBER-CLI 共有三层，三层的稳定性承诺各不相同：

- **顶层公共 API**：`nber_cli.__all__` 中列出的名字。这是使用本包“受支持”的入口方式，是唯一具有稳定性承诺的一层。删除或重命名 `__all__` 中的名字会被视为破坏性变更。
- **模块级辅助函数**：`nber_cli.formatters`、`nber_cli.fetcher`、`nber_cli.config_store`、`nber_cli.cli` 等模块中不带下划线前缀的名字。可以直接导入使用，也对高级调用方有帮助，但它们**不属于**顶层公共契约，可能在 minor 版本之间调整。
- **兼容包装器**：仅为了兼容早期版本的调用方而保留的若干名字。`feed` 模块重新导出了 `init_feed_database`、`migrate_feed_database`、`get_feed_database_path`，现在它们会转发到底层数据库模块。它们会在替代接口发布后保留一个 minor 版本，并可能在之后移除。

`__all__` 是“官方导出”的唯一事实来源。若一个名字不在 `__all__` 中，也未在文档中作为模块级辅助函数登记，即便没有下划线前缀也应视为私有。

## 安装

```bash
uv add nber-cli
```

如果是在项目外运行脚本：

```bash
uvx --from nber-cli python your_script.py
```

## 搜索论文

```python
import asyncio

from nber_cli import search_nber, search_results


async def main() -> None:
    results = await search_nber("labor economics", per_page=20)
    payload = search_results(results)
    print(payload["total_results"])
    for paper in payload["results"]:
        print(paper["id"], paper["title"])


asyncio.run(main())
```

## 获取论文元数据

```python
import asyncio

from nber_cli import get_nber, info


async def main() -> None:
    paper = await get_nber(25000)
    payload = info(paper)
    print(payload["title"])
    print(payload["abstract"])


asyncio.run(main())
```

## 下载 PDF

```python
import asyncio
from pathlib import Path

from nber_cli import download_paper, download_paper_to_file


async def main() -> None:
    await download_paper("w34567", Path("papers"))
    await download_paper_to_file("w25000", Path("papers/w25000.pdf"))


asyncio.run(main())
```

## 批量下载

```python
import asyncio
from pathlib import Path

from nber_cli import download_multiple_papers


async def main() -> None:
    result = await download_multiple_papers(
        ["w34567", "w25000", "w32000"],
        Path("papers"),
    )
    print(f"成功下载 {len(result.paths)} 篇论文")
    for failure in result.failures:
        print(f"失败: {failure.paper_id} - {failure.error}")


asyncio.run(main())
```

## 使用本地数据库

初始化默认数据库：

```python
from nber_cli import init_database

db_path = init_database()
print(db_path)
```

使用 SQLite URL 初始化：

```python
from nber_cli import init_database

db_path = init_database("sqlite:////Users/name/data/nber.db")
print(db_path)
```

获取 NBER RSS feed 并显示新的缓存条目：

```python
from nber_cli import feed_results, fetch_feed

result = fetch_feed()
payload = feed_results(result)
print(payload["new_count"])
for item in payload["results"]:
    print(item["id"], item["title"])
```

显示所有获取到的 RSS 条目，并限制返回数量：

```python
from nber_cli import fetch_feed

result = fetch_feed(display_all=True, max_items=5)
```

移动数据库：

```python
from pathlib import Path

from nber_cli import migrate_database

old_path, new_path = migrate_database(Path("~/data/nber.db"))
```

清理 feed 缓存数据库记录：

```python
from nber_cli import clean_feed_cache

preview = clean_feed_cache(days=30, dry_run=True)
print(preview.matched_count)

result = clean_feed_cache(days=30)
print(result.deleted_count)
```

`clean_feed_cache` 只会删除本地缓存记录。如果被删除的记录仍然出现在 RSS feed 中，后续调用 `fetch_feed` 时它们可能会再次作为新条目返回。

直接读写论文元数据缓存：

```python
from nber_cli import read_info_cache, write_info_cache
from nber_cli import get_nber
import asyncio

paper = read_info_cache(None, "w25000")
if paper is None:
    paper = asyncio.run(get_nber(25000))
    write_info_cache(None, paper)
print(paper.title)
```

通过高层辅助函数读取论文元数据缓存，该函数会遵守用户配置中的 TTL 和全局缓存开关：

```python
import asyncio

from nber_cli.info_cache import get_paper_with_info_cache_result


async def main() -> None:
    result = await get_paper_with_info_cache_result(25000)
    if result.from_cache:
        print("Served from local info cache")
    print(result.paper.title)


asyncio.run(main())
```

`refresh=True` 跳过缓存读取，重新从 NBER 拉取，并在缓存开启时写回：

```python
import asyncio

from nber_cli.info_cache import get_paper_with_info_cache_result


async def main() -> None:
    result = await get_paper_with_info_cache_result(25000, refresh=True)
    print(result.paper.title)


asyncio.run(main())
```

管理用户配置（`~/.nber-cli/config.json`）：

```python
from nber_cli import (
    get_info_cache_settings,
    set_info_cache_enabled,
    set_info_cache_ttl_days,
)

print(get_info_cache_settings())
set_info_cache_enabled(False)
set_info_cache_ttl_days(7)
```

清理论文元数据缓存：

```python
from nber_cli import clear_info_cache, count_info_cache

print(f"Cached rows: {count_info_cache()}")

preview = clear_info_cache(days=30, dry_run=True)
print(f"Matched: {preview.matched_count}")

result = clear_info_cache(days=30)
print(f"Deleted: {result.deleted_count}")
```

`clear_info_cache` 同时支持 `delete_all=True` 以及 `start_date` / `end_date` 过滤，与 `clean_feed_cache` 的语义一致。

## 数据库与日志辅助函数

这些辅助函数属于顶层公共 API，可以在用户代码中安全调用。它们通过 SQLModel/SQLAlchemy 包装了 `info`、`search`、`download` 和 `feed` 内部使用的本地 SQLite 数据库。日志与缓存写入采用“软失败”策略：数据库异常发生时，函数会向 `stderr` 输出一行 warning（对于记录器返回 `None`），而不会抛出异常，因此不会打断调用方的主命令。缓存读取器在数据库局部错误下返回 `None` 或 `0`。需要更强保证的调用方可以直接检查解析后的本地数据库路径。

### `get_database_path(db_path=None) -> Path`

返回解析后的 SQLite 数据库路径。`db_path` 可以是 `Path`、文件路径字符串，也可以是 `sqlite:///...` URL。当 `db_path` 为 `None` 时，NBER-CLI 优先使用 `~/.nber-cli/config.json` 中配置的位置，回退到默认 `~/.nber-cli/nber.db`，在文件存在时回退到旧版 `~/.nber-cli/feed.db`。即使输入是 SQLite URL，返回值也始终是绝对路径。**不要求**该数据库文件实际存在。

### `get_schema_version(db_path=None) -> int`

返回数据库当前的 `PRAGMA user_version`。文件不存在时返回 `0`。包代码在 `init_database` 或自动从 v1/v2 升级到 v3 后把该值设为 `3`。

### `record_query(db_path, keyword, conditions, result_count)`

向 `query_log` 追加一行。`conditions` 是描述实际筛选条件的可 JSON 序列化 `dict`。失败（例如只读文件系统或数据库损坏）会向 `stderr` 打印 `warning: failed to record_query: ...` 并直接返回，不会抛出。

### `record_download(db_path, paper_id, status, saved_path=None, error=None)`

向 `download_log` 追加一行。`status` 通常是 `"success"` 或 `"failed"`。失败被吞掉并打印到 `stderr`；调用方下载命令的退出码不受影响。

### `record_info(db_path, paper_id)`

向 `info_log` 追加一行，记录被查询的论文。`paper_id` 可以是 `int`，也可以是带或不带 `w` 前缀的字符串。失败被吞掉，只打印 `stderr`。

### `is_info_cache_enabled() -> bool`

返回 `~/.nber-cli/config.json` 中配置的 `info_cache` 全局开关当前值。

### `get_info_cache_ttl_days() -> int`

返回 `~/.nber-cli/config.json` 中配置的 `info_cache` 刷新间隔（天）。字段缺失或非正时回退到默认 `30`。

### `is_info_cache_expired(last_fetched_at, ttl_days=None, *, now=None) -> bool`

当时间戳字符串 `last_fetched_at` 比 `ttl_days`（或 `ttl_days=None` 时取配置的 TTL）更早时返回 `True`。`ttl_days <= 0` 视为“总是过期”。时间戳无法解析也视为过期。`now` 接受 `datetime`，仅用于测试。

### `touch_info_cache(db_path, paper_id)`

更新 `paper_id` 对应的 `info_cache` 行：把 `last_fetched_at` 设为当前 UTC 时间，并把 `fetch_count` 加 1。因为每次缓存命中都会调用它，TTL 实际基于最近一次命中时间，而不是首次写入时间——这使得 `info_cache` 表现为**滑动 TTL** 而非首次写入起的固定窗口。行不存在或数据库文件不存在时该函数是 no-op。错误会写入 `stderr` 并被忽略。

### `parse_feed_xml(xml_text) -> list[NBERFeedItem]`

把 NBER RSS 的原始 XML 解析为 `NBERFeedItem` 列表。条目必须在 `link` 或 `guid` 中携带能匹配 `r"/papers/(w\d+)"` 的论文 ID；没有论文 ID 的条目会被跳过。解析器只会修复 `title` 和 `description` 文本中后接空白或数字的未转义 `<`，然后重新进行严格解析。其他 XML 格式错误会抛出以 `"invalid NBER RSS XML"` 开头的 `ValueError`，并在可用时附带行号和列号。该函数不访问网络，也不读写数据库；`feed.fetch_feed` 在其上包装持久化与 `feed_fetches` 摘要写入。

## 数据模型

### NBER

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `paper_id` | `int` | 数字论文编号。 |
| `title` | `str` | 论文标题。 |
| `authors` | `list[str]` | 作者姓名。 |
| `date` | `str` | NBER 暴露的发表日期。 |
| `abstract` | `str` | 论文摘要。 |
| `url` | `str` 或 `None` | 可用时的 NBER 论文 URL。 |
| `published_version` | `str` 或 `None` | 可用时的 published-version 文本。 |
| `topic` | `str` 或 `None` | 可用时的主题元数据。 |
| `programs` | `str` 或 `None` | 可用时的项目元数据。 |

### NBERSearchResults

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `query` | `str` | 原始查询。 |
| `total_results` | `int` | NBER 结果总数。 |
| `results` | `list[NBER]` | 当前页论文。 |
| `page` | `int` | 当前页码。 |
| `per_page` | `int` | 每页结果数量。 |
| `start_date` | `str` 或 `None` | 已应用的开始日期。 |
| `end_date` | `str` 或 `None` | 已应用的结束日期。 |

### NBERFeedItem

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `paper_id` | `str` | 论文编号，例如 `w35254`。 |
| `title` | `str` | 从 RSS 条目解析出的论文标题。 |
| `authors` | `list[str]` | 从 RSS 标题解析出的作者姓名。 |
| `abstract` | `str` | RSS 条目的 description。 |
| `url` | `str` | 去掉 RSS fragment 后的 NBER 论文 URL。 |
| `source_url` | `str` | RSS 条目中的原始 URL。 |
| `guid` | `str` | RSS 条目的 GUID。 |

### NBERFeedFetchResult

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `source_url` | `str` | RSS feed URL。 |
| `database_path` | `Path` | 解析后的本地 SQLite 缓存数据库路径。 |
| `total_fetched` | `int` | 本次获取到的 RSS 条目数量。 |
| `new_count` | `int` | 本次获取到且缓存中原本不存在的条目数量。 |
| `display_all` | `bool` | 返回条目是否包含所有获取到的条目。 |
| `items` | `list[NBERFeedItem]` | 选中用于展示或结构化输出的条目。 |
| `max_items` | `int` 或 `None` | 提供时的展示数量限制。 |

### NBERFeedCleanResult

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `database_path` | `Path` | 解析后的本地 SQLite 缓存数据库路径。 |
| `matched_count` | `int` | 符合清理条件的缓存记录数量。 |
| `deleted_count` | `int` | 已删除的缓存记录数量。 |
| `mode` | `str` | 清理模式：`days`、`all` 或 `date-range`。 |
| `days` | `int` 或 `None` | `days` 模式下的天数阈值。 |
| `start_date` | `str` 或 `None` | `date-range` 模式下前后包含的开始日期。 |
| `end_date` | `str` 或 `None` | `date-range` 模式下前后包含的结束日期。 |
| `dry_run` | `bool` | 是否只统计匹配记录而不删除。 |

### NBERInfoCacheClearResult

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `database_path` | `Path` | 解析后的本地 SQLite 缓存数据库路径。 |
| `matched_count` | `int` | 符合清理条件的缓存记录数量。 |
| `deleted_count` | `int` | 已删除的缓存记录数量。 |
| `mode` | `str` | 清理模式：`days`、`all` 或 `date-range`。 |
| `days` | `int` 或 `None` | `days` 模式下的天数阈值。 |
| `start_date` | `str` 或 `None` | `date-range` 模式下前后包含的开始日期。 |
| `end_date` | `str` 或 `None` | `date-range` 模式下前后包含的结束日期。 |
| `dry_run` | `bool` | 是否只统计匹配记录而不删除。 |

### InfoCacheSettings

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `cache_enabled` | `bool` | `info_cache` 读取的全局开关。 |
| `cache_ttl_days` | `int` | 缓存刷新间隔（天）。 |

### InfoCacheLookupResult

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `paper` | `NBER` | 查询返回的论文对象。 |
| `from_cache` | `bool` | 当论文来自本地 `info_cache` 时为 `True`。 |

### DownloadFailure

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `paper_id` | `str` | 下载失败的论文编号。 |
| `error` | `BaseException` | 下载尝试期间抛出的异常。 |

### DownloadBatchResult

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `paths` | `list[Path]` | 成功下载的 PDF 路径。 |
| `failures` | `list[DownloadFailure]` | 失败下载及其错误。 |

## Formatter 辅助函数

如果需要稳定的字典输出用于 JSON 或 MCP 风格响应，可以使用 formatter：

```python
from nber_cli import feed_results, info, related, search_results
```

- `info(paper)` 返回核心元数据。
- `related(paper)` 返回可选相关字段。
- `search_results(results)` 返回结构化搜索结果。
- `feed_results(result)` 返回结构化 feed fetch 结果。

如果需要适合人读的文本输出，请从 `nber_cli.formatters` 模块导入：

```python
from nber_cli.formatters import feed_results_text, info_text, search_results_text
```

- `info_text(paper, include_all=False)` 返回格式化的论文详情文本。设置 `include_all=True` 可包含 topic、programs 和 published version。
- `search_results_text(results)` 返回格式化的搜索结果文本。
- `feed_results_text(result)` 返回格式化的 feed 文本。

## JSON 输出结构

`info`、`search` 和 `feed fetch` 的 `--format json` 输出与对应 `*_results` formatter 构造的字典一致。JSON 负载写入 **stdout**，错误信息写入 **stderr**。缓存命中不会额外输出 stderr 提示，因此脚本可以通过重定向或管道捕获负载，而不会混入缓存状态文本。

### `info --format json`

由 `info(paper)` 构造；启用 `--all` 时会并入 `related(paper)` 以及一个有条件的 `published_version` 字段：

| 字段 | 类型 | 始终出现 | 备注 |
| --- | --- | --- | --- |
| `id` | `str` | 是 | 格式化为 `wNNNN` 的 `paper_id`。 |
| `title` | `str` | 是 | NBER 未暴露时为空字符串。 |
| `authors` | `list[str]` | 是 | NBER 未暴露时为空列表。 |
| `date` | `str` | 是 | NBER 暴露的发布日期，可能为空。 |
| `abstract` | `str` | 是 | NBER 未暴露时为空字符串。 |
| `url` | `str` | 否 | 仅在论文有非空 NBER URL 时出现。 |
| `topic` | `str` | 仅 `--all` | 可空，未知时输出 `null`。 |
| `programs` | `str` | 仅 `--all` | 可空，未知时输出 `null`。 |
| `published_version` | `str` | 仅 `--all` 且非空 | NBER 未暴露时整个键省略不输出。 |

### `search --format json`

由 `search_results(results)` 构造：

| 字段 | 类型 | 始终出现 | 备注 |
| --- | --- | --- | --- |
| `query` | `str` | 是 | 原始查询。 |
| `total_results` | `int` | 是 | NBER 报告的总数。 |
| `page` | `int` | 是 | 当前页。 |
| `per_page` | `int` | 是 | 页大小，取值为 `20`、`50`、`100`。 |
| `start_date` | `str` | 否 | 仅在调用应用了开始日期时出现。 |
| `end_date` | `str` | 否 | 仅在调用应用了结束日期时出现。 |
| `results` | `list[object]` | 是 | 与 `search_result(paper)` 字段一致的每条论文字典。 |

`results` 中每条记录包含 `id`、`title`、`authors`、`date`、`abstract`、`url`。与 `info` 不同的是，`url` 始终出现（可能为空字符串）。

### `feed fetch --format json`

由 `feed_results(result)` 构造：

| 字段 | 类型 | 备注 |
| --- | --- | --- |
| `source_url` | `str` | 本次抓取的 RSS feed URL。 |
| `database_path` | `str` | 写入条目的本地 SQLite 数据库解析后绝对路径。 |
| `total_fetched` | `int` | 本次从 feed 解析出的条目数。 |
| `new_count` | `int` | 本地缓存中原本不存在的条目数。 |
| `display_all` | `bool` | `results` 包含全部条目时为 `true`；只包含新条目时为 `false`。 |
| `max_items` | `int` 或 `null` | 设置 `--max-items` 时为该上限，否则为 `null`。 |
| `displayed_count` | `int` | 实际放入 `results` 的条目数。 |
| `results` | `list[object]` | 每条目包含 `id`、`title`、`authors`、`abstract`、`url`、`source_url`、`guid`。 |

### 兼容性说明

JSON 结构是 CLI 与 MCP 工具共享的对外输出契约。允许在 minor 版本中以“新增可选键”的方式添加字段。已有键的重命名、删除或类型变更视为破坏性变更。消费 `--format json` 的脚本应将未知键视为可忽略数据，而不要对完整键集做强断言。
