#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : test_feed.py

import json
import sqlite3
from unittest.mock import patch

import pytest

from nber_cli.feed import fetch_feed, init_feed_database, parse_feed_xml

SAMPLE_FEED_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<atom:link href="http://back.nber.org/rss/new.xml" rel="self" type="application/rss+xml" />
<title>National Bureau of Economic Research Working Papers</title>
<description>The Latest NBER Working Papers</description>
<link>http://www.nber.org/new.html</link>
<item>
<title>A Test Paper -- by Person A, Person &amp; B</title>
<description>Abstract with &amp;amp; entity.</description>
<link>https://www.nber.org/papers/w35254#fromrss</link>
<guid>https://www.nber.org/papers/w35254#fromrss</guid>
</item>
<item>
<title>Another Test Paper -- by Person C</title>
<description>Second abstract.</description>
<link>https://www.nber.org/papers/w35255#fromrss</link>
<guid>https://www.nber.org/papers/w35255#fromrss</guid>
</item>
</channel>
</rss>
"""


class TestParseFeedXml:
    def test_parses_items(self):
        items = parse_feed_xml(SAMPLE_FEED_XML)

        assert len(items) == 2
        assert items[0].paper_id == "w35254"
        assert items[0].title == "A Test Paper"
        assert items[0].authors == ["Person A", "Person & B"]
        assert items[0].abstract == "Abstract with & entity."
        assert items[0].url == "https://www.nber.org/papers/w35254"
        assert items[0].source_url == "https://www.nber.org/papers/w35254#fromrss"


class TestInitFeedDatabase:
    def test_initializes_database_and_writes_config(self, tmp_path):
        home = tmp_path / "home"
        db_path = tmp_path / "feed.sqlite"

        with patch("nber_cli.feed.Path.home", return_value=home):
            initialized_path = init_feed_database(db_path)

        config_path = home / ".nber-cli" / "config.json"
        config = json.loads(config_path.read_text())

        assert initialized_path == db_path
        assert config["feed"]["db-path"] == str(db_path)

        with sqlite3.connect(db_path) as connection:
            table_names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }

        assert "feed_items" in table_names
        assert "feed_fetches" in table_names


class TestFetchFeed:
    def test_fetch_returns_only_new_items_by_default(self, tmp_path):
        db_path = tmp_path / "feed.db"

        with patch("nber_cli.feed._load_text_sync", return_value=SAMPLE_FEED_XML):
            first_result = fetch_feed(db_path=db_path)
            second_result = fetch_feed(db_path=db_path)

        assert first_result.total_fetched == 2
        assert first_result.new_count == 2
        assert [item.paper_id for item in first_result.items] == ["w35254", "w35255"]
        assert second_result.total_fetched == 2
        assert second_result.new_count == 0
        assert second_result.items == []

    def test_fetch_display_all_returns_seen_items(self, tmp_path):
        db_path = tmp_path / "feed.db"

        with patch("nber_cli.feed._load_text_sync", return_value=SAMPLE_FEED_XML):
            fetch_feed(db_path=db_path)
            result = fetch_feed(display_all=True, db_path=db_path)

        assert result.total_fetched == 2
        assert result.new_count == 0
        assert [item.paper_id for item in result.items] == ["w35254", "w35255"]

    def test_fetch_max_items_limits_output_without_limiting_storage(self, tmp_path):
        db_path = tmp_path / "feed.db"

        with patch("nber_cli.feed._load_text_sync", return_value=SAMPLE_FEED_XML):
            result = fetch_feed(db_path=db_path, max_items=1)

        assert result.total_fetched == 2
        assert result.new_count == 2
        assert result.max_items == 1
        assert [item.paper_id for item in result.items] == ["w35254"]

        with sqlite3.connect(db_path) as connection:
            stored_count = connection.execute("SELECT COUNT(*) FROM feed_items").fetchone()[0]

        assert stored_count == 2

    def test_fetch_allows_zero_max_items(self, tmp_path):
        db_path = tmp_path / "feed.db"

        with patch("nber_cli.feed._load_text_sync", return_value=SAMPLE_FEED_XML):
            result = fetch_feed(db_path=db_path, max_items=0)

        assert result.new_count == 2
        assert result.items == []

    def test_fetch_rejects_invalid_max_items(self, tmp_path):
        db_path = tmp_path / "feed.db"

        with patch("nber_cli.feed._load_text_sync", return_value=SAMPLE_FEED_XML):
            with pytest.raises(ValueError, match="max_items"):
                fetch_feed(db_path=db_path, max_items=-1)

    def test_fetch_records_fetch_history(self, tmp_path):
        db_path = tmp_path / "feed.db"

        with patch("nber_cli.feed._load_text_sync", return_value=SAMPLE_FEED_XML):
            fetch_feed(db_path=db_path)

        with sqlite3.connect(db_path) as connection:
            row = connection.execute(
                "SELECT total_count, new_count FROM feed_fetches"
            ).fetchone()

        assert row == (2, 2)
