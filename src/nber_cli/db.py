#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : db.py

from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from . import config_store
from .core.models import NBER, NBERInfoCacheClearResult

NBER_CLI_DIR_NAME = config_store.NBER_CLI_DIR_NAME
NBER_CLI_CONFIG_NAME = config_store.NBER_CLI_CONFIG_NAME
NBER_DB_NAME = config_store.NBER_DB_NAME
LEGACY_DB_NAME = config_store.LEGACY_DB_NAME
SCHEMA_VERSION = 2


def _validate_db_path(path: Path) -> None:
    if sys.platform == "win32":
        return
    try:
        path.resolve(strict=False).relative_to(Path.home().resolve(strict=False))
    except ValueError:
        raise ValueError(f"database path must be within the home directory: {path}")


def init_database(db_path: Path | str | None = None) -> Path:
    resolved_db_path = _normalize_db_path(db_path or _configured_db_path())
    _validate_db_path(resolved_db_path)
    _ensure_full_schema(resolved_db_path)
    _write_config(resolved_db_path, SCHEMA_VERSION)
    return resolved_db_path


def migrate_database(new_db_path: Path | str) -> tuple[Path, Path]:
    old_db_path = get_database_path()
    resolved_new_db_path = _normalize_db_path(new_db_path)
    _validate_db_path(resolved_new_db_path)

    if old_db_path == resolved_new_db_path:
        raise ValueError("new database path must be different from current path")
    if not old_db_path.exists():
        raise ValueError(f"database does not exist: {old_db_path}")

    move_pairs = _db_move_pairs(old_db_path, resolved_new_db_path)
    for _, target in move_pairs:
        if target.exists():
            raise ValueError(f"target database file already exists: {target}")

    resolved_new_db_path.parent.mkdir(parents=True, exist_ok=True)
    for source, target in move_pairs:
        shutil.move(str(source), str(target))

    _write_config(resolved_new_db_path, SCHEMA_VERSION)
    return old_db_path, resolved_new_db_path


def get_database_path(db_path: Path | str | None = None) -> Path:
    return _normalize_db_path(db_path or _configured_db_path())


def get_schema_version(db_path: Path | str | None = None) -> int:
    resolved_db_path = get_database_path(db_path)
    if not resolved_db_path.exists():
        return 0
    with sqlite3.connect(resolved_db_path) as connection:
        return _read_user_version(connection)


def _ensure_full_schema(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        current_version = _read_user_version(connection)
        if current_version == 0:
            _create_all_tables(connection)
        elif current_version == 1:
            _upgrade_v1_to_v2(connection)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def _create_all_tables(connection: sqlite3.Connection) -> None:
    _create_feed_tables(connection)
    _create_query_log_table(connection)
    _create_download_log_table(connection)
    _create_info_log_table(connection)
    _create_info_cache_table(connection)


def _create_feed_tables(connection: sqlite3.Connection) -> None:
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


def _create_query_log_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS query_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            keyword TEXT NOT NULL,
            conditions TEXT NOT NULL,
            result_count INTEGER NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_query_log_created_at
        ON query_log(created_at)
        """
    )


def _create_download_log_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS download_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            paper_id TEXT NOT NULL,
            status TEXT NOT NULL,
            saved_path TEXT,
            error TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_download_log_created_at
        ON download_log(created_at)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_download_log_paper_id
        ON download_log(paper_id)
        """
    )


def _create_info_log_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS info_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            paper_id TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_info_log_paper_id
        ON info_log(paper_id)
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_info_log_created_at
        ON info_log(created_at)
        """
    )


def _create_info_cache_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS info_cache (
            paper_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            authors_json TEXT NOT NULL,
            date TEXT NOT NULL,
            abstract TEXT NOT NULL,
            url TEXT,
            published_version TEXT,
            topic TEXT,
            programs TEXT,
            first_cached_at TEXT NOT NULL,
            last_fetched_at TEXT NOT NULL,
            fetch_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_info_cache_last_fetched_at
        ON info_cache(last_fetched_at)
        """
    )


