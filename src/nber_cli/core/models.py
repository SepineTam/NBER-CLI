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
from typing import List


@dataclass
class NBER:
    paper_id: int
    title: str
    authors: List[str]
    date: str
    abstract: str

    published_version: str | None = None
    topic: str | None = None
    programs: str | None = None


@dataclass
class DownloadFailure:
    paper_id: str
    error: BaseException


@dataclass
class DownloadBatchResult:
    paths: list[Path]
    failures: list[DownloadFailure]
