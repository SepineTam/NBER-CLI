"""Public package API and CLI entrypoint."""

from __future__ import annotations

from .cli import main
from .core.models import DownloadBatchResult, DownloadFailure, NBER
from .download import download_multiple_papers, download_paper, download_paper_to_file
from .fetcher import get_nber
from .formatters import info, related

__all__ = [
    "NBER",
    "DownloadBatchResult",
    "DownloadFailure",
    "download_multiple_papers",
    "download_paper",
    "download_paper_to_file",
    "get_nber",
    "info",
    "main",
    "related",
]
