#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : fetcher.py

import re

from aiohttp import ClientSession, ClientTimeout

from .core.models import NBER

_REQUEST_TIMEOUT = ClientTimeout(total=30)


async def get_nber(nber_id: int, session: ClientSession | None = None) -> NBER:
    _url = f"https://www.nber.org/papers/w{nber_id:04d}"
    if session is not None:
        page = await _load_page(_url, session)
    else:
        async with ClientSession(timeout=_REQUEST_TIMEOUT) as new_session:
            page = await _load_page(_url, new_session)
    return parse_page(page)


async def _load_page(url: str, session: ClientSession) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    async with session.get(url, headers=headers) as resp:
        resp.raise_for_status()
        return await resp.text()


def parse_page(page: str) -> NBER:
    title_match = re.search(r'<meta name="citation_title" content="([^"]*)"', page)
    title = title_match.group(1) if title_match else ""

    authors = re.findall(r'<meta name="citation_author" content="([^"]*)"', page)

    date_match = re.search(r'<meta name="citation_publication_date" content="([^"]*)"', page)
    date = date_match.group(1) if date_match else ""

    paper_id_match = re.search(
        r'<meta name="citation_technical_report_number" content="([^"]*)"',
        page,
    )
    paper_id_str = paper_id_match.group(1) if paper_id_match else ""
    paper_id = int(paper_id_str.replace("w", "").lstrip("0") or "0")

    abstract = _extract_abstract(page)
    published_version = _extract_published_version(page)

    return NBER(
        paper_id=paper_id,
        title=title,
        authors=authors,
        date=date,
        abstract=abstract,
        published_version=published_version,
    )


def _extract_abstract(page: str) -> str:
    intro_match = re.search(
        r'<div class="page-header__intro-inner">\s*<p>(.*?)</p>',
        page,
        re.DOTALL,
    )
    if intro_match:
        text = intro_match.group(1)
        text = re.sub(r"<[^>]+>", "", text)
        return " ".join(text.split())
    return ""


def _extract_published_version(page: str) -> str | None:
    pub_match = re.search(
        r'Published Versions</h2>\s*<p>(.*?)</p>',
        page,
        re.DOTALL,
    )
    if pub_match:
        text = pub_match.group(1)
        text = re.sub(r"<[^>]+>", "", text)
        return " ".join(text.split())
    return None
