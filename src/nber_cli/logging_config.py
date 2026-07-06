#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : logging_config.py

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path

_LOG_FORMAT = "%(asctime)s %(funcName)s %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_LOG_FILE_NAME = "debug.log"
_LOG_MAX_BYTES = 1_000_000
_LOG_BACKUP_COUNT = 3
_LOGGER_NAME = "nber_cli"


def _default_log_dir() -> Path:
    log_dir = Path.home() / ".nber-cli"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def configure_logging(*, verbose: bool = False) -> logging.Logger:
    debug_env = os.environ.get("NBER_CLI_DEBUG", "")
    level = logging.DEBUG if verbose or debug_env == "1" else logging.WARNING

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    log_dir = _default_log_dir()
    log_file = log_dir / _LOG_FILE_NAME
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=_LOG_MAX_BYTES,
        backupCount=_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if verbose:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger
