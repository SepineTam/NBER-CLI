"""Public package API and CLI entrypoint."""

from __future__ import annotations

import argparse
import asyncio
from importlib.metadata import version as get_version
from pathlib import Path

from .core.download.downloader import download_multiple_papers, download_paper, download_paper_to_file


def get_version_info() -> str:
    """Return the package version string."""
    try:
        return get_version("nber-cli")
    except Exception:
        return "0.2.0"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nber-cli",
        description="Download NBER papers from the command line.",
    )
    parser.add_argument("-v", "--version", action="version", version=f"NBER CLI v{get_version_info()}")

    subparsers = parser.add_subparsers(dest="command")
    download_parser = subparsers.add_parser("download", help="Download one or more NBER papers.")
    download_parser.add_argument("paper_id", nargs="?", help="Single paper ID, e.g. w1234.")
    download_parser.add_argument("--file", "-f", dest="file_path", type=Path, help="Explicit target file path.")
    download_parser.add_argument(
        "--save-base",
        "-s",
        dest="save_base",
        type=Path,
        default=Path.cwd(),
        help="Target directory to save PDF files. Defaults to current working directory.",
    )
    download_parser.add_argument("--batch", "-b", nargs="+", dest="batch_ids", help="Batch paper IDs.")
    return parser


def _resolve_paper_ids(single_id: str | None, batch_ids: list[str] | None) -> list[str]:
    if batch_ids:
        return batch_ids
    if single_id:
        return [single_id]
    return []


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command != "download":
        parser.print_help()
        raise SystemExit(0)

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

    if len(paper_ids) == 1:
        asyncio.run(download_paper(paper_ids[0], args.save_base))
    else:
        asyncio.run(download_multiple_papers(paper_ids, args.save_base))
