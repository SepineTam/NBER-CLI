#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : formatters.py

import textwrap
from typing import Dict

from .core.models import NBER, NBERSearchResults

_TEXT_WIDTH = 88


def paper_id_str(paper: NBER) -> str:
    return f"w{paper.paper_id:04d}"


def info(paper: NBER) -> Dict:
    result = {
        "id": paper_id_str(paper),
        "title": paper.title,
        "authors": paper.authors,
        "date": paper.date,
        "abstract": paper.abstract,
    }
    if paper.url:
        result["url"] = paper.url
    return result


def related(paper: NBER) -> Dict[str, str | None]:
    return {
        "topic": paper.topic,
        "programs": paper.programs,
    }


def search_result(paper: NBER) -> Dict:
    return {
        "id": paper_id_str(paper),
        "title": paper.title,
        "authors": paper.authors,
        "date": paper.date,
        "abstract": paper.abstract,
        "url": paper.url,
    }


def search_results(search: NBERSearchResults) -> Dict:
    return {
        "query": search.query,
        "total_results": search.total_results,
        "page": search.page,
        "per_page": search.per_page,
        "start_date": search.start_date,
        "end_date": search.end_date,
        "results": [search_result(result) for result in search.results],
    }


def info_text(paper: NBER, include_all: bool = False) -> str:
    lines = [
        f"{paper_id_str(paper)} | {paper.title}",
        f"Date: {paper.date or 'Unknown'}",
        f"Authors: {_join_authors(paper.authors)}",
    ]
    if paper.url:
        lines.append(f"URL: {paper.url}")
    if include_all:
        if paper.topic:
            lines.append(f"Topic: {paper.topic}")
        if paper.programs:
            lines.append(f"Programs: {paper.programs}")
        if paper.published_version:
            lines.append(f"Published version: {paper.published_version}")
    if paper.abstract:
        lines.extend(["", "Abstract:", _wrap_text(paper.abstract)])
    return "\n".join(lines)


def search_results_text(search: NBERSearchResults) -> str:
    date_range = _format_date_range(search.start_date, search.end_date)
    lines = [
        f"Query: {search.query}",
        f"Total results: {search.total_results:,}",
        f"Page: {search.page} | Per page: {search.per_page}",
        f"Date range: {date_range}",
        "",
    ]

    if not search.results:
        lines.append("No results found.")
        return "\n".join(lines)

    lines.append("Results:")
    lines.extend(_search_result_line(result) for result in search.results)
    return "\n".join(lines)


def _search_result_line(paper: NBER) -> str:
    parts = [
        paper_id_str(paper),
        paper.date or "Unknown date",
        paper.title,
        _join_authors(paper.authors),
    ]
    if paper.url:
        parts.append(paper.url)
    return " | ".join(parts)


def _format_date_range(start_date: str | None, end_date: str | None) -> str:
    if start_date and end_date:
        return f"{start_date} to {end_date}"
    if start_date:
        return f"{start_date} to any time"
    if end_date:
        return f"any time to {end_date}"
    return "Any time"


def _join_authors(authors: list[str]) -> str:
    return ", ".join(authors) if authors else "Unknown"


def _wrap_text(text: str) -> str:
    return textwrap.fill(text, width=_TEXT_WIDTH)