def _upgrade_v1_to_v2(connection: sqlite3.Connection) -> None:
    _create_all_tables(connection)


def _read_user_version(connection: sqlite3.Connection) -> int:
    row = connection.execute("PRAGMA user_version").fetchone()
    return int(row[0]) if row else 0


def _write_config(db_path: Path, schema_version: int) -> None:
    config_store.update_database_config(db_path, schema_version, _default_config_path())


def _configured_db_path() -> Path:
    configured_db_path = config_store.get_configured_db_path(_default_config_path())
    if configured_db_path is not None:
        return configured_db_path

    default = _default_db_path()
    if default.exists():
        return default

    legacy = _legacy_db_path()
    if legacy.exists():
        return legacy
    return default


def _read_config(config_path: Path) -> dict[str, Any]:
    return config_store.read_config(config_path)


def _default_config_path() -> Path:
    return Path.home() / NBER_CLI_DIR_NAME / NBER_CLI_CONFIG_NAME


def _default_db_path() -> Path:
    return Path.home() / NBER_CLI_DIR_NAME / NBER_DB_NAME


def _legacy_db_path() -> Path:
    return Path.home() / NBER_CLI_DIR_NAME / LEGACY_DB_NAME


def _normalize_db_path(db_path: Path | str) -> Path:
    path = Path(db_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve(strict=False)


def _db_move_pairs(old_db_path: Path, new_db_path: Path) -> list[tuple[Path, Path]]:
    pairs = [(old_db_path, new_db_path)]
    for suffix in ("-wal", "-shm", "-journal"):
        source_path = Path(f"{old_db_path}{suffix}")
        if source_path.exists():
            pairs.append((source_path, Path(f"{new_db_path}{suffix}")))
    return pairs


def record_query(
    db_path: Path | str | None,
    keyword: str,
    conditions: dict[str, Any],
    result_count: int,
) -> None:
    try:
        resolved = get_database_path(db_path)
        _ensure_full_schema(resolved)
        with sqlite3.connect(resolved) as connection:
            connection.execute(
                """
                INSERT INTO query_log (created_at, keyword, conditions, result_count)
                VALUES (?, ?, ?, ?)
                """,
                (
                    _utc_now(),
                    keyword,
                    json.dumps(conditions, ensure_ascii=False),
                    result_count,
                ),
            )
    except Exception as error:
        _log_warning("record_query", error)


def record_download(
    db_path: Path | str | None,
    paper_id: str,
    status: str,
    saved_path: str | None = None,
    error: str | None = None,
) -> None:
    try:
        resolved = get_database_path(db_path)
        _ensure_full_schema(resolved)
        with sqlite3.connect(resolved) as connection:
            connection.execute(
                """
                INSERT INTO download_log (
                    created_at, paper_id, status, saved_path, error
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (_utc_now(), paper_id, status, saved_path, error),
            )
    except Exception as exc:
        _log_warning("record_download", exc)


def record_info(
    db_path: Path | str | None,
    paper_id: str | int,
) -> None:
    try:
        resolved = get_database_path(db_path)
        _ensure_full_schema(resolved)
        normalized = _normalize_paper_id(paper_id)
        with sqlite3.connect(resolved) as connection:
            connection.execute(
                """
                INSERT INTO info_log (created_at, paper_id)
                VALUES (?, ?)
                """,
                (_utc_now(), normalized),
            )
    except Exception as exc:
        _log_warning("record_info", exc)


def read_info_cache(
    db_path: Path | str | None,
    paper_id: str | int,
    *,
    cache_enabled: bool | None = None,
    ttl_days: int | None = None,
) -> NBER | None:
    if cache_enabled is None or ttl_days is None:
        settings = config_store.get_info_cache_settings()
        if cache_enabled is None:
            cache_enabled = settings.cache_enabled
        if ttl_days is None:
            ttl_days = settings.cache_ttl_days

    if not cache_enabled:
        return None

    try:
        resolved = get_database_path(db_path)
        if not resolved.exists():
            return None
        normalized = _normalize_paper_id(paper_id)
        with sqlite3.connect(resolved) as connection:
            row = connection.execute(
                """
                SELECT paper_id, title, authors_json, date, abstract,
                       url, published_version, topic, programs, last_fetched_at
                FROM info_cache WHERE paper_id = ?
                """,
                (normalized,),
            ).fetchone()
    except (sqlite3.DatabaseError, OSError):
        return None

    if row is None:
        return None

    if is_info_cache_expired(row[9], ttl_days):
        return None

    authors = json.loads(row[2]) if row[2] else []
    return NBER(
        paper_id=_paper_id_from_str(row[0]),
        title=row[1],
        authors=authors,
        date=row[3],
        abstract=row[4],
        url=row[5],
        published_version=row[6],
        topic=row[7],
        programs=row[8],
    )


def is_info_cache_enabled() -> bool:
    return config_store.get_info_cache_settings().cache_enabled


def get_info_cache_ttl_days() -> int:
    return config_store.get_info_cache_settings().cache_ttl_days


def is_info_cache_expired(
    last_fetched_at: str,
    ttl_days: int | None = None,
    *,
    now: datetime | None = None,
) -> bool:
    effective_ttl_days = config_store.DEFAULT_INFO_CACHE_TTL_DAYS if ttl_days is None else ttl_days
    if effective_ttl_days <= 0:
        return True

    fetched_at = _parse_cached_datetime(last_fetched_at)
    if fetched_at is None:
        return True

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    return fetched_at < current_time - timedelta(days=effective_ttl_days)


def write_info_cache(db_path: Path | str | None, paper: NBER) -> None:
    try:
        resolved = get_database_path(db_path)
        _ensure_full_schema(resolved)
        paper_id_str = _paper_id_to_str(paper.paper_id)
        now = _utc_now()
        with sqlite3.connect(resolved) as connection:
            connection.execute(
                """
                INSERT INTO info_cache (
                    paper_id, title, authors_json, date, abstract,
                    url, published_version, topic, programs,
                    first_cached_at, last_fetched_at, fetch_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(paper_id) DO UPDATE SET
                    title = excluded.title,
                    authors_json = excluded.authors_json,
                    date = excluded.date,
                    abstract = excluded.abstract,
                    url = excluded.url,
                    published_version = excluded.published_version,
                    topic = excluded.topic,
                    programs = excluded.programs,
                    last_fetched_at = excluded.last_fetched_at
                """,
                (
                    paper_id_str,
                    paper.title,
                    json.dumps(paper.authors, ensure_ascii=False),
                    paper.date,
                    paper.abstract,
                    paper.url,
                    paper.published_version,
                    paper.topic,
                    paper.programs,
                    now,
                    now,
                ),
            )
    except Exception as exc:
        _log_warning("write_info_cache", exc)


def touch_info_cache(db_path: Path | str | None, paper_id: str | int) -> None:
    try:
        resolved = get_database_path(db_path)
        if not resolved.exists():
            return
        normalized = _normalize_paper_id(paper_id)
        with sqlite3.connect(resolved) as connection:
            connection.execute(
                """
                UPDATE info_cache
                SET last_fetched_at = ?, fetch_count = fetch_count + 1
                WHERE paper_id = ?
                """,
                (_utc_now(), normalized),
            )
    except Exception as exc:
        _log_warning("touch_info_cache", exc)


def count_info_cache(db_path: Path | str | None = None) -> int:
    try:
        resolved = get_database_path(db_path)
        if not resolved.exists():
            return 0
        with sqlite3.connect(resolved) as connection:
            row = connection.execute("SELECT COUNT(*) FROM info_cache").fetchone()
    except (sqlite3.DatabaseError, OSError):
        return 0
    return int(row[0]) if row else 0


def clear_info_cache(
    *,
    days: int | None = None,
    delete_all: bool = False,
    start_date: str | None = None,
    end_date: str | None = None,
    dry_run: bool = False,
    db_path: Path | str | None = None,
) -> NBERInfoCacheClearResult:
    resolved_db_path = get_database_path(db_path)
    if not resolved_db_path.exists():
        raise ValueError(f"info cache database does not exist: {resolved_db_path}")

    condition, parameters, mode = _build_info_cache_clear_condition(
        days=days,
        delete_all=delete_all,
        start_date=start_date,
        end_date=end_date,
    )
    _ensure_full_schema(resolved_db_path)

    with sqlite3.connect(resolved_db_path) as connection:
        matched_count = connection.execute(
            f"SELECT COUNT(*) FROM info_cache WHERE {condition}",
            parameters,
        ).fetchone()[0]

        deleted_count = 0
        if not dry_run and matched_count:
            cursor = connection.execute(
                f"DELETE FROM info_cache WHERE {condition}",
                parameters,
            )
            deleted_count = cursor.rowcount if cursor.rowcount >= 0 else matched_count

    return NBERInfoCacheClearResult(
        database_path=resolved_db_path,
        matched_count=matched_count,
        deleted_count=deleted_count,
        mode=mode,
        days=(config_store.DEFAULT_INFO_CACHE_TTL_DAYS if days is None else days)
        if mode == "days"
        else None,
        start_date=start_date if mode == "date-range" else None,
        end_date=end_date if mode == "date-range" else None,
        dry_run=dry_run,
    )


def _build_info_cache_clear_condition(
    *,
    days: int | None,
    delete_all: bool,
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, tuple[str, ...], str]:
    has_date_filter = start_date is not None or end_date is not None
    mode_count = sum((days is not None, delete_all, has_date_filter))
    if mode_count > 1:
        raise ValueError("choose only one info cache clear mode")

    if delete_all:
        return "1 = 1", (), "all"

    if has_date_filter:
        return _build_info_cache_date_condition(start_date, end_date)

    clear_days = config_store.DEFAULT_INFO_CACHE_TTL_DAYS if days is None else days
    if clear_days <= 0:
        raise ValueError("days must be a positive integer")
    cutoff_datetime = datetime.fromisoformat(_utc_now()) - timedelta(days=clear_days)
    return "last_fetched_at < ?", (cutoff_datetime.isoformat(timespec="seconds"),), "days"


def _build_info_cache_date_condition(
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, tuple[str, ...], str]:
    if start_date is not None and end_date is None:
        raise ValueError("end-date is required when start-date is provided")
    if end_date is None:
        raise ValueError("end-date is required for date range clear mode")

    parsed_start_date = _parse_cache_date(start_date) if start_date else None
    parsed_end_date = _parse_cache_date(end_date)
    if parsed_start_date and parsed_start_date > parsed_end_date:
        raise ValueError("start-date must be on or before end-date")

    if start_date is None:
        return "substr(last_fetched_at, 1, 10) <= ?", (end_date,), "date-range"

    return (
        "substr(last_fetched_at, 1, 10) >= ? AND substr(last_fetched_at, 1, 10) <= ?",
        (start_date, end_date),
        "date-range",
    )


def _parse_cache_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as error:
        raise ValueError(f"invalid date '{value}', expected YYYY-MM-DD") from error


def _parse_cached_datetime(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _paper_id_to_str(paper_id: int) -> str:
    return f"w{paper_id}"


def _paper_id_from_str(paper_id_str: str) -> int:
    return int(paper_id_str.lstrip("w") or "0")


def _normalize_paper_id(paper_id: str | int) -> str:
    if isinstance(paper_id, int):
        return _paper_id_to_str(paper_id)
    cleaned = paper_id.strip().lower()
    if cleaned.startswith("w"):
        return cleaned
    return f"w{cleaned}"


def _log_warning(operation: str, error: BaseException) -> None:
    print(f"warning: failed to {operation}: {error.__class__.__name__}", file=sys.stderr)
