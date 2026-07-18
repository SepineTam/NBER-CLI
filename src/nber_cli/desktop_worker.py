from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import db
from .config import config_store
from .db.info_cache import get_paper_with_info_cache_result
from .fetch.feed import fetch_feed

logger = logging.getLogger(__name__)

_PREFETCH_CONCURRENCY = 4
_PREFETCH_BUDGET_SECONDS = 60.0


@dataclass(frozen=True, slots=True)
class FeedInfoPrefetchResult:
    fetched_count: int
    cached_count: int
    failed_count: int


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="One-shot NBER-CLI Desktop worker")
    parser.add_argument("--db-path", required=True, type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init")
    subparsers.add_parser("feed-fetch")
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            initialized = db.init_database(args.db_path)
            payload: dict[str, Any] = {
                "database_path": str(initialized),
                "schema_version": db.SCHEMA_VERSION,
            }
        elif args.command == "feed-fetch":
            result = fetch_feed(display_all=True, db_path=args.db_path)
            prefetch = asyncio.run(
                prefetch_feed_info(
                    [item.paper_id for item in result.items],
                    db_path=args.db_path,
                )
            )
            payload = {
                "fetched_count": result.total_fetched,
                "new_count": result.new_count,
                "info_fetched_count": prefetch.fetched_count,
                "info_cached_count": prefetch.cached_count,
                "info_failed_count": prefetch.failed_count,
            }
    except Exception as error:
        print(
            json.dumps(
                {
                    "error": error.__class__.__name__,
                    "message": str(error),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise SystemExit(1) from None

    print(json.dumps(payload, ensure_ascii=False))


async def prefetch_feed_info(
    paper_ids: list[str],
    *,
    db_path: Path,
    concurrency: int = _PREFETCH_CONCURRENCY,
    budget_seconds: float = _PREFETCH_BUDGET_SECONDS,
) -> FeedInfoPrefetchResult:
    if concurrency <= 0:
        raise ValueError("concurrency must be positive")
    if budget_seconds <= 0:
        raise ValueError("budget_seconds must be positive")

    unique_paper_ids = list(dict.fromkeys(paper_ids))
    if not unique_paper_ids:
        return FeedInfoPrefetchResult(0, 0, 0)
    if not config_store.get_info_cache_settings().cache_enabled:
        return FeedInfoPrefetchResult(0, 0, 0)

    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        asyncio.create_task(
            _prefetch_one_paper(
                _paper_number(paper_id),
                db_path=db_path,
                semaphore=semaphore,
            )
        )
        for paper_id in unique_paper_ids
    ]
    done, pending = await asyncio.wait(tasks, timeout=budget_seconds)
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    statuses = [task.result() for task in done]
    return FeedInfoPrefetchResult(
        fetched_count=statuses.count("fetched"),
        cached_count=statuses.count("cached"),
        failed_count=statuses.count("failed") + len(pending),
    )


async def _prefetch_one_paper(
    paper_id: int,
    *,
    db_path: Path,
    semaphore: asyncio.Semaphore,
) -> str:
    async with semaphore:
        try:
            result = await get_paper_with_info_cache_result(
                paper_id,
                db_path=db_path,
            )
            paper = getattr(result, "paper", None)
            if result.from_cache and paper is not None and not (
                getattr(paper, "topic", None) or getattr(paper, "programs", None)
            ):
                result = await get_paper_with_info_cache_result(
                    paper_id,
                    refresh=True,
                    db_path=db_path,
                )
        except Exception as error:
            logger.warning(
                "Desktop Feed metadata prefetch failed for w%s: %s",
                paper_id,
                error.__class__.__name__,
            )
            return "failed"
    return "cached" if result.from_cache else "fetched"


def _paper_number(value: str) -> int:
    cleaned = value.strip().lower().removeprefix("w")
    if not cleaned.isdigit() or int(cleaned) <= 0:
        raise argparse.ArgumentTypeError("paper_id must look like w12345")
    return int(cleaned)


if __name__ == "__main__":
    main()
