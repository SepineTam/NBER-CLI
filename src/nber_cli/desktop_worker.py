from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from . import db
from .db.info_cache import get_paper_with_info_cache_result
from .fetch.feed import fetch_feed


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="One-shot NBER-CLI Desktop worker")
    parser.add_argument("--db-path", required=True, type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init")
    subparsers.add_parser("feed-fetch")
    paper_parser = subparsers.add_parser("paper-info")
    paper_parser.add_argument("paper_id", type=_paper_number)
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            initialized = db.init_database(args.db_path)
            payload: dict[str, Any] = {
                "database_path": str(initialized),
                "schema_version": db.SCHEMA_VERSION,
            }
        elif args.command == "feed-fetch":
            result = fetch_feed(db_path=args.db_path)
            payload = {
                "fetched_count": result.total_fetched,
                "new_count": result.new_count,
            }
        else:
            result = asyncio.run(
                get_paper_with_info_cache_result(
                    args.paper_id,
                    db_path=args.db_path,
                )
            )
            db.record_info(args.db_path, args.paper_id)
            paper = result.paper
            payload = {
                "paper_id": f"w{paper.paper_id}",
                "title": paper.title,
                "authors": paper.authors,
                "date": paper.date,
                "abstract": paper.abstract,
                "url": paper.url or f"https://www.nber.org/papers/w{paper.paper_id}",
                "published_version": paper.published_version,
                "topic": paper.topic,
                "programs": paper.programs,
                "from_cache": result.from_cache,
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


def _paper_number(value: str) -> int:
    cleaned = value.strip().lower().removeprefix("w")
    if not cleaned.isdigit() or int(cleaned) <= 0:
        raise argparse.ArgumentTypeError("paper_id must look like w12345")
    return int(cleaned)


if __name__ == "__main__":
    main()
