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
import sys
from importlib.metadata import version as get_version
from pathlib import Path

from .core.models import DownloadBatchResult
from .download import download_multiple_papers, download_paper, download_paper_to_file
from .fetcher import get_nber
from .formatters import info, related


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


def _handle_download_errors(batch_result: DownloadBatchResult, paper_ids: list[str]) -> None:
    for failure in batch_result.failures:
        error_message = str(failure.error) or failure.error.__class__.__name__
        print(f"Failed to download {failure.paper_id}: {error_message}", file=sys.stderr)
    print(
        f"Downloaded {len(batch_result.paths)} of {len(paper_ids)} papers; "
        f"{len(batch_result.failures)} failed.",
        file=sys.stderr,
    )


def _run_mcp_server(transport: str, port: int) -> None:
    from .mcp import mcp
    mcp.run(transport=transport, port=port)


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
            asyncio.run(download_paper_to_file(paper_ids[0], args.file_path))
            return

        if args.batch_ids is not None:
            batch_result = asyncio.run(download_multiple_papers(paper_ids, args.save_base))
            if batch_result.failures:
                _handle_download_errors(batch_result, paper_ids)
                raise SystemExit(1)
            return

        asyncio.run(download_paper(paper_ids[0], args.save_base))
        return

    if args.command == "info":
        try:
            nber_id = _parse_paper_id(args.paper_id)
        except ValueError:
            parser.error(f"invalid paper ID '{args.paper_id}'")

        paper = asyncio.run(get_nber(nber_id))
        print(info(paper))
        if args.show_all:
            print(related(paper))
            if paper.published_version:
                print({"published_version": paper.published_version})
        return

    if args.command == "mcp-server":
        _run_mcp_server(args.transport, args.port)
        return
