# Python API

NBER-CLI exposes the same core functionality as importable Python functions. The API is asynchronous because lookup, search, and downloads perform network I/O.

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

## Formatter Helpers

Use formatter helpers when you want stable dictionaries for JSON output or MCP-style responses:

```python
from nber_cli import info, related, search_results
```

- `info(paper)` returns core metadata.
- `related(paper)` returns related optional fields.
- `search_results(results)` returns a structured search payload.
