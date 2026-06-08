#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : test_fetcher.py

from datetime import date
from urllib.error import URLError
from unittest.mock import MagicMock, patch

import pytest

from nber_cli.config import NBER_CLI_CONFIG
from nber_cli.fetcher import _build_search_params, _load_text_sync, _parse_search_payload


class TestConfigDefaults:
    def test_request_defaults(self):
        assert NBER_CLI_CONFIG.request_timeout_seconds == 60
        assert NBER_CLI_CONFIG.request_retry_count == 3
        assert NBER_CLI_CONFIG.request_attempts == 4


class TestBuildSearchParams:
    def test_keyword_search_params(self):
        params = _build_search_params(" inflation ", page=2, per_page=50)
        assert params == {
            "page": 2,
            "perPage": 50,
            "q": "inflation",
        }

    def test_start_date_adds_today_as_end_date(self):
        params = _build_search_params(
            "inflation",
            start_date="2024-01-01",
            today=date(2024, 2, 3),
        )
        assert params["startDate"] == "2024-01-01"
        assert params["endDate"] == "2024-02-03"

    def test_end_date_can_be_used_by_itself(self):
        params = _build_search_params("inflation", end_date=date(2024, 1, 1))
        assert params["endDate"] == "2024-01-01"
        assert "startDate" not in params

    def test_rejects_empty_query(self):
        with pytest.raises(ValueError, match="query must not be empty"):
            _build_search_params("")

    def test_rejects_invalid_date(self):
        with pytest.raises(ValueError, match="expected YYYY-MM-DD"):
            _build_search_params("inflation", start_date="01/01/2024")

    def test_rejects_reversed_dates(self):
        with pytest.raises(ValueError, match="start_date"):
            _build_search_params(
                "inflation",
                start_date="2024-02-01",
                end_date="2024-01-01",
            )

    def test_rejects_unsupported_page_size(self):
        with pytest.raises(ValueError, match="20, 50, or 100"):
            _build_search_params("inflation", per_page=1)


class TestParseSearchPayload:
    def test_parse_result_payload(self):
        payload = {
            "totalResults": 1,
            "results": [
                {
                    "authors": [
                        '<a href="/people/person_a">Person A</a>',
                        '<a href="/people/person_b">Person &amp; B</a>',
                    ],
                    "displaydate": "January 2024",
                    "abstract": "Abstract with <em>markup</em>.",
                    "title": "A Test Paper",
                    "url": "/papers/w32000",
                }
            ],
        }
        params = {
            "q": "inflation",
            "page": 1,
            "perPage": 20,
            "startDate": "2024-01-01",
            "endDate": "2024-02-01",
        }

        results = _parse_search_payload(payload, params)

        assert results.total_results == 1
        assert results.query == "inflation"
        assert results.start_date == "2024-01-01"
        assert results.end_date == "2024-02-01"
        assert results.results[0].paper_id == 32000
        assert results.results[0].authors == ["Person A", "Person & B"]
        assert results.results[0].url == "https://www.nber.org/papers/w32000"
        assert results.results[0].abstract == "Abstract with markup."


class TestLoadTextSyncRetry:
    def test_retries_on_network_error(self):
        class FakeResponse:
            def __init__(self, text_value: str):
                self._text_value = text_value
                self.headers = MagicMock()
                self.headers.get_content_charset.return_value = "utf-8"

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return self._text_value.encode("utf-8")

        calls = [URLError("temporary failure"), URLError("temporary failure"), FakeResponse("ok")]

        def fake_urlopen(request, timeout, context=None):
            result = calls.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with patch("nber_cli.fetcher.urlopen", side_effect=fake_urlopen):
            with patch("nber_cli.fetcher.time.sleep") as mock_sleep:
                text = _load_text_sync("https://example.com")

        assert text == "ok"
        assert mock_sleep.call_count == 2
