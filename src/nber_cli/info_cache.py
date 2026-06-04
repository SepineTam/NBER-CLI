#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : info_cache.py

from __future__ import annotations

from . import config_store, db
from .core.models import NBER
from .fetcher import get_nber


async def get_paper_with_info_cache(paper_id: int, *, refresh: bool = False) -> NBER:
    settings = config_store.get_info_cache_settings()

    if settings.cache_enabled and not refresh:
        cached_paper = db.read_info_cache(
            None,
            paper_id,
            cache_enabled=True,
            ttl_days=settings.cache_ttl_days,
        )
        if cached_paper is not None:
            db.touch_info_cache(None, paper_id)
            return cached_paper

    paper = await get_nber(paper_id)
    if settings.cache_enabled:
        db.write_info_cache(None, paper)
    return paper
