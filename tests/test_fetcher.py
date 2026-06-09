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


class TestParsePage:
    def test_parses_full_page(self):
        page = """<html><head>
<meta name="citation_title" content="Test Paper Title">
<meta name="citation_author" content="Author One">
<meta name="citation_author" content="Author Two">
<meta name="citation_publication_date" content="2024/01/15">
<meta name="citation_technical_report_number" content="w32000">
</head><body>
<div class="page-header__intro-inner">  <p>This is the <em>abstract</em> of the paper.</p></div>
<h2>Published Versions</h2>  <p>Published in <em>Journal of Economics</em>, 2024.</p>
</body></html>"""
        from nber_cli.fetcher import parse_page
        result = parse_page(page)
        assert result.paper_id == 32000
        assert result.title == "Test Paper Title"
        assert result.authors == ["Author One", "Author Two"]
        assert result.date == "2024/01/15"
        assert result.abstract == "This is the abstract of the paper."
        assert result.published_version == "Published in Journal of Economics, 2024."

    def test_handles_missing_fields(self):
        page = "<html><head></head><body></body></html>"
        from nber_cli.fetcher import parse_page
        result = parse_page(page)
        assert result.paper_id == 0
        assert result.title == ""
        assert result.authors == []
        assert result.date == ""
        assert result.abstract == ""
        assert result.published_version is None

    def test_parses_paper_id_with_leading_zeros(self):
        page = '<meta name="citation_technical_report_number" content="w00123">'
        from nber_cli.fetcher import parse_page
        result = parse_page(page)
        assert result.paper_id == 123

    def test_parses_paper_id_without_w_prefix(self):
        page = '<meta name="citation_technical_report_number" content="456">'
        from nber_cli.fetcher import parse_page
        result = parse_page(page)
        assert result.paper_id == 456


class TestExtractAbstract:
    def test_extracts_abstract(self):
        from nber_cli.fetcher import _extract_abstract
        page = '<div class="page-header__intro-inner">\n<p>This is the abstract.</p>\n</div>'
        assert _extract_abstract(page) == "This is the abstract."

    def test_strips_html_tags(self):
        from nber_cli.fetcher import _extract_abstract
        page = '<div class="page-header__intro-inner"><p>Abstract with <em>markup</em> and <a href="#">links</a>.</p></div>'
        assert _extract_abstract(page) == "Abstract with markup and links."

    def test_collapses_whitespace(self):
        from nber_cli.fetcher import _extract_abstract
        page = '<div class="page-header__intro-inner"><p>Abstract\n\nwith   spaces.</p></div>'
        assert _extract_abstract(page) == "Abstract with spaces."

    def test_returns_empty_when_missing(self):
        from nber_cli.fetcher import _extract_abstract
        assert _extract_abstract("<html></html>") == ""


class TestExtractPublishedVersion:
    def test_extracts_published_version(self):
        from nber_cli.fetcher import _extract_published_version
        page = '<h2>Published Versions</h2>\n<p>Published in Journal, 2024.</p>'
        assert _extract_published_version(page) == "Published in Journal, 2024."

    def test_strips_html_tags(self):
        from nber_cli.fetcher import _extract_published_version
        page = '<h2>Published Versions</h2><p>Published in <em>Journal</em>.</p>'
        assert _extract_published_version(page) == "Published in Journal."

    def test_returns_none_when_missing(self):
        from nber_cli.fetcher import _extract_published_version
        assert _extract_published_version("<html></html>") is None


class TestNormalizeDate:
    def test_none_returns_none(self):
        from nber_cli.fetcher import _normalize_date
        assert _normalize_date(None) is None

    def test_date_object_returns_isoformat(self):
        from nber_cli.fetcher import _normalize_date
        assert _normalize_date(date(2024, 1, 15)) == "2024-01-15"

    def test_valid_string_returns_isoformat(self):
        from nber_cli.fetcher import _normalize_date
        assert _normalize_date("2024-01-15") == "2024-01-15"

    def test_rejects_invalid_format(self):
        from nber_cli.fetcher import _normalize_date
        with pytest.raises(ValueError, match="expected YYYY-MM-DD"):
            _normalize_date("01/15/2024")

    def test_rejects_malformed_date(self):
        from nber_cli.fetcher import _normalize_date
        with pytest.raises(ValueError, match="expected YYYY-MM-DD"):
            _normalize_date("2024-13-01")

    def test_rejects_empty_string(self):
        from nber_cli.fetcher import _normalize_date
        with pytest.raises(ValueError, match="expected YYYY-MM-DD"):
            _normalize_date("")


class TestParseSearchResult:
    def test_parses_complete_result(self):
        from nber_cli.fetcher import _parse_search_result
        raw = {
            "url": "/papers/w12345",
            "title": "A Paper",
            "authors": ['<a href="/people/a">Author A</a>'],
            "displaydate": "Jan 2024",
            "abstract": "Abstract text.",
        }
        result = _parse_search_result(raw)
        assert result.paper_id == 12345
        assert result.title == "A Paper"
        assert result.authors == ["Author A"]
        assert result.date == "Jan 2024"
        assert result.abstract == "Abstract text."
        assert result.url == "https://www.nber.org/papers/w12345"

    def test_handles_missing_url(self):
        from nber_cli.fetcher import _parse_search_result
        result = _parse_search_result({})
        assert result.paper_id == 0
        assert result.url == ""

    def test_handles_missing_fields_gracefully(self):
        from nber_cli.fetcher import _parse_search_result
        raw = {"url": "/papers/w99999"}
        result = _parse_search_result(raw)
        assert result.paper_id == 99999
        assert result.title == ""
        assert result.authors == []
        assert result.date == ""
        assert result.abstract == ""

    def test_skips_empty_authors(self):
        from nber_cli.fetcher import _parse_search_result
        raw = {"authors": ["", "Author A", ""]}
        result = _parse_search_result(raw)
        assert result.authors == ["Author A"]

    def test_handles_external_url(self):
        from nber_cli.fetcher import _parse_search_result
        raw = {"url": "https://example.com/papers/w1"}
        result = _parse_search_result(raw)
        assert result.url == "https://example.com/papers/w1"

    def test_handles_none_values(self):
        from nber_cli.fetcher import _parse_search_result
        raw = {
            "url": None,
            "title": None,
            "authors": None,
            "displaydate": None,
            "abstract": None,
        }
        result = _parse_search_result(raw)
        assert result.paper_id == 0
        assert result.title == ""
        assert result.authors == []
        assert result.date == ""
        assert result.abstract == ""

    def test_cleans_html_in_all_fields(self):
        from nber_cli.fetcher import _parse_search_result
        raw = {
            "title": "Title with <em>markup</em>",
            "authors": ['<a href="#">A &amp; B</a>'],
            "displaydate": "Jan 2024",
            "abstract": "Abstract with <br>line break.",
        }
        result = _parse_search_result(raw)
        assert result.title == "Title with markup"
        assert result.authors == ["A & B"]
        assert result.abstract == "Abstract with line break."
