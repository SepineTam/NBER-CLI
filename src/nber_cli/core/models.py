#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : models.py

from dataclasses import dataclass
from pathlib import Path


@dataclass
class NBER:
    paper_id: int
    title: str
    authors: list[str]
    date: str
    abstract: str

    url: str | None = None
    published_version: str | None = None
    topic: str | None = None
    programs: str | None = None


@dataclass
class NBERSearchResults:
    query: str
    total_results: int
    results: list[NBER]
    page: int
    per_page: int
    start_date: str | None = None
    end_date: str | None = None


@dataclass
class NBERFeedItem:
    paper_id: str
    title: str
    authors: list[str]
    abstract: str
    url: str
    source_url: str
    guid: str


@dataclass
class NBERFeedFetchResult:
    source_url: str
    database_path: Path
    total_fetched: int
    new_count: int
    display_all: bool
    items: list[NBERFeedItem]
    max_items: int | None = None


@dataclass
class NBERFeedCleanResult:
    database_path: Path
    matched_count: int
    deleted_count: int
    mode: str
    days: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    dry_run: bool = False


@dataclass
class NBERInfoCacheClearResult:
    database_path: Path
    matched_count: int
    deleted_count: int
    mode: str
    days: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    dry_run: bool = False


@dataclass
class DownloadFailure:
    paper_id: str
    error: BaseException


@dataclass
class DownloadBatchResult:
    paths: list[Path]
    failures: list[DownloadFailure]
