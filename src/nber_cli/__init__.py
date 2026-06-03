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
from .db import (
    get_database_path,
    get_schema_version,
    init_database,
    migrate_database,
    read_info_cache,
    record_download,
    record_info,
    record_query,
    touch_info_cache,
    write_info_cache,
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
    "DownloadBatchResult",
    "DownloadFailure",
    "NBER",
    "NBERCLIConfig",
    "NBER_CLI_CONFIG",
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
    "get_database_path",
    "get_nber",
    "get_schema_version",
    "init_database",
    "init_feed_database",
    "info",
    "main",
    "migrate_database",
    "migrate_feed_database",
    "parse_feed_xml",
    "read_info_cache",
    "record_download",
    "record_info",
    "record_query",
    "related",
    "search_nber",
    "search_results",
    "touch_info_cache",
    "write_info_cache",
]
