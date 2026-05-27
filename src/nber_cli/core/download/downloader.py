"""Download utilities for NBER papers."""

from __future__ import annotations

import asyncio
import ssl
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import certifi
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from aiohttp_retry import ExponentialRetry, RetryClient
from fake_useragent import UserAgent

MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 30


@dataclass
class DownloadFailure:
    paper_id: str
    error: BaseException


@dataclass
class DownloadBatchResult:
    paths: list[Path]
    failures: list[DownloadFailure]


async def download_paper_to_file(paper_id: str, output_file: Path) -> Path:
    """Download a single NBER paper to an explicit output file path."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://www.nber.org/papers/{paper_id}.pdf"
    headers = {"User-Agent": UserAgent().random}
    retry_options = ExponentialRetry(attempts=MAX_RETRIES)
    timeout = ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = TCPConnector(ssl=ssl_context)

    async with ClientSession(
        timeout=timeout, connector=connector, headers=headers
    ) as base_session:
        async with RetryClient(
            client_session=base_session,
            retry_options=retry_options,
        ) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()

    output_file.write_bytes(content)
    return output_file


async def download_paper(paper_id: str, save_base: Path) -> Path:
    """Download a single paper into a base directory using <paper_id>.pdf naming."""
    return await download_paper_to_file(paper_id, save_base / f"{paper_id}.pdf")


async def download_multiple_papers(
    paper_ids: list[str], save_base: Path
) -> DownloadBatchResult:
    """Download multiple papers concurrently into the same base directory."""
    tasks = [download_paper(paper_id=paper_id, save_base=save_base) for paper_id in paper_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    paths: list[Path] = []
    failures: list[DownloadFailure] = []
    for paper_id, result in zip(paper_ids, results):
        if isinstance(result, (Exception, asyncio.CancelledError)):
            failures.append(DownloadFailure(paper_id=paper_id, error=result))
        else:
            paths.append(cast(Path, result))
    return DownloadBatchResult(paths=paths, failures=failures)
