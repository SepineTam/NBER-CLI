# Python API

NBER-CLI 暴露了与 CLI 相同核心能力的 Python 函数。由于查询、搜索和下载都涉及网络 I/O，这些 API 是异步的。

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
from nber_cli import info, related, search_results
```

- `info(paper)` 返回核心元数据。
- `related(paper)` 返回可选相关字段。
- `search_results(results)` 返回结构化搜索结果。

如果需要适合人读的文本输出，可以使用文本格式化器：

```python
from nber_cli import info_text, search_results_text
```

- `info_text(paper, include_all=False)` 返回格式化的论文详情文本。设置 `include_all=True` 可包含 topic、programs 和 published version。
- `search_results_text(results)` 返回格式化的搜索结果文本。
