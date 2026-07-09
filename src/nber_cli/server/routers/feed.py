from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

from fastapi import APIRouter, Query, Request
from starlette.concurrency import run_in_threadpool

from nber_cli import db
from nber_cli.feed import fetch_feed
from nber_cli.server.errors import (
    ApiError,
    EXTERNAL_SERVICE_ERROR_CODE,
    api_success,
)
from nber_cli.server.schemas import FeedItemResponse, FeedListResponse, FeedRefreshResponse

router = APIRouter(prefix="/api/v1/feed", tags=["feed"])


@router.get("")
async def list_feed(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = False,
):
    data = await run_in_threadpool(
        _list_feed_items,
        Path(request.app.state.db_path),
        limit,
        offset,
        unread_only,
    )
    return api_success(data.model_dump())


@router.post("/refresh")
async def refresh_feed(request: Request):
    db_path = Path(request.app.state.db_path)
    try:
        result = await run_in_threadpool(fetch_feed, True, db_path, None)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
        raise ApiError(
            status_code=503,
            code=EXTERNAL_SERVICE_ERROR_CODE,
            message=f"failed to refresh NBER feed: {error}",
        ) from error

    total_count = await run_in_threadpool(_count_feed_items, db_path)
    data = FeedRefreshResponse(
        new_count=result.new_count,
        total_count=total_count,
        fetched_count=result.total_fetched,
        last_successful_fetch_at=_last_successful_fetch_at(db_path),
    )
    return api_success(data.model_dump())


def _list_feed_items(
    db_path: Path,
    limit: int,
    offset: int,
    unread_only: bool,
) -> FeedListResponse:
    db.init_database(db_path)
    where_clause = "WHERE COALESCE(read_status.is_read, 0) = 0" if unread_only else ""
    with db._open_session(db_path) as session:
        connection = session.connection()
        rows = db._execute(
            connection,
            f"""
            SELECT
                feed_items.paper_id,
                feed_items.title,
                feed_items.authors_json,
                feed_items.abstract,
                feed_items.url,
                feed_items.source_url,
                feed_items.guid,
                feed_items.first_seen_at,
                feed_items.last_seen_at,
                COALESCE(read_status.is_read, 0) AS is_read
            FROM feed_items
            LEFT JOIN read_status ON read_status.paper_id = feed_items.paper_id
            {where_clause}
            ORDER BY feed_items.last_seen_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        total_count = db._execute(
            connection,
            f"""
            SELECT COUNT(*)
            FROM feed_items
            LEFT JOIN read_status ON read_status.paper_id = feed_items.paper_id
            {where_clause}
            """,
        ).fetchone()[0]

    items = [
        FeedItemResponse(
            paper_id=row[0],
            title=row[1],
            authors=_decode_authors(row[2]),
            abstract=row[3],
            url=row[4],
            source_url=row[5],
            guid=row[6],
            first_seen_at=row[7],
            last_seen_at=row[8],
            is_read=bool(row[9]),
        )
        for row in rows
    ]
    return FeedListResponse(
        items=items,
        total_count=int(total_count),
        limit=limit,
        offset=offset,
        last_successful_fetch_at=_last_successful_fetch_at(db_path),
    )


def _count_feed_items(db_path: Path) -> int:
    db.init_database(db_path)
    with db._open_session(db_path) as session:
        row = db._execute(session.connection(), "SELECT COUNT(*) FROM feed_items").fetchone()
    return int(row[0]) if row else 0


def _last_successful_fetch_at(db_path: Path) -> str | None:
    if not db_path.exists():
        return None
    with db._open_session(db_path) as session:
        row = db._execute(
            session.connection(),
            "SELECT fetched_at FROM feed_fetches ORDER BY fetched_at DESC LIMIT 1",
        ).fetchone()
    return str(row[0]) if row else None


def _decode_authors(value: str) -> list[str]:
    try:
        loaded: Any = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(author) for author in loaded] if isinstance(loaded, list) else []
