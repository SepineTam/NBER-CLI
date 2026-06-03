"""Public package API and CLI entrypoint."""

from __future__ import annotations

from .cli import main
from .config import NBER_CLI_CONFIG, NBERCLIConfig
from .core.models import (
    DownloadBatchResult,
    DownloadFailure,
    NBER,
    NBERFeedCleanResult,
    NBERFeedFetchResult,
    NBERFeedItem,
    NBERSearchResults,
)
from .download import download_multiple_papers, download_paper, download_paper_to_file
from .feed import (
    clean_feed_cache,
    fetch_feed,
    init_feed_database,
    migrate_feed_database,
    parse_feed_xml,
)
from .fetcher import get_nber, search_nber
from .formatters import feed_results, info, related, search_results

__all__ = [
    "NBER",
    "NBERCLIConfig",
    "NBER_CLI_CONFIG",
    "DownloadBatchResult",
    "DownloadFailure",
    "NBERFeedCleanResult",
    "NBERFeedFetchResult",
    "NBERFeedItem",
    "NBERSearchResults",
    "clean_feed_cache",
    "download_multiple_papers",
    "download_paper",
    "download_paper_to_file",
    "feed_results",
    "fetch_feed",
    "get_nber",
    "init_feed_database",
    "info",
    "main",
    "migrate_feed_database",
    "parse_feed_xml",
    "related",
    "search_nber",
    "search_results",
]
