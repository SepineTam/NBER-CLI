"""Public package API and CLI entrypoint."""

from __future__ import annotations

from .cli import main
from .config import NBER_CLI_CONFIG, NBERCLIConfig
from .config_store import (
    InfoCacheSettings,
    get_info_cache_settings,
    set_info_cache_enabled,
    set_info_cache_ttl_days,
)
from .core.models import (
    DownloadBatchResult,
    DownloadFailure,
    NBER,
    NBERFeedCleanResult,
    NBERFeedFetchResult,
    NBERFeedItem,
    NBERInfoCacheClearResult,
    NBERSearchResults,
)
from .db import (
    clear_info_cache,
    count_info_cache,
    get_database_path,
    get_info_cache_ttl_days,
    get_schema_version,
    init_database,
    is_info_cache_enabled,
    is_info_cache_expired,
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
    "InfoCacheSettings",
    "NBER",
    "NBERCLIConfig",
    "NBER_CLI_CONFIG",
    "NBERFeedCleanResult",
    "NBERFeedFetchResult",
    "NBERFeedItem",
    "NBERInfoCacheClearResult",
    "NBERSearchResults",
    "clear_info_cache",
    "clean_feed_cache",
    "count_info_cache",
    "download_multiple_papers",
    "download_paper",
    "download_paper_to_file",
    "feed_results",
    "fetch_feed",
    "get_database_path",
    "get_info_cache_settings",
    "get_info_cache_ttl_days",
    "get_nber",
    "get_schema_version",
    "init_database",
    "init_feed_database",
    "info",
    "is_info_cache_enabled",
    "is_info_cache_expired",
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
    "set_info_cache_enabled",
    "set_info_cache_ttl_days",
    "touch_info_cache",
    "write_info_cache",
]
