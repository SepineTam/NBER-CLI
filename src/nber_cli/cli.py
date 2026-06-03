#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : cli.py

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from importlib.metadata import version as get_version
from pathlib import Path

from aiohttp import ClientError, ClientResponseError

from .core.models import DownloadBatchResult, NBERFeedCleanResult
from .download import download_multiple_papers, download_paper, download_paper_to_file
from .feed import clean_feed_cache, fetch_feed, init_feed_database, migrate_feed_database
from .fetcher import get_nber, search_nber
from .formatters import (
    feed_results,
    feed_results_text,
    info,
    info_text,
    related,
    search_results,
    search_results_text,
)

_OUTPUT_FORMATS = ["list", "json"]


def _get_version() -> str:
    try:
        return get_version("nber-cli")
    except Exception:
        return "0.2.0"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nber-cli",
        description="Download NBER papers from the command line.",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"NBER CLI v{_get_version()}"
    )

    subparsers = parser.add_subparsers(dest="command")

    download_parser = subparsers.add_parser("download", help="Download one or more NBER papers.")
    download_parser.add_argument("paper_id", nargs="?", help="Single paper ID, e.g. w1234.")
    download_parser.add_argument(
        "--file", "-f", dest="file_path", type=Path, help="Explicit target file path."
    )
    download_parser.add_argument(
        "--save-base",
        "-s",
        dest="save_base",
        type=Path,
        default=Path.cwd(),
        help="Target directory to save PDF files. Defaults to current working directory.",
    )
    download_parser.add_argument("--batch", "-b", nargs="+", dest="batch_ids", help="Batch paper IDs.")

    info_parser = subparsers.add_parser("info", help="Show information about an NBER paper.")
    info_parser.add_argument("paper_id", help="Paper ID, e.g. w1234.")
    info_parser.add_argument(
        "--all", "-a", action="store_true", dest="show_all", help="Show all fields including related."
    )
    info_parser.add_argument(
        "--format",
        "-f",
        choices=_OUTPUT_FORMATS,
        default="list",
        dest="output_format",
        help="Output format (default: list).",
    )

    search_parser = subparsers.add_parser("search", help="Search NBER working papers.")
    search_parser.add_argument("query", help="Title, number, author, abstract, or keyword.")
    search_parser.add_argument(
        "--start-date",
        "--start",
        dest="start_date",
        help="Only include papers on or after this date (YYYY-MM-DD).",
    )
    search_parser.add_argument(
        "--end-date",
        "--end",
        dest="end_date",
        help="Only include papers on or before this date (YYYY-MM-DD).",
    )
    search_parser.add_argument("--page", type=int, default=1, help="Result page to fetch.")
    search_parser.add_argument(
        "--per-page",
        type=int,
        default=20,
        choices=[20, 50, 100],
        dest="per_page",
        help="Number of results per page.",
    )
    search_parser.add_argument(
        "--format",
        "-f",
        choices=_OUTPUT_FORMATS,
        default="list",
        dest="output_format",
        help="Output format (default: list).",
    )

    feed_parser = subparsers.add_parser("feed", help="Manage the NBER working papers RSS feed.")
    feed_subparsers = feed_parser.add_subparsers(dest="feed_command", required=True)

    feed_init_parser = feed_subparsers.add_parser("init", help="Initialize the feed database.")
    feed_init_parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="SQLite database path. Defaults to ~/.nber-cli/feed.db.",
    )

    feed_migrate_parser = feed_subparsers.add_parser(
        "migrate",
        help="Move the feed database to a new path and update config.",
    )
    feed_migrate_parser.add_argument("new_db_path", type=Path, help="New SQLite database path.")

    feed_clean_parser = feed_subparsers.add_parser(
        "clean",
        help="Clean cached feed database records.",
    )
    feed_clean_parser.add_argument(
        "--days",
        type=_parse_positive_int,
        default=None,
        help="Clean cached records not seen for this many days (default: 30).",
    )
    feed_clean_parser.add_argument(
        "--all",
        action="store_true",
        dest="delete_all",
        help="Clean all cached feed database records.",
    )
    feed_clean_parser.add_argument(
        "--start-date",
        dest="start_date",
        help="Clean cached records last seen on or after this date (YYYY-MM-DD).",
    )
    feed_clean_parser.add_argument(
        "--end-date",
        dest="end_date",
        help="Clean cached records last seen on or before this date (YYYY-MM-DD).",
    )

    feed_fetch_parser = feed_subparsers.add_parser(
        "fetch",
        help="Fetch the NBER RSS feed.",
        allow_abbrev=False,
    )
    feed_fetch_parser.add_argument(
        "--display-all",
        nargs="?",
        const="true",
        default=None,
        type=_parse_bool,
        help=(
            "Display all fetched items instead of only new items "
            "(true/false; defaults to true when --max-items is set, otherwise false)."
        ),
    )
    feed_fetch_parser.add_argument(
        "--format",
        "-f",
        choices=_OUTPUT_FORMATS,
        default="list",
        dest="output_format",
        help="Output format (default: list).",
    )
    feed_fetch_parser.add_argument(
        "--max-items",
        type=_parse_non_negative_int,
        default=None,
        dest="max_items",
        help="Maximum number of feed items to display.",
    )

    mcp_parser = subparsers.add_parser("mcp-server", help="Start the MCP server.")
    mcp_parser.add_argument(
        "--transport",
        choices=["stdio", "streamable_http"],
        default="stdio",
        help="Transport mechanism (default: stdio).",
    )
    mcp_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for streamable_http transport (default: 8000).",
    )

    return parser


