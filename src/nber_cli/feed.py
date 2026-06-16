#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : feed.py

from __future__ import annotations

import html
import re
import sqlite3
from defusedxml import ElementTree as ET
from defusedxml.common import EntitiesForbidden
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urldefrag

from . import db
from .core.models import NBERFeedCleanResult, NBERFeedFetchResult, NBERFeedItem
from .fetcher import _load_text_sync

NBER_FEED_URL = "https://www.nber.org/rss/new.xml"
_UNESCAPED_TEXT_LESS_THAN = re.compile(r"<(?=[\s\d])")
_FEED_TEXT_ELEMENT = re.compile(
    r"(<(?P<tag>title|description)>)(?P<text>.*?)(</(?P=tag)>)",
    re.DOTALL,
)
_FEED_AUTHOR_SEPARATOR = re.compile(r"\s*(?:,|ⓡ)\s*")


def init_feed_database(db_path: Path | str | None = None) -> Path:
    return db.init_database(db_path)


def migrate_feed_database(new_db_path: Path | str) -> tuple[Path, Path]:
    return db.migrate_database(new_db_path)


def get_feed_database_path() -> Path:
    return db.get_database_path()


def clean_feed_cache(
    *,
    days: int | None = None,
    delete_all: bool = False,
    start_date: str | None = None,
    end_date: str | None = None,
    dry_run: bool = False,
    db_path: Path | str | None = None,
) -> NBERFeedCleanResult:
    resolved_db_path = db.get_database_path(db_path)
    if not resolved_db_path.exists():
        raise ValueError(f"feed database does not exist: {resolved_db_path}")

    condition, parameters, mode = _build_feed_cache_clean_condition(
        days=days,
        delete_all=delete_all,
        start_date=start_date,
        end_date=end_date,
    )
    with sqlite3.connect(resolved_db_path) as connection:
        db._ensure_full_schema_on_connection(connection)
        matched_count = connection.execute(
            f"SELECT COUNT(*) FROM feed_items WHERE {condition}",
            parameters,
        ).fetchone()[0]

        deleted_count = 0
        if not dry_run and matched_count:
            cursor = connection.execute(
                f"DELETE FROM feed_items WHERE {condition}",
                parameters,
            )
            deleted_count = cursor.rowcount if cursor.rowcount >= 0 else matched_count

    return NBERFeedCleanResult(
        database_path=resolved_db_path,
        matched_count=matched_count,
        deleted_count=deleted_count,
        mode=mode,
        days=(30 if days is None else days) if mode == "days" else None,
        start_date=start_date if mode == "date-range" else None,
        end_date=end_date if mode == "date-range" else None,
        dry_run=dry_run,
    )


def fetch_feed(
    display_all: bool = False,
    db_path: Path | str | None = None,
    max_items: int | None = None,
) -> NBERFeedFetchResult:
    if max_items is not None and max_items < 0:
        raise ValueError("max_items must be 0 or greater")

    resolved_db_path = db.get_database_path(db_path)
    resolved_db_path.parent.mkdir(parents=True, exist_ok=True)
    db._ensure_full_schema(resolved_db_path)

    xml_text = _load_text_sync(NBER_FEED_URL)
    feed_items = parse_feed_xml(xml_text)
    seen_at = db._utc_now()
    with sqlite3.connect(resolved_db_path) as connection:
        db._ensure_full_schema_on_connection(connection)
        new_items = _save_feed_items(connection, feed_items, seen_at)
    output_items = feed_items if display_all else new_items
    if max_items is not None:
        output_items = output_items[:max_items]

    return NBERFeedFetchResult(
        source_url=NBER_FEED_URL,
        database_path=resolved_db_path,
        total_fetched=len(feed_items),
        new_count=len(new_items),
        display_all=display_all,
        max_items=max_items,
        items=output_items,
    )


def parse_feed_xml(xml_text: str) -> list[NBERFeedItem]:
    try:
        root = ET.fromstring(xml_text)
    except EntitiesForbidden as error:
        raise ValueError("invalid NBER RSS XML") from error
    except ET.ParseError as error:
        repaired_xml_text = _repair_unescaped_text_less_than(xml_text)
        if repaired_xml_text == xml_text:
            raise _invalid_feed_xml_error(error) from error
        try:
            root = ET.fromstring(repaired_xml_text)
        except (ET.ParseError, EntitiesForbidden) as repaired_error:
            raise _invalid_feed_xml_error(repaired_error) from repaired_error

    items: list[NBERFeedItem] = []
    for raw_item in root.findall("./channel/item"):
        try:
            raw_title = _clean_feed_text(raw_item.findtext("title"))
            title, authors = _parse_feed_title(raw_title)
            source_url = _clean_feed_text(raw_item.findtext("link"))
            guid = _clean_feed_text(raw_item.findtext("guid")) or source_url
            paper_id = _extract_paper_id(source_url) or _extract_paper_id(guid)
            if not paper_id:
                continue

            url, _ = urldefrag(source_url)
            items.append(
                NBERFeedItem(
                    paper_id=paper_id,
                    title=title,
                    authors=authors,
                    abstract=_clean_feed_text(raw_item.findtext("description")),
                    url=url or source_url,
                    source_url=source_url,
                    guid=guid,
                )
            )
        except Exception:
            continue

    return items


