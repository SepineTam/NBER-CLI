#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : fetch/__init__.py

"""Network fetching and download subpackage."""

from __future__ import annotations

from .download import download_multiple_papers, download_paper, download_paper_to_file
from .feed import (
    clean_feed_cache,
    fetch_feed,
    init_feed_database,
    migrate_feed_database,
    parse_feed_xml,
)
from .fetcher import get_nber, search_nber

__all__ = [
    "clean_feed_cache",
    "download_multiple_papers",
    "download_paper",
    "download_paper_to_file",
    "fetch_feed",
    "get_nber",
    "init_feed_database",
    "migrate_feed_database",
    "parse_feed_xml",
    "search_nber",
]
