#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : download.py

from __future__ import annotations

import asyncio
import re
import ssl
from pathlib import Path
from typing import cast

import certifi
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from fake_useragent import UserAgent

from .config import NBER_CLI_CONFIG
from .core.models import DownloadBatchResult, DownloadFailure
from .fetcher import _retry_async

_USER_AGENT = UserAgent()


def _is_within_cwd(path: Path) -> bool:
    try:
        path.absolute().relative_to(Path.cwd().absolute())
        return True
    except ValueError:
        return False


def _validate_paper_id(paper_id: str) -> None:
    if not re.fullmatch(r"w?\d+", paper_id):
        raise ValueError(f"invalid paper ID: {paper_id}")


def _validate_download_path(path: Path) -> None:
    if not _is_within_cwd(path):
        raise ValueError(f"download path {path} is outside the current directory")


def _create_connector() -> TCPConnector:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    return TCPConnector(
        ssl=ssl_context,
        limit=NBER_CLI_CONFIG.download_connection_limit,
        limit_per_host=NBER_CLI_CONFIG.download_connection_limit_per_host,
    )


async def download_paper_to_file(
    paper_id: str,
    output_file: Path,
    session: ClientSession | None = None,
    *,
    restrict_dir: bool = True,
) -> Path:
    """Download a single NBER paper to an explicit output file path.

    If *session* is provided, it is reused. Otherwise a new session is created
    and closed before the function returns.
    """
    _validate_paper_id(paper_id)
    if restrict_dir:
        _validate_download_path(output_file)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://www.nber.org/papers/{paper_id}.pdf"
    headers = {"User-Agent": _USER_AGENT.random}

    async def _fetch(sess: ClientSession) -> bytes:
        async with sess.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.read()

    if session is not None:
        content = await _retry_async(lambda: _fetch(session))
    else:
        connector = _create_connector()
        timeout = ClientTimeout(total=NBER_CLI_CONFIG.request_timeout_seconds)
        async with ClientSession(
            timeout=timeout, connector=connector, headers=headers
        ) as base_session:
            content = await _retry_async(lambda: _fetch(base_session))

    output_file.write_bytes(content)
    return output_file


async def download_paper(
    paper_id: str,
    save_base: Path,
    session: ClientSession | None = None,
    *,
    restrict_dir: bool = True,
) -> Path:
    """Download a single paper into a base directory using <paper_id>.pdf naming.

    If *session* is provided, it is reused. Otherwise a new session is created
    and closed before the function returns.
    """
    _validate_paper_id(paper_id)
    output_file = save_base / f"{paper_id}.pdf"
    if restrict_dir:
        _validate_download_path(output_file)
    return await download_paper_to_file(
        paper_id, output_file, session=session, restrict_dir=restrict_dir
    )


async def download_multiple_papers(
    paper_ids: list[str],
    save_base: Path,
    *,
    restrict_dir: bool = True,
    concurrency: int | None = None,
) -> DownloadBatchResult:
    """Download multiple papers concurrently into the same base directory."""
    for pid in paper_ids:
        _validate_paper_id(pid)
    if restrict_dir:
        _validate_download_path(save_base / "x.pdf")

    max_concurrency = concurrency if concurrency is not None else NBER_CLI_CONFIG.download_concurrency
    semaphore = asyncio.Semaphore(max_concurrency)

    connector = _create_connector()
    timeout = ClientTimeout(total=NBER_CLI_CONFIG.request_timeout_seconds)
    headers = {"User-Agent": _USER_AGENT.random}
    async with ClientSession(
        timeout=timeout, connector=connector, headers=headers
    ) as base_session:
        async def _download_limited(paper_id: str) -> Path:
            async with semaphore:
                return await download_paper(
                    paper_id=paper_id,
                    save_base=save_base,
                    session=base_session,
                    restrict_dir=restrict_dir,
                )

        tasks = [
            _download_limited(paper_id)
            for paper_id in paper_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    paths: list[Path] = []
    failures: list[DownloadFailure] = []
    for paper_id, result in zip(paper_ids, results):
        if isinstance(result, (Exception, asyncio.CancelledError)):
            failures.append(DownloadFailure(paper_id=paper_id, error=result))
        else:
            paths.append(cast(Path, result))
    return DownloadBatchResult(paths=paths, failures=failures)
