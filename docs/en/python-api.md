# Python API

NBER-CLI exposes the same core functionality as importable Python functions. The API is asynchronous because lookup, search, and downloads perform network I/O.

Feed cache helpers are synchronous because they perform local SQLite work and a synchronous RSS fetch.

## API Boundaries

NBER-CLI has three layers, and the stability contract is different for each:

- **Top-level public API**: the names listed in `nber_cli.__all__`. Importing them from the `nber_cli` package is the supported way to use the package. This is the only layer with a stability promise. Removing or renaming a name in `__all__` is treated as a breaking change.
- **Module-level helpers**: non-underscore names defined in modules such as `nber_cli.formatters`, `nber_cli.fetcher`, `nber_cli.config_store`, and `nber_cli.cli`. These are usable directly and useful for advanced callers, but they are not part of the public top-level contract and may change between minor versions.
- **Compatibility wrappers**: a few names exist only for backward compatibility with callers written against earlier versions. The `feed` module re-exports `init_feed_database`, `migrate_feed_database`, and `get_feed_database_path`, which now forward to the database layer. They are kept for one minor release after their replacement ships and may be removed later.

`__all__` is the source of truth for what is "officially exported" from the package. If a name is not in `__all__` and not documented as a module-level helper, treat it as private even if it is not underscore-prefixed.

## Install

```bash
uv add nber-cli
```

For a script outside a project:

```bash
uvx --from nber-cli python your_script.py
```

## Search Papers

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

## Fetch Paper Metadata

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

## Download a PDF

```python
import asyncio
from pathlib import Path

from nber_cli import download_paper, download_paper_to_file


async def main() -> None:
    await download_paper("w34567", Path("papers"))
    await download_paper_to_file("w25000", Path("papers/w25000.pdf"))


asyncio.run(main())
```

## Download Multiple Papers

```python
import asyncio
from pathlib import Path

from nber_cli import download_multiple_papers


async def main() -> None:
    result = await download_multiple_papers(
        ["w34567", "w25000", "w32000"],
        Path("papers"),
    )
    print(f"Downloaded {len(result.paths)} papers")
    for failure in result.failures:
        print(f"Failed: {failure.paper_id} - {failure.error}")


asyncio.run(main())
```

## Work with the Local Database

Initialize the default database:

```python
from nber_cli import init_database

db_path = init_database()
print(db_path)
```

Fetch the NBER RSS feed and display new cached items:

```python
from nber_cli import feed_results, fetch_feed

result = fetch_feed()
payload = feed_results(result)
print(payload["new_count"])
for item in payload["results"]:
    print(item["id"], item["title"])
```

Display all fetched RSS items and limit the returned items:

```python
from nber_cli import fetch_feed

result = fetch_feed(display_all=True, max_items=5)
```

Move the database:

```python
from pathlib import Path

from nber_cli import migrate_database

old_path, new_path = migrate_database(Path("~/data/nber.db"))
```

Clean cached feed database records:

```python
from nber_cli import clean_feed_cache

preview = clean_feed_cache(days=30, dry_run=True)
print(preview.matched_count)

result = clean_feed_cache(days=30)
print(result.deleted_count)
```

`clean_feed_cache` deletes local cache records only. If deleted records still appear in the RSS feed, a later `fetch_feed` call may return them as new items again.

Read or write the paper metadata cache directly:

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

Read the paper metadata cache through the high-level helper, which respects the user-config TTL and the global cache toggle:

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

`refresh=True` skips the cache lookup and re-fetches from NBER before optionally writing back:

```python
import asyncio

from nber_cli.info_cache import get_paper_with_info_cache_result


async def main() -> None:
    result = await get_paper_with_info_cache_result(25000, refresh=True)
    print(result.paper.title)


asyncio.run(main())
```

Manage the user config (`~/.nber-cli/config.json`):

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

Clean cached paper metadata:

```python
from nber_cli import clear_info_cache, count_info_cache

print(f"Cached rows: {count_info_cache()}")

preview = clear_info_cache(days=30, dry_run=True)
print(f"Matched: {preview.matched_count}")

result = clear_info_cache(days=30)
print(f"Deleted: {result.deleted_count}")
```

