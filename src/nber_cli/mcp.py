#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : mcp.py

from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from . import db
from .fetcher import get_nber, search_nber
from .formatters import info, related, search_results
from .download import download_paper as download_paper_to_dir, download_paper_to_file

nber_mcp = FastMCP("nber_mcp")


def _parse_paper_id(paper_id_str: str) -> int:
    cleaned = paper_id_str.lower().removeprefix("w")
    return int(cleaned)


@nber_mcp.tool()
async def get_paper_info(paper_id: str, include_all: bool = True) -> dict:
    """Fetch metadata and abstract for an NBER working paper by ID.

    Args:
        paper_id: Paper ID, e.g. 'w1234' or '1234'
        include_all: Whether to include related fields and published version

    Returns:
        Dictionary containing paper metadata.
    """
    nber_id = _parse_paper_id(paper_id)
    paper = db.read_info_cache(None, nber_id)
    if paper is None:
        paper = await get_nber(nber_id)
        db.write_info_cache(None, paper)
    else:
        db.touch_info_cache(None, nber_id)
    db.record_info(None, nber_id)

    result = info(paper)
    if include_all:
        result.update(related(paper))
        if paper.published_version:
            result["published_version"] = paper.published_version

    return result


@nber_mcp.tool()
async def search_papers(
    query: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """Search NBER working papers by keyword with optional date constraints.

    Args:
        query: Title, number, author, abstract, or keyword.
        start_date: Optional earliest working paper date, formatted YYYY-MM-DD.
        end_date: Optional latest working paper date, formatted YYYY-MM-DD.
        page: Result page to fetch.
        per_page: Number of results per page.

    Returns:
        Dictionary containing result metadata and papers.
    """
    results = await search_nber(
        query,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page,
    )
    return search_results(results)


@nber_mcp.tool()
async def download_paper(paper_id: str, output_path: Optional[str] = None) -> bool:
    """Download an NBER working paper as a PDF.

    Args:
        paper_id: Paper ID, e.g. 'w1234' or '1234'
        output_path: Explicit output file path. If not provided, saves as <paper_id>.pdf in current directory.

    Returns:
        True if download succeeds. On failure, an exception is raised and propagated to the caller.
    """
    if output_path:
        await download_paper_to_file(paper_id, Path(output_path))
    else:
        await download_paper_to_dir(paper_id, Path.cwd())

    return True
