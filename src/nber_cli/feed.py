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
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag

from .core.models import NBERFeedFetchResult, NBERFeedItem
from .fetcher import _load_text_sync

NBER_FEED_URL = "https://www.nber.org/rss/new.xml"
NBER_CLI_DIR_NAME = ".nber-cli"
NBER_CLI_CONFIG_NAME = "config.json"
NBER_FEED_DB_NAME = "feed.db"
FEED_SCHEMA_VERSION = 1


def init_feed_database(db_path: Path | str | None = None) -> Path:
    resolved_db_path = _normalize_db_path(db_path or _default_feed_db_path())
    _ensure_feed_schema(resolved_db_path)
    _write_feed_config(resolved_db_path)
    return resolved_db_path


def fetch_feed(display_all: bool = False, db_path: Path | str | None = None) -> NBERFeedFetchResult:
    resolved_db_path = _normalize_db_path(db_path or _configured_feed_db_path())
    _ensure_feed_schema(resolved_db_path)

    xml_text = _load_text_sync(NBER_FEED_URL)
    feed_items = parse_feed_xml(xml_text)
    seen_at = _utc_now()
    new_items = _save_feed_items(resolved_db_path, feed_items, seen_at)
    output_items = feed_items if display_all else new_items

    return NBERFeedFetchResult(
        source_url=NBER_FEED_URL,
        database_path=resolved_db_path,
        total_fetched=len(feed_items),
        new_count=len(new_items),
        display_all=display_all,
        items=output_items,
    )


def parse_feed_xml(xml_text: str) -> list[NBERFeedItem]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as error:
        raise ValueError("invalid NBER RSS XML") from error

    items: list[NBERFeedItem] = []
    for raw_item in root.findall("./channel/item"):
        raw_title = _clean_feed_text(raw_item.findtext("title"))
        title, authors = _parse_feed_title(raw_title)
        source_url = _clean_feed_text(raw_item.findtext("link"))
        guid = _clean_feed_text(raw_item.findtext("guid")) or source_url
        paper_id = _extract_paper_id(source_url) or _extract_paper_id(guid)
        if not paper_id:
            raise ValueError("NBER RSS item is missing a paper ID")

        url, _fragment = urldefrag(source_url)
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

    return items


def get_feed_database_path() -> Path:
    return _normalize_db_path(_configured_feed_db_path())


def _save_feed_items(
    db_path: Path,
    feed_items: list[NBERFeedItem],
    seen_at: str,
) -> list[NBERFeedItem]:
    new_items: list[NBERFeedItem] = []

    with sqlite3.connect(db_path) as connection:
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


def _ensure_feed_schema(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feed_items (
                paper_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors_json TEXT NOT NULL,
                abstract TEXT NOT NULL,
                url TEXT NOT NULL,
                source_url TEXT NOT NULL,
                guid TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feed_fetches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                total_count INTEGER NOT NULL,
                new_count INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_feed_items_last_seen_at
            ON feed_items(last_seen_at)
            """
        )
        connection.execute(f"PRAGMA user_version = {FEED_SCHEMA_VERSION}")


def _write_feed_config(db_path: Path) -> None:
    config_path = _default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = _read_user_config(config_path)
    feed_config = config.get("feed")
    if not isinstance(feed_config, dict):
        feed_config = {}
    feed_config["db-path"] = str(db_path)
    config["feed"] = feed_config
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")


def _configured_feed_db_path() -> Path:
    config = _read_user_config(_default_config_path())
    feed_config = config.get("feed")
    if isinstance(feed_config, dict):
        db_path = feed_config.get("db-path")
        if isinstance(db_path, str) and db_path.strip():
            return Path(db_path)
    return _default_feed_db_path()


def _read_user_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}

    try:
        config = json.loads(config_path.read_text())
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid config file: {config_path}") from error

    if not isinstance(config, dict):
        raise ValueError(f"invalid config file: {config_path}")
    return config


def _default_config_path() -> Path:
    return Path.home() / NBER_CLI_DIR_NAME / NBER_CLI_CONFIG_NAME


def _default_feed_db_path() -> Path:
    return Path.home() / NBER_CLI_DIR_NAME / NBER_FEED_DB_NAME


def _normalize_db_path(db_path: Path | str) -> Path:
    path = Path(db_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve(strict=False)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_feed_title(raw_title: str) -> tuple[str, list[str]]:
    title, separator, authors_text = raw_title.rpartition(" -- by ")
    if not separator:
        return raw_title, []

    authors = [author.strip() for author in authors_text.split(",") if author.strip()]
    return title.strip(), authors


def _extract_paper_id(url: str) -> str | None:
    match = re.search(r"/papers/(w\d+)", url)
    return match.group(1) if match else None


def _clean_feed_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(html.unescape(value).split())