The same `clear_info_cache` function also supports `delete_all=True` and `start_date` / `end_date` filters that mirror `clean_feed_cache`.

## Database and Logging Helpers

These helpers are part of the top-level public API and are safe to call from user code. They wrap the SQLite layer that `info`, `search`, `download`, and `feed` use internally. Logging and cache writers fail soft: when a database error occurs, the helper prints a one-line warning to `stderr` and returns `None` (for recorders) instead of raising, so they do not break the calling command. Cache readers return `None` or `0` on partial database errors. Callers that need stronger guarantees should talk to SQLite directly.

### `get_database_path(db_path=None) -> Path`

Return the resolved SQLite database path. When `db_path` is `None`, NBER-CLI uses the path configured in `~/.nber-cli/config.json`, or falls back to the default `~/.nber-cli/nber.db`, or the legacy `~/.nber-cli/feed.db` file when present. The returned path is always absolute. The database file is **not** required to exist.

### `get_schema_version(db_path=None) -> int`

Return the current `PRAGMA user_version` of the database. Returns `0` when the file does not exist. The package sets the user version to `2` after `init_database` or an automatic v1-to-v2 upgrade.

### `record_query(db_path, keyword, conditions, result_count)`

Append a row to `query_log`. `conditions` is a JSON-serialisable `dict` describing the filters actually applied to the call. Failures (for example a read-only filesystem or a corrupted database) print `warning: failed to record_query: ...` to `stderr` and return without raising.

### `record_download(db_path, paper_id, status, saved_path=None, error=None)`

Append a row to `download_log`. `status` is typically `"success"` or `"failed"`. Failures are swallowed and printed to `stderr`; the calling download command still exits with its normal code.

### `record_info(db_path, paper_id)`

Append a row to `info_log` for the looked-up paper. `paper_id` may be an `int` or a string with or without the `w` prefix. Failures are swallowed and reported to `stderr` only.

### `is_info_cache_enabled() -> bool`

Return the current global `info_cache` toggle, as configured in `~/.nber-cli/config.json`.

### `get_info_cache_ttl_days() -> int`

Return the current `info_cache` refresh interval in days, as configured in `~/.nber-cli/config.json`. Defaults to `30` when the field is missing or non-positive.

### `is_info_cache_expired(last_fetched_at, ttl_days=None, *, now=None) -> bool`

Return `True` when the timestamp string `last_fetched_at` is older than `ttl_days` (or the configured TTL when `ttl_days` is `None`). `ttl_days <= 0` is treated as "always expired". Malformed timestamps are treated as expired. `now` is for testing and accepts a `datetime`.

### `touch_info_cache(db_path, paper_id)`

Update the `info_cache` row for `paper_id`: set `last_fetched_at` to the current UTC time and increment `fetch_count`. Because this is invoked on every cache hit, the TTL check uses the touch time, not the original write time. This is what makes the cache a **sliding** TTL rather than a fixed window from the first write. The function is a no-op when the row does not exist or the database is missing. Errors are logged to `stderr` and otherwise ignored.

### `parse_feed_xml(xml_text) -> list[NBERFeedItem]`

Parse raw NBER RSS XML into a list of `NBERFeedItem` objects. Items must carry a `link` or `guid` that matches `r"/papers/(w\d+)"`; when neither field contains a paper ID, `parse_feed_xml` raises `ValueError("NBER RSS item is missing a paper ID")`. Malformed XML raises `ValueError("invalid NBER RSS XML")`. The function performs no network I/O and never touches the database; `feed.fetch_feed` wraps it to persist items and write a `feed_fetches` summary.

## Data Models

### NBER

