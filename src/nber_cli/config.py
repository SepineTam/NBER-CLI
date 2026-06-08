#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : config.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import config_store


@dataclass(frozen=True, slots=True)
class NBERCLIConfig:
    request_timeout_seconds: int = 60
    request_retry_count: int = 3
    download_connection_limit: int = 100
    download_connection_limit_per_host: int = 10
    search_page_sizes: tuple[int, ...] = (20, 50, 100)
    restrict_dir: bool = True
    download_concurrency: int = 3

    @property
    def request_attempts(self) -> int:
        return self.request_retry_count + 1

    @classmethod
    def from_config_file(cls) -> NBERCLIConfig:
        config = config_store.read_config()
        kwargs: dict[str, Any] = {}
        restrict_dir = config_store.get_config_value(config, "download.restrict_dir")
        if isinstance(restrict_dir, bool):
            kwargs["restrict_dir"] = restrict_dir
        concurrency = config_store.get_config_value(config, "download.concurrency")
        if isinstance(concurrency, int) and not isinstance(concurrency, bool):
            kwargs["download_concurrency"] = concurrency
        return cls(**kwargs)


NBER_CLI_CONFIG = NBERCLIConfig.from_config_file()
