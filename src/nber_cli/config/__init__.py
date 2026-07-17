#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : config/__init__.py

"""Configuration subpackage."""

from __future__ import annotations

from .config import NBER_CLI_CONFIG, NBERCLIConfig
from .config_store import (
    InfoCacheSettings,
    get_config_value,
    get_info_cache_settings,
    read_config,
    set_config_value,
    set_info_cache_enabled,
    set_info_cache_ttl_days,
    validate_config,
    write_config,
)

__all__ = [
    "InfoCacheSettings",
    "NBERCLIConfig",
    "NBER_CLI_CONFIG",
    "get_config_value",
    "get_info_cache_settings",
    "read_config",
    "set_config_value",
    "set_info_cache_enabled",
    "set_info_cache_ttl_days",
    "validate_config",
    "write_config",
]
