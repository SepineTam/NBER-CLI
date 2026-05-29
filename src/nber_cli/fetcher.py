#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : fetcher.py

from __future__ import annotations

import asyncio
import html
import json
import re
from datetime import date
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from aiohttp import ClientSession, ClientTimeout

from .core.models import NBER, NBERSearchResults

_REQUEST_TIMEOUT_SECONDS = 30
_REQUEST_TIMEOUT = ClientTimeout(total=_REQUEST_TIMEOUT_SECONDS)
_NBER_SEARCH_API = "https://www.nber.org/api/v1/working_page_listing/contentType/working_paper/_/_/search"
_NBER_BASE_URL = "https://www.nber.org"
_SUPPORTED_SEARCH_PAGE_SIZES = {20, 50, 100}


async def get_nber(nber_id: int, session: ClientSession | None = None) -> NBER:
    _url = f"https://www.nber.org/papers/w{nber_id:04d}"
    if session is not None:
        page = await _load_page(_url, session)
    else:
        page = await asyncio.to_thread(_load_page_sync, _url)
    return parse_page(page)


async def search_nber(
    query: str,
    *,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    page: int = 1,
    per_page: int = 20,
    session: ClientSession | None = None,
) -> NBERSearchResults:
    params = _build_search_params(
        query=query,
        start_date=start_date,
        end_date=end_date,
        page=page,
        per_page=per_page,
    )
    if session is not None:
        payload = await _load_json(_NBER_SEARCH_API, session, params)
    else:
        payload = await asyncio.to_thread(_load_json_sync, _NBER_SEARCH_API, params)
    return _parse_search_payload(payload, params)


async def _load_page(url: str, session: ClientSession) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    async with session.get(url, headers=headers) as resp:
        resp.raise_for_status()
        return await resp.text()


async def _load_json(url: str, session: ClientSession, params: dict[str, Any]) -> dict[str, Any]:
    headers = {"User-Agent": "Mozilla/5.0"}
    async with session.get(url, headers=headers, params=params) as resp:
        resp.raise_for_status()
        return await resp.json()


def _load_page_sync(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
        encoding = response.headers.get_content_charset("utf-8")
        return response.read().decode(encoding)


def _load_json_sync(url: str, params: dict[str, Any]) -> dict[str, Any]:
    query_string = urlencode(params)
    page = _load_page_sync(f"{url}?{query_string}")
    return json.loads(page)


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


def _build_search_params(
    query: str,
    *,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    page: int = 1,
    per_page: int = 20,
    today: date | None = None,
) -> dict[str, Any]:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("query must not be empty")
    if page < 1:
        raise ValueError("page must be greater than 0")
    if per_page not in _SUPPORTED_SEARCH_PAGE_SIZES:
        raise ValueError("per_page must be one of 20, 50, or 100")

    start_date_value = _normalize_date(start_date)
    end_date_value = _normalize_date(end_date)
    if start_date_value is not None and end_date_value is None:
        end_date_value = (today or date.today()).isoformat()
    if start_date_value is not None and end_date_value is not None and start_date_value > end_date_value:
        raise ValueError("start_date must be on or before end_date")

    params: dict[str, Any] = {
        "page": page,
        "perPage": per_page,
        "q": cleaned_query,
    }
    if start_date_value is not None:
        params["startDate"] = start_date_value
    if end_date_value is not None:
        params["endDate"] = end_date_value
    return params


def _normalize_date(value: date | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()

    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError(f"invalid date '{value}', expected YYYY-MM-DD") from error


def _parse_search_payload(
    payload: dict[str, Any], params: dict[str, Any]
) -> NBERSearchResults:
    raw_results = payload.get("results", [])
    if not isinstance(raw_results, list):
        raw_results = []

    results = [_parse_search_result(result) for result in raw_results]
    return NBERSearchResults(
        query=str(params["q"]),
        total_results=int(payload.get("totalResults", 0) or 0),
        results=results,
        page=int(params["page"]),
        per_page=int(params["perPage"]),
        start_date=params.get("startDate"),
        end_date=params.get("endDate"),
    )


def _parse_search_result(raw_result: dict[str, Any]) -> NBER:
    url = str(raw_result.get("url") or "")
    paper_id_match = re.search(r"/papers/w(\d+)", url)
    paper_id = int(paper_id_match.group(1)) if paper_id_match else 0
    full_url = f"{_NBER_BASE_URL}{url}" if url.startswith("/") else url
    authors = [_clean_html_text(author) for author in raw_result.get("authors", [])]

    return NBER(
        paper_id=paper_id,
        title=_clean_html_text(raw_result.get("title")),
        authors=[author for author in authors if author],
        date=_clean_html_text(raw_result.get("displaydate")),
        abstract=_clean_html_text(raw_result.get("abstract")),
        url=full_url,
    )


def _clean_html_text(value: Any) -> str:
    if value is None:
        return ""
    text = re.sub(r"<[^>]+>", "", str(value))
    return " ".join(html.unescape(text).split())