def _repair_unescaped_text_less_than(xml_text: str) -> str:
    def repair_element(match: re.Match[str]) -> str:
        repaired_text = _UNESCAPED_TEXT_LESS_THAN.sub("&lt;", match.group("text"))
        return f"{match.group(1)}{repaired_text}{match.group(4)}"

    return _FEED_TEXT_ELEMENT.sub(repair_element, xml_text)


def _invalid_feed_xml_error(error: Exception) -> ValueError:
    position = getattr(error, "position", None)
    if position is None:
        return ValueError("invalid NBER RSS XML")
    line, column = position
    return ValueError(f"invalid NBER RSS XML at line {line}, column {column}")


def _save_feed_items(
    connection: sqlite3.Connection,
    feed_items: list[NBERFeedItem],
    seen_at: str,
) -> list[NBERFeedItem]:
    import json

    new_items: list[NBERFeedItem] = []

    for feed_item in feed_items:
        is_new_item = not _feed_item_exists(connection, feed_item.paper_id)
        connection.execute(
            """
            INSERT INTO feed_items (
                paper_id,
                title,
                authors_json,
                abstract,
                url,
                source_url,
                guid,
                first_seen_at,
                last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(paper_id) DO UPDATE SET
                title = excluded.title,
                authors_json = excluded.authors_json,
                abstract = excluded.abstract,
                url = excluded.url,
                source_url = excluded.source_url,
                guid = excluded.guid,
                last_seen_at = excluded.last_seen_at
            """,
            (
                feed_item.paper_id,
                feed_item.title,
                json.dumps(feed_item.authors, ensure_ascii=False),
                feed_item.abstract,
                feed_item.url,
                feed_item.source_url,
                feed_item.guid,
                seen_at,
                seen_at,
            ),
        )
        if is_new_item:
            new_items.append(feed_item)

    connection.execute(
        """
        INSERT INTO feed_fetches (source_url, fetched_at, total_count, new_count)
        VALUES (?, ?, ?, ?)
        """,
        (NBER_FEED_URL, seen_at, len(feed_items), len(new_items)),
    )

    return new_items


def _feed_item_exists(connection: sqlite3.Connection, paper_id: str) -> bool:
    row = connection.execute(
        """
        SELECT 1 FROM feed_items WHERE paper_id = ?
        """,
        (paper_id,),
    ).fetchone()
    return row is not None


def _build_feed_cache_clean_condition(
    *,
    days: int | None,
    delete_all: bool,
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, tuple[str, ...], str]:
    has_date_filter = start_date is not None or end_date is not None
    mode_count = sum((days is not None, delete_all, has_date_filter))
    if mode_count > 1:
        raise ValueError("choose only one feed cache clean mode")

    if delete_all:
        return "1 = 1", (), "all"

    if has_date_filter:
        return _build_feed_cache_date_condition(start_date, end_date)

    clean_days = 30 if days is None else days
    if clean_days <= 0:
        raise ValueError("days must be a positive integer")
    cutoff_datetime = datetime.fromisoformat(db._utc_now()) - _timedelta_days(clean_days)
    return "last_seen_at < ?", (cutoff_datetime.isoformat(timespec="seconds"),), "days"


def _build_feed_cache_date_condition(
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, tuple[str, ...], str]:
    if start_date is not None and end_date is None:
        raise ValueError("end-date is required when start-date is provided")
    if end_date is None:
        raise ValueError("end-date is required for date range clean mode")

    parsed_start_date = _parse_feed_cache_date(start_date) if start_date else None
    parsed_end_date = _parse_feed_cache_date(end_date)
    if parsed_start_date and parsed_start_date > parsed_end_date:
        raise ValueError("start-date must be on or before end-date")

    if start_date is None:
        return "substr(last_seen_at, 1, 10) <= ?", (end_date,), "date-range"

    return (
        "substr(last_seen_at, 1, 10) >= ? AND substr(last_seen_at, 1, 10) <= ?",
        (start_date, end_date),
        "date-range",
    )


def _parse_feed_cache_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError(f"invalid date '{value}', expected YYYY-MM-DD") from error


def _timedelta_days(days: int):
    from datetime import timedelta

    return timedelta(days=days)


def _parse_feed_title(raw_title: str) -> tuple[str, list[str]]:
    title, separator, authors_text = raw_title.rpartition(" -- by ")
    if not separator:
        return raw_title, []

    authors = [
        author.strip()
        for author in _FEED_AUTHOR_SEPARATOR.split(authors_text)
        if author.strip()
    ]
    return title.strip(), authors


def _extract_paper_id(url: str) -> str | None:
    import re

    match = re.search(r"/papers/(w\d+)", url)
    return match.group(1) if match else None


def _clean_feed_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(html.unescape(value).split())
