from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError, URLError

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from nber_cli import db
from nber_cli.info_cache import get_paper_with_info_cache_result
from nber_cli.server.errors import (
    ApiError,
    EXTERNAL_SERVICE_ERROR_CODE,
    PARAMETER_ERROR_CODE,
    api_success,
)
from nber_cli.server.schemas import PaperResponse, ReadStatusResponse, ReadStatusUpdate

router = APIRouter(prefix="/api/v1/papers", tags=["papers"])


@router.get("/{paper_id}")
async def get_paper(paper_id: str, request: Request):
    db_path = Path(request.app.state.db_path)
    normalized = _normalize_paper_id(paper_id)
    feed_url = await run_in_threadpool(_paper_url_from_feed, db_path, normalized)
    if feed_url is None:
        raise ApiError(
            status_code=404,
            code=PARAMETER_ERROR_CODE,
            message=f"paper not found: {normalized}",
        )

    numeric_id = _paper_number(normalized)
    try:
        result = await get_paper_with_info_cache_result(numeric_id)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
        raise ApiError(
            status_code=503,
            code=EXTERNAL_SERVICE_ERROR_CODE,
            message=f"failed to fetch paper details: {error}",
        ) from error

    await run_in_threadpool(db.set_paper_read_status, db_path, normalized, True)
    paper = result.paper
    data = PaperResponse(
        paper_id=normalized,
        title=paper.title,
        authors=paper.authors,
        date=paper.date,
        abstract=paper.abstract,
        url=paper.url or feed_url,
        pdf_url=_paper_pdf_url(normalized),
        published_version=paper.published_version,
        topic=paper.topic,
        programs=paper.programs,
        is_read=True,
        from_cache=result.from_cache,
    )
    return api_success(data.model_dump())


@router.post("/{paper_id}/mark-read")
async def mark_paper_read(
    paper_id: str,
    request: Request,
    payload: ReadStatusUpdate | None = None,
):
    db_path = Path(request.app.state.db_path)
    normalized = _normalize_paper_id(paper_id)
    is_read = True if payload is None else payload.is_read
    await run_in_threadpool(db.set_paper_read_status, db_path, normalized, is_read)
    data = ReadStatusResponse(paper_id=normalized, is_read=is_read)
    return api_success(data.model_dump())


def _paper_url_from_feed(db_path: Path, paper_id: str) -> str | None:
    db.init_database(db_path)
    with db._open_session(db_path) as session:
        row = db._execute(
            session.connection(),
            "SELECT url FROM feed_items WHERE paper_id = ?",
            (paper_id,),
        ).fetchone()
    return str(row[0]) if row else None


def _normalize_paper_id(paper_id: str) -> str:
    cleaned = paper_id.strip().lower()
    if cleaned.startswith("w"):
        cleaned = cleaned[1:]
    if not cleaned.isdigit() or int(cleaned) <= 0:
        raise ApiError(
            status_code=400,
            code=PARAMETER_ERROR_CODE,
            message="paper_id must look like w12345",
        )
    return f"w{cleaned}"


def _paper_number(paper_id: str) -> int:
    return int(paper_id[1:])


def _paper_pdf_url(paper_id: str) -> str:
    return f"https://www.nber.org/system/files/working_papers/{paper_id}/{paper_id}.pdf"
