"""Public package API and CLI entrypoint."""

from __future__ import annotations

from .cli import main
from .config import NBER_CLI_CONFIG, NBERCLIConfig
from .core.models import (
    DownloadBatchResult,
    DownloadFailure,
    NBER,
    NBERSearchResults,
)
from .download import download_multiple_papers, download_paper, download_paper_to_file
from .fetcher import get_nber, search_nber
from .formatters import info, related, search_results

__all__ = [
    "NBER",
    "NBERCLIConfig",
    "NBER_CLI_CONFIG",
    "DownloadBatchResult",
    "DownloadFailure",
    "NBERSearchResults",
    "download_multiple_papers",
    "download_paper",
    "download_paper_to_file",
    "get_nber",
    "info",
    "main",
    "related",
    "search_nber",
    "search_results",
]