def _resolve_paper_ids(single_id: str | None, batch_ids: list[str] | None) -> list[str]:
    if batch_ids:
        return batch_ids
    if single_id:
        return [single_id]
    return []


def _parse_paper_id(paper_id_str: str) -> int:
    cleaned = paper_id_str.lower().removeprefix("w")
    return int(cleaned)


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def _parse_non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected a non-negative integer") from error
    if parsed < 0:
        raise argparse.ArgumentTypeError("expected a non-negative integer")
    return parsed


def _parse_positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected a positive integer") from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def _print_download_success(paper_id: str, output_file: Path) -> None:
    print(f"Successfully downloaded {paper_id} to {output_file}")


def _format_download_error(paper_id: str, error: BaseException) -> str:
    if isinstance(error, ClientResponseError):
        if error.status == 403:
            return (
                f"Failed to download {paper_id}: no permission to access this paper "
                "(HTTP 403). It may still be in NBER's first-week access restriction."
            )
        if error.status == 404:
            return f"Failed to download {paper_id}: paper not found (HTTP 404)."

        error_message = error.message or "HTTP error"
        return f"Failed to download {paper_id}: HTTP {error.status} {error_message}."

    if isinstance(error, TimeoutError):
        return f"Failed to download {paper_id}: request timed out."

    if isinstance(error, (ClientError, ConnectionError)):
        error_message = str(error) or error.__class__.__name__
        return f"Failed to download {paper_id}: network error: {error_message}."

    if isinstance(error, asyncio.CancelledError):
        return f"Failed to download {paper_id}: download cancelled."

    error_message = str(error) or error.__class__.__name__
    return f"Failed to download {paper_id}: {error_message}"


def _run_single_download(paper_id: str, output_file: Path | None, save_base: Path) -> None:
    try:
        if output_file is not None:
            downloaded_file = asyncio.run(download_paper_to_file(paper_id, output_file))
        else:
            downloaded_file = asyncio.run(download_paper(paper_id, save_base))
    except (Exception, asyncio.CancelledError) as error:
        print(_format_download_error(paper_id, error), file=sys.stderr)
        raise SystemExit(1) from None

    _print_download_success(paper_id, downloaded_file)


def _handle_download_errors(batch_result: DownloadBatchResult, paper_ids: list[str]) -> None:
    for output_file in batch_result.paths:
        _print_download_success(output_file.stem, output_file)

    for failure in batch_result.failures:
        print(_format_download_error(failure.paper_id, failure.error), file=sys.stderr)

    if batch_result.failures:
        print(
            f"Downloaded {len(batch_result.paths)} of {len(paper_ids)} papers; "
            f"{len(batch_result.failures)} failed.",
            file=sys.stderr,
        )


