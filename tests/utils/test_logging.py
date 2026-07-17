#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : utils/test_logging.py

import logging
import os
from unittest.mock import patch


class TestConfigureLogging:
    def test_default_level_is_warning(self, tmp_path):
        from nber_cli.utils.logging_config import configure_logging

        with patch("nber_cli.utils.logging_config._default_log_dir", return_value=tmp_path):
            logger = configure_logging(verbose=False)

        assert logger.level == logging.WARNING

    def test_verbose_sets_debug_level(self, tmp_path):
        from nber_cli.utils.logging_config import configure_logging

        with patch("nber_cli.utils.logging_config._default_log_dir", return_value=tmp_path):
            logger = configure_logging(verbose=True)

        assert logger.level == logging.DEBUG

    def test_env_var_debug_sets_debug_level(self, tmp_path):
        from nber_cli.utils.logging_config import configure_logging

        with patch.dict(os.environ, {"NBER_CLI_DEBUG": "1"}):
            with patch("nber_cli.utils.logging_config._default_log_dir", return_value=tmp_path):
                logger = configure_logging(verbose=False)

        assert logger.level == logging.DEBUG

    def test_creates_stderr_handler_when_verbose(self, tmp_path):
        from nber_cli.utils.logging_config import configure_logging

        with patch("nber_cli.utils.logging_config._default_log_dir", return_value=tmp_path):
            logger = configure_logging(verbose=True)

        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
        assert len(stream_handlers) == 1
        assert stream_handlers[0].level == logging.DEBUG

    def test_does_not_create_stderr_handler_by_default(self, tmp_path):
        from nber_cli.utils.logging_config import configure_logging

        with patch("nber_cli.utils.logging_config._default_log_dir", return_value=tmp_path):
            logger = configure_logging(verbose=False)

        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
        assert len(stream_handlers) == 0

    def test_creates_rotating_file_handler(self, tmp_path):
        from nber_cli.utils.logging_config import configure_logging

        with patch("nber_cli.utils.logging_config._default_log_dir", return_value=tmp_path):
            logger = configure_logging(verbose=False)

        file_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(file_handlers) == 1
        assert file_handlers[0].maxBytes == 1_000_000
        assert file_handlers[0].backupCount == 3

    def test_log_format_matches_design(self, tmp_path):
        from nber_cli.utils.logging_config import configure_logging

        with patch("nber_cli.utils.logging_config._default_log_dir", return_value=tmp_path):
            logger = configure_logging(verbose=True)

        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)]
        formatter = stream_handlers[0].formatter
        assert formatter is not None
        assert formatter._fmt == "%(asctime)s %(funcName)s %(message)s"
        assert formatter.datefmt == "%Y-%m-%d %H:%M:%S"

    def test_log_file_path(self, tmp_path):
        from nber_cli.utils.logging_config import configure_logging

        with patch("nber_cli.utils.logging_config._default_log_dir", return_value=tmp_path):
            configure_logging(verbose=False)

        assert (tmp_path / "debug.log").exists()

    def test_clears_existing_handlers_on_reconfigure(self, tmp_path):
        from nber_cli.utils.logging_config import configure_logging

        with patch("nber_cli.utils.logging_config._default_log_dir", return_value=tmp_path):
            logger = configure_logging(verbose=True)
            first_handlers = list(logger.handlers)
            configure_logging(verbose=False)

        assert len(logger.handlers) == 1
        assert logger.handlers[0] not in first_handlers


class TestCliLogging:
    def test_parser_accepts_verbose_flag(self):
        from nber_cli.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["--verbose", "feed", "fetch"])

        assert args.verbose is True

    def test_parser_default_verbose_is_false(self):
        from nber_cli.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["feed", "fetch"])

        assert args.verbose is False


class TestFetcherLogging:
    def test_load_text_sync_logs_request(self, tmp_path, caplog):
        from nber_cli.fetch.fetcher import _load_text_sync

        with patch("nber_cli.utils.logging_config._default_log_dir", return_value=tmp_path):
            from nber_cli.utils.logging_config import configure_logging
            configure_logging(verbose=True)

        class FakeHeaders:
            def get_content_charset(self, default="utf-8"):
                return default

        class FakeResponse:
            def __init__(self):
                self.headers = FakeHeaders()
                self.status = 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b"ok"

        with patch("nber_cli.fetch.fetcher.urlopen", return_value=FakeResponse()):
            with caplog.at_level(logging.DEBUG, logger="nber_cli.fetch.fetcher"):
                _load_text_sync("https://example.com/test")

        assert any("https://example.com/test" in record.message for record in caplog.records)


class TestFeedLogging:
    def test_fetch_feed_logs_counts(self, tmp_path, caplog):
        from nber_cli.fetch import fetch_feed

        with patch("nber_cli.utils.logging_config._default_log_dir", return_value=tmp_path):
            from nber_cli.utils.logging_config import configure_logging
            configure_logging(verbose=True)

        sample_xml = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
<item>
<title>Test -- by A</title>
<description>Abstract.</description>
<link>https://www.nber.org/papers/w00001#fromrss</link>
<guid>https://www.nber.org/papers/w00001#fromrss</guid>
</item>
</channel>
</rss>
"""

        with patch("nber_cli.fetch.feed._load_text_sync", return_value=sample_xml):
            with patch("nber_cli.fetch.feed.db.get_database_path", return_value=tmp_path / "feed.db"):
                with caplog.at_level(logging.DEBUG, logger="nber_cli.fetch.feed"):
                    fetch_feed(db_path=tmp_path / "feed.db")

        assert any("feed fetch complete" in record.message.lower() for record in caplog.records)