| Field | Type | Description |
| --- | --- | --- |
| `paper_id` | `int` | Numeric paper ID. |
| `title` | `str` | Paper title. |
| `authors` | `list[str]` | Author names. |
| `date` | `str` | Publication date as exposed by NBER. |
| `abstract` | `str` | Paper abstract. |
| `url` | `str` or `None` | NBER paper URL when available. |
| `published_version` | `str` or `None` | Published-version text when available. |
| `topic` | `str` or `None` | Topic metadata when available. |
| `programs` | `str` or `None` | Program metadata when available. |

### NBERSearchResults

| Field | Type | Description |
| --- | --- | --- |
| `query` | `str` | Original query. |
| `total_results` | `int` | NBER result count. |
| `results` | `list[NBER]` | Papers on the current page. |
| `page` | `int` | Current page. |
| `per_page` | `int` | Results per page. |
| `start_date` | `str` or `None` | Applied start date. |
| `end_date` | `str` or `None` | Applied end date. |

### NBERFeedItem

| Field | Type | Description |
| --- | --- | --- |
| `paper_id` | `str` | Paper ID, for example `w35254`. |
| `title` | `str` | Paper title parsed from the RSS item. |
| `authors` | `list[str]` | Author names parsed from the RSS title. |
| `abstract` | `str` | RSS item description. |
| `url` | `str` | Canonical NBER paper URL without the RSS fragment. |
| `source_url` | `str` | Original RSS item URL. |
| `guid` | `str` | RSS item GUID. |

### NBERFeedFetchResult

| Field | Type | Description |
| --- | --- | --- |
| `source_url` | `str` | RSS feed URL. |
| `database_path` | `Path` | SQLite cache database path. |
| `total_fetched` | `int` | Number of RSS items fetched. |
| `new_count` | `int` | Number of fetched items that were not already in the cache. |
| `display_all` | `bool` | Whether returned items include all fetched items. |
| `items` | `list[NBERFeedItem]` | Items selected for display or structured output. |
| `max_items` | `int` or `None` | Display limit when provided. |

### NBERFeedCleanResult

| Field | Type | Description |
| --- | --- | --- |
| `database_path` | `Path` | SQLite cache database path. |
| `matched_count` | `int` | Number of cache records matching the clean criteria. |
| `deleted_count` | `int` | Number of cache records deleted. |
| `mode` | `str` | Clean mode: `days`, `all`, or `date-range`. |
| `days` | `int` or `None` | Day threshold for `days` mode. |
| `start_date` | `str` or `None` | Inclusive start date for `date-range` mode. |
| `end_date` | `str` or `None` | Inclusive end date for `date-range` mode. |
| `dry_run` | `bool` | Whether the operation only counted matching records. |

### NBERInfoCacheClearResult

| Field | Type | Description |
| --- | --- | --- |
| `database_path` | `Path` | SQLite cache database path. |
| `matched_count` | `int` | Number of cache records matching the clean criteria. |
| `deleted_count` | `int` | Number of cache records deleted. |
| `mode` | `str` | Clean mode: `days`, `all`, or `date-range`. |
| `days` | `int` or `None` | Day threshold for `days` mode. |
| `start_date` | `str` or `None` | Inclusive start date for `date-range` mode. |
| `end_date` | `str` or `None` | Inclusive end date for `date-range` mode. |
| `dry_run` | `bool` | Whether the operation only counted matching records. |

### InfoCacheSettings

| Field | Type | Description |
| --- | --- | --- |
| `cache_enabled` | `bool` | Global toggle for the `info_cache` lookup. |
| `cache_ttl_days` | `int` | Cache refresh interval in days. |

### InfoCacheLookupResult

| Field | Type | Description |
| --- | --- | --- |
| `paper` | `NBER` | The paper returned by the lookup. |
| `from_cache` | `bool` | `True` when the paper was served from the local `info_cache`. |

### DownloadFailure

| Field | Type | Description |
| --- | --- | --- |
| `paper_id` | `str` | The paper ID that failed to download. |
| `error` | `BaseException` | The exception raised during the download attempt. |

### DownloadBatchResult

| Field | Type | Description |
| --- | --- | --- |
| `paths` | `list[Path]` | Paths of successfully downloaded PDFs. |
| `failures` | `list[DownloadFailure]` | Failed downloads with their errors. |