def _run_mcp_server(transport: str, port: int) -> None:
    from .mcp import nber_mcp
    nber_mcp.run(transport=transport, port=port)


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _info_payload(paper, include_all: bool) -> dict:
    result = info(paper)
    if include_all:
        result.update(related(paper))
        if paper.published_version:
            result["published_version"] = paper.published_version
    return result


def _feed_clean_options(args: argparse.Namespace) -> dict[str, object]:
    return {
        "days": args.days,
        "delete_all": args.delete_all,
        "start_date": args.start_date,
        "end_date": args.end_date,
    }


def _print_feed_clean_preview(result: NBERFeedCleanResult) -> None:
    print(f"Database: {result.database_path}")
    print(f"Matched cached records: {result.matched_count}")
    print("")
    if result.matched_count == 0:
        print("No cached records matched.")
        return

    print("This operation is irreversible.")
    print("Deleted cache records may be fetched again as new items if they still appear in the RSS feed.")


def _confirm_feed_clean() -> bool:
    print("Continue? [y/N]: ", end="")
    return input().strip() in {"y", "Y"}


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        raise SystemExit(0)

    if args.command == "download":
        if args.paper_id and args.batch_ids:
            parser.error("cannot mix positional paper ID with --batch")

        if args.batch_ids and args.file_path is not None:
            parser.error("--file/-f is not supported with --batch")

        paper_ids = _resolve_paper_ids(args.paper_id, args.batch_ids)
        if not paper_ids:
            parser.error("download requires one paper ID or --batch with one or more IDs.")

        if len(paper_ids) > 1 and args.file_path is not None:
            parser.error("--file/-f is only supported for single downloads, not for --batch or multiple IDs.")

        if args.file_path is not None:
            _run_single_download(paper_ids[0], args.file_path, args.save_base)
            return

        if args.batch_ids is not None:
            batch_result = asyncio.run(download_multiple_papers(paper_ids, args.save_base))
            _handle_download_errors(batch_result, paper_ids)
            if batch_result.failures:
                raise SystemExit(1)
            return

        _run_single_download(paper_ids[0], None, args.save_base)
        return

    if args.command == "info":
        try:
            nber_id = _parse_paper_id(args.paper_id)
        except ValueError:
            parser.error(f"invalid paper ID '{args.paper_id}'")

        paper = asyncio.run(get_nber(nber_id))
        if args.output_format == "json":
            _print_json(_info_payload(paper, args.show_all))
        else:
            print(info_text(paper, include_all=args.show_all))
        return

    if args.command == "search":
        try:
            results = asyncio.run(
                search_nber(
                    args.query,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    page=args.page,
                    per_page=args.per_page,
                )
            )
        except ValueError as error:
            parser.error(str(error))
        if args.output_format == "json":
            _print_json(search_results(results))
        else:
            print(search_results_text(results))
        return

    if args.command == "feed":
        if args.feed_command == "init":
            try:
                db_path = init_feed_database(args.db_path)
            except ValueError as error:
                parser.error(str(error))
            print(f"Feed database initialized at {db_path}")
            return

        if args.feed_command == "migrate":
            try:
                old_db_path, new_db_path = migrate_feed_database(args.new_db_path)
            except ValueError as error:
                parser.error(str(error))
            print(f"Feed database migrated from {old_db_path} to {new_db_path}")
            return

        if args.feed_command == "clean":
            clean_options = _feed_clean_options(args)
            try:
                preview = clean_feed_cache(**clean_options, dry_run=True)
            except ValueError as error:
                parser.error(str(error))

            _print_feed_clean_preview(preview)
            if preview.matched_count == 0:
                return
            if not _confirm_feed_clean():
                print("Aborted.")
                return

            try:
                result = clean_feed_cache(**clean_options)
            except ValueError as error:
                parser.error(str(error))
            print(f"Deleted cached records: {result.deleted_count}")
            return

        if args.feed_command == "fetch":
            try:
                display_all = (
                    args.display_all
                    if args.display_all is not None
                    else args.max_items is not None
                )
                result = fetch_feed(display_all=display_all, max_items=args.max_items)
            except ValueError as error:
                parser.error(str(error))
            if args.output_format == "json":
                _print_json(feed_results(result))
            else:
                print(feed_results_text(result))
            return

    if args.command == "mcp-server":
        _run_mcp_server(args.transport, args.port)
        return
