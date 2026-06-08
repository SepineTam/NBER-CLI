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

from nber_cli.feed import (
    clean_feed_cache,
    fetch_feed,
    init_feed_database,
    migrate_feed_database,
    parse_feed_xml,
)

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


def _insert_cached_feed_item(db_path, paper_id: str, last_seen_at: str) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO feed_items (
                paper_id,
                title,
                authors_json,
                abstract,
                url,
                source_url,
                guid,
                first_seen_at,
                last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper_id,
                f"Title {paper_id}",
                "[]",
                "",
                f"https://www.nber.org/papers/{paper_id}",
                f"https://www.nber.org/papers/{paper_id}#fromrss",
                f"https://www.nber.org/papers/{paper_id}#fromrss",
                last_seen_at,
                last_seen_at,
            ),
        )


def _cached_feed_ids(db_path) -> list[str]:
    with sqlite3.connect(db_path) as connection:
        return [
            row[0]
            for row in connection.execute(
                "SELECT paper_id FROM feed_items ORDER BY paper_id"
            ).fetchall()
        ]


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

    def test_rejects_xml_with_external_entities(self):
        malicious_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE rss [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<rss version="2.0">
<channel>
<item>
<title>Test -- by A</title>
<description>&xxe;</description>
<link>https://www.nber.org/papers/w00001#fromrss</link>
<guid>https://www.nber.org/papers/w00001#fromrss</guid>
</item>
</channel>
</rss>
"""
        with pytest.raises(ValueError, match="invalid NBER RSS XML"):
            parse_feed_xml(malicious_xml)

    def test_rejects_xml_with_billion_laughs(self):
        malicious_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE rss [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<rss version="2.0">
<channel>
<item>
<title>Test -- by A</title>
<description>&lol3;</description>
<link>https://www.nber.org/papers/w00001#fromrss</link>
<guid>https://www.nber.org/papers/w00001#fromrss</guid>
</item>
</channel>
</rss>
"""
        with pytest.raises(ValueError, match="invalid NBER RSS XML"):
            parse_feed_xml(malicious_xml)


class TestInitFeedDatabase:
    def test_initializes_database_and_writes_config(self, tmp_path):
        home = tmp_path / "home"
        db_path = tmp_path / "feed.sqlite"

        with patch("nber_cli.db.Path.home", return_value=home):
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


class TestMigrateFeedDatabase:
    def test_migrates_configured_database_and_updates_config(self, tmp_path):
        home = tmp_path / "home"
        old_db_path = tmp_path / "old" / "feed.db"
        new_db_path = tmp_path / "new" / "feed.db"

        with patch("nber_cli.db.Path.home", return_value=home):
            init_feed_database(old_db_path)
            old_path, new_path = migrate_feed_database(new_db_path)

        config_path = home / ".nber-cli" / "config.json"
        config = json.loads(config_path.read_text())

        assert old_path == old_db_path
        assert new_path == new_db_path
        assert not old_db_path.exists()
        assert new_db_path.exists()
        assert config["feed"]["db-path"] == str(new_db_path)

    def test_migrates_default_database_when_config_is_missing(self, tmp_path):
        home = tmp_path / "home"
        new_db_path = tmp_path / "new" / "feed.db"

        with patch("nber_cli.db.Path.home", return_value=home):
            default_db_path = home / ".nber-cli" / "feed.db"
            init_feed_database(default_db_path)
            (home / ".nber-cli" / "config.json").unlink()

            old_path, new_path = migrate_feed_database(new_db_path)

        assert old_path == default_db_path
        assert new_path == new_db_path
        assert not default_db_path.exists()
        assert new_db_path.exists()

    def test_migrates_sqlite_sidecar_files(self, tmp_path):
        home = tmp_path / "home"
        old_db_path = tmp_path / "old" / "feed.db"
        new_db_path = tmp_path / "new" / "feed.db"

        with patch("nber_cli.db.Path.home", return_value=home):
            init_feed_database(old_db_path)
            old_wal_path = tmp_path / "old" / "feed.db-wal"
            old_shm_path = tmp_path / "old" / "feed.db-shm"
            old_wal_path.write_text("wal")
            old_shm_path.write_text("shm")

            migrate_feed_database(new_db_path)

        assert not old_wal_path.exists()
        assert not old_shm_path.exists()
        assert (tmp_path / "new" / "feed.db-wal").read_text() == "wal"
        assert (tmp_path / "new" / "feed.db-shm").read_text() == "shm"

    def test_rejects_missing_source_database(self, tmp_path):
        home = tmp_path / "home"
        new_db_path = tmp_path / "new" / "feed.db"

        with patch("nber_cli.db.Path.home", return_value=home):
            with pytest.raises(ValueError, match="does not exist"):
                migrate_feed_database(new_db_path)

    def test_rejects_existing_target_database(self, tmp_path):
        home = tmp_path / "home"
        old_db_path = tmp_path / "old" / "feed.db"
        new_db_path = tmp_path / "new" / "feed.db"

        with patch("nber_cli.db.Path.home", return_value=home):
            init_feed_database(old_db_path)
            new_db_path.parent.mkdir(parents=True)
            new_db_path.write_text("existing")

            with pytest.raises(ValueError, match="already exists"):
                migrate_feed_database(new_db_path)

        assert old_db_path.exists()
        assert new_db_path.read_text() == "existing"

    def test_rejects_same_database_path(self, tmp_path):
        home = tmp_path / "home"
        db_path = tmp_path / "feed.db"

        with patch("nber_cli.db.Path.home", return_value=home):
            init_feed_database(db_path)

            with pytest.raises(ValueError, match="different"):
                migrate_feed_database(db_path)


class TestCleanFeedCache:
    def test_defaults_to_cleaning_records_not_seen_for_30_days(self, tmp_path):
        db_path = tmp_path / "feed.db"
        init_feed_database(db_path)
        _insert_cached_feed_item(db_path, "w10001", "2026-04-30T00:00:00+00:00")
        _insert_cached_feed_item(db_path, "w10002", "2026-05-20T00:00:00+00:00")

        with patch("nber_cli.db._utc_now", return_value="2026-06-03T00:00:00+00:00"):
            result = clean_feed_cache(db_path=db_path)

        assert result.mode == "days"
        assert result.days == 30
        assert result.matched_count == 1
        assert result.deleted_count == 1
        assert _cached_feed_ids(db_path) == ["w10002"]

    def test_dry_run_counts_without_deleting(self, tmp_path):
        db_path = tmp_path / "feed.db"
        init_feed_database(db_path)
        _insert_cached_feed_item(db_path, "w10001", "2026-04-30T00:00:00+00:00")

        with patch("nber_cli.db._utc_now", return_value="2026-06-03T00:00:00+00:00"):
            result = clean_feed_cache(db_path=db_path, dry_run=True)

        assert result.dry_run is True
        assert result.matched_count == 1
        assert result.deleted_count == 0
        assert _cached_feed_ids(db_path) == ["w10001"]

    def test_deletes_all_cached_records(self, tmp_path):
        db_path = tmp_path / "feed.db"
        init_feed_database(db_path)
        _insert_cached_feed_item(db_path, "w10001", "2026-05-01T00:00:00+00:00")
        _insert_cached_feed_item(db_path, "w10002", "2026-06-01T00:00:00+00:00")

        result = clean_feed_cache(db_path=db_path, delete_all=True)

        assert result.mode == "all"
        assert result.matched_count == 2
        assert result.deleted_count == 2
        assert _cached_feed_ids(db_path) == []

    def test_end_date_cleans_from_earliest_record_inclusively(self, tmp_path):
        db_path = tmp_path / "feed.db"
        init_feed_database(db_path)
        _insert_cached_feed_item(db_path, "w10001", "2026-05-01T00:00:00+00:00")
        _insert_cached_feed_item(db_path, "w10002", "2026-05-31T23:59:59+00:00")
        _insert_cached_feed_item(db_path, "w10003", "2026-06-01T00:00:00+00:00")

        result = clean_feed_cache(db_path=db_path, end_date="2026-05-31")

        assert result.mode == "date-range"
        assert result.start_date is None
        assert result.end_date == "2026-05-31"
        assert result.matched_count == 2
        assert _cached_feed_ids(db_path) == ["w10003"]

    def test_start_and_end_date_are_inclusive(self, tmp_path):
        db_path = tmp_path / "feed.db"
        init_feed_database(db_path)
        _insert_cached_feed_item(db_path, "w10001", "2026-05-01T00:00:00+00:00")
        _insert_cached_feed_item(db_path, "w10002", "2026-05-15T00:00:00+00:00")
        _insert_cached_feed_item(db_path, "w10003", "2026-05-31T23:59:59+00:00")
        _insert_cached_feed_item(db_path, "w10004", "2026-06-01T00:00:00+00:00")

        result = clean_feed_cache(
            db_path=db_path,
            start_date="2026-05-01",
            end_date="2026-05-31",
        )

        assert result.matched_count == 3
        assert result.deleted_count == 3
        assert _cached_feed_ids(db_path) == ["w10004"]

    def test_rejects_start_date_without_end_date(self, tmp_path):
        db_path = tmp_path / "feed.db"
        init_feed_database(db_path)

        with pytest.raises(ValueError, match="end-date is required"):
            clean_feed_cache(db_path=db_path, start_date="2026-05-01")

    def test_rejects_multiple_clean_modes(self, tmp_path):
        db_path = tmp_path / "feed.db"
        init_feed_database(db_path)

        with pytest.raises(ValueError, match="only one"):
            clean_feed_cache(db_path=db_path, days=30, delete_all=True)

    def test_rejects_missing_database(self, tmp_path):
        db_path = tmp_path / "missing.db"

        with pytest.raises(ValueError, match="does not exist"):
            clean_feed_cache(db_path=db_path)


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
