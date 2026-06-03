# Python API

NBER-CLI exposes the same core functionality as importable Python functions. The API is asynchronous because lookup, search, and downloads perform network I/O.

Feed cache helpers are synchronous because they perform local SQLite work and a synchronous RSS fetch.

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

## Work with the Feed Cache

Initialize the default feed cache:

```python
from nber_cli import init_feed_database

db_path = init_feed_database()
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

Move the feed cache database:

```python
from pathlib import Path

from nber_cli import migrate_feed_database

old_path, new_path = migrate_feed_database(Path("~/data/nber-feed.db"))
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

For human-readable text output, use the text formatters:

```python
from nber_cli import info_text, search_results_text
```

- `info_text(paper, include_all=False)` returns a formatted text string with paper details. Set `include_all=True` to include topic, programs, and published version.
- `search_results_text(results)` returns a formatted text string with search results.
