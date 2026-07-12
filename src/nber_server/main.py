from __future__ import annotations

import argparse
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nber_cli import config_store
from nber_server.errors import (
    ApiError,
    PARAMETER_ERROR_CODE,
    api_error_handler,
)
from nber_server.migrations import upgrade_database
from nber_server.routers import feed, health, papers, settings

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:1420",
    "http://127.0.0.1:1420",
    "tauri://localhost",
]


def create_app(
    *,
    db_path: Path | str | None = None,
    log_dir: Path | str | None = None,
    allowed_origins: list[str] | None = None,
) -> FastAPI:
    resolved_db_path = Path(db_path).expanduser() if db_path else config_store.default_db_path()
    resolved_log_dir = Path(log_dir).expanduser() if log_dir else Path.home() / ".nber-cli" / "logs"

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.db_path = upgrade_database(resolved_db_path)
        app.state.log_dir = resolved_log_dir
        resolved_log_dir.mkdir(parents=True, exist_ok=True)
        yield

    app = FastAPI(title="NBER Desktop API", version="1.0.0", lifespan=lifespan)
    app.state.db_path = resolved_db_path
    app.state.log_dir = resolved_log_dir
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or DEFAULT_ALLOWED_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.include_router(health.router)
    app.include_router(feed.router)
    app.include_router(papers.router)
    app.include_router(settings.router)
    return app


async def _validation_error_handler(_request, error: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": PARAMETER_ERROR_CODE,
            "data": {"errors": error.errors()},
            "message": "request validation failed",
        },
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the NBER desktop HTTP API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=config_store.DEFAULT_DESKTOP_SERVER_PORT)
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--log-dir", type=Path, default=None)
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    app = create_app(db_path=args.db_path, log_dir=args.log_dir)
    uvicorn.run(app, host=args.host, port=args.port)
