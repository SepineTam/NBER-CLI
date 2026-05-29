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


@dataclass(frozen=True, slots=True)
class NBERCLIConfig:
    request_timeout_seconds: int = 60
    request_retry_count: int = 3
    download_connection_limit: int = 100
    download_connection_limit_per_host: int = 10
    search_page_sizes: tuple[int, ...] = (20, 50, 100)

    @property
    def request_attempts(self) -> int:
        return self.request_retry_count + 1


NBER_CLI_CONFIG = NBERCLIConfig()