## Formatter Helpers

Use formatter helpers when you want stable dictionaries for JSON output or MCP-style responses:

```python
from nber_cli import feed_results, info, related, search_results
```

- `info(paper)` returns core metadata.
- `related(paper)` returns related optional fields.
- `search_results(results)` returns a structured search payload.
- `feed_results(result)` returns a structured feed fetch payload.

For human-readable text output, use the text formatters from `nber_cli.formatters`:

```python
from nber_cli.formatters import feed_results_text, info_text, search_results_text
```

- `info_text(paper, include_all=False)` returns a formatted text string with paper details. Set `include_all=True` to include topic, programs, and published version.
- `search_results_text(results)` returns a formatted text string with search results.
- `feed_results_text(result)` returns a formatted text string with feed items.

## JSON Output Structures

`--format json` for `info`, `search`, and `feed fetch` produces the same dictionaries that the matching `*_results` formatters build. The JSON payload is always written to **stdout**, while the cache hit hint (for `info`) and any error message are written to **stderr**. This split lets scripts capture the payload with `>` redirection or pipes without picking up hint or error text.

### `info --format json`

Produced by `info(paper)` plus, when `--all` is set, `related(paper)` and a conditional `published_version` field:

| Field | Type | Always present | Notes |
| --- | --- | --- | --- |
| `id` | `str` | yes | `paper_id` formatted as `wNNNN`. |
| `title` | `str` | yes | Empty string when NBER does not expose one. |
| `authors` | `list[str]` | yes | Empty list when NBER does not expose any. |
| `date` | `str` | yes | Publication date as exposed by NBER; may be empty. |
| `abstract` | `str` | yes | Empty string when NBER does not expose an abstract. |
| `url` | `str` | no | Present only when the paper has a non-empty NBER URL. |
| `topic` | `str` | only with `--all` | `None`-able; emitted as `null` when unknown. |
| `programs` | `str` | only with `--all` | `None`-able; emitted as `null` when unknown. |
| `published_version` | `str` | only with `--all` and truthy | Omitted entirely when NBER does not expose one. |

### `search --format json`

Produced by `search_results(results)`:

| Field | Type | Always present | Notes |
| --- | --- | --- | --- |
| `query` | `str` | yes | The original query. |
| `total_results` | `int` | yes | NBER-reported total. |
| `page` | `int` | yes | Current page. |
| `per_page` | `int` | yes | Page size, one of `20`, `50`, `100`. |
| `start_date` | `str` | no | Present only when the call applied a start date. |
| `end_date` | `str` | no | Present only when the call applied an end date. |
| `results` | `list[object]` | yes | Per-paper dictionaries with the same fields as `search_result(paper)`. |

Each entry in `results` carries `id`, `title`, `authors`, `date`, `abstract`, and `url`. Unlike `info`, `url` is always emitted (possibly empty).

### `feed fetch --format json`

Produced by `feed_results(result)`:

| Field | Type | Notes |
| --- | --- | --- |
| `source_url` | `str` | The RSS feed URL that was fetched. |
| `database_path` | `str` | Absolute path of the SQLite database the items were written to. |
| `total_fetched` | `int` | Total items parsed from the feed. |
| `new_count` | `int` | Items that were not already in the local cache. |
| `display_all` | `bool` | `true` when `results` includes all fetched items, `false` when limited to new ones. |
| `max_items` | `int` or `null` | The cap from `--max-items` when provided. |
| `displayed_count` | `int` | Number of items actually included in `results`. |
| `results` | `list[object]` | Per-item dictionaries: `id`, `title`, `authors`, `abstract`, `url`, `source_url`, `guid`. |

### Compatibility Notes

The JSON structures are the published output contract used by both the CLI and the MCP tools. Additive fields (new optional keys) may appear in a minor version. Renaming or removing an existing key, or changing the type of an existing field, is treated as a breaking change. Scripts that consume `--format json` should treat unknown keys as ignored data rather than asserting on the full key set.
