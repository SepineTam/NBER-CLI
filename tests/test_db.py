#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : test_db.py

import json
import sqlite3
from unittest.mock import patch

import pytest

from nber_cli import db



EXPECTED_TABLES = {
    "feed_items",
    "feed_fetches",
    "query_log",
    "download_log",
    "info_log",
    "info_cache",
}


class TestInitDatabase:
    def test_creates_all_tables(self, tmp_path):
        db_path = tmp_path / "nber.db"
        db.init_database(db_path)

        with sqlite3.connect(db_path) as connection:
            table_names = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }

        assert EXPECTED_TABLES.issubset(table_names)

    def test_sets_user_version_to_2(self, tmp_path):
        db_path = tmp_path / "nber.db"
        db.init_database(db_path)

        with sqlite3.connect(db_path) as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]

        assert version == db.SCHEMA_VERSION
        assert version == 2

    def test_writes_schema_version_to_config(self, tmp_path):
        home = tmp_path / "home"
        db_path = home / "nber.db"

        with patch("nber_cli.db.Path.home", return_value=home):
            db.init_database(db_path)

        config_path = home / ".nber-cli" / "config.json"
        config = json.loads(config_path.read_text())

        assert config["schema_version"] == db.SCHEMA_VERSION
        assert config["feed"]["db-path"] == str(db_path)

    def test_init_is_idempotent(self, tmp_path):
        db_path = tmp_path / "nber.db"
        db.init_database(db_path)

        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "INSERT INTO info_cache (paper_id, title, authors_json, date, abstract, "
                "first_cached_at, last_fetched_at) "
                "VALUES ('w1', 'T', '[]', '2024', 'a', '2024', '2024')"
            )

        db.init_database(db_path)

        with sqlite3.connect(db_path) as connection:
            row = connection.execute(
                "SELECT title FROM info_cache WHERE paper_id = 'w1'"
            ).fetchone()

        assert row[0] == "T"


class TestSchemaUpgrade:
    def test_upgrades_v1_to_v2_with_legacy_db(self, tmp_path):
        db_path = tmp_path / "feed.db"

        with sqlite3.connect(db_path) as connection:
            connection.execute(
                """
                CREATE TABLE feed_items (
                    paper_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors_json TEXT NOT NULL,
                    abstract TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    guid TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )
                """
            )
            connection.execute("PRAGMA user_version = 1")
            connection.execute(
                "INSERT INTO feed_items VALUES "
                "('w1', 'Old', '[]', 'a', 'u', 's', 'g', 't', 't')"
            )

        db.init_database(db_path)

        with sqlite3.connect(db_path) as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            row = connection.execute(
                "SELECT title FROM feed_items WHERE paper_id = 'w1'"
            ).fetchone()

        assert version == 2
        assert EXPECTED_TABLES.issubset(tables)
        assert row[0] == "Old"


class TestDatabasePathConfig:
    def test_uses_configured_path(self, tmp_path):
        custom_path = tmp_path / "custom" / "nber.db"

        db.init_database(custom_path)

        assert custom_path.exists()
        assert db.get_database_path() == custom_path

    def test_legacy_feed_db_is_discovered_when_default_missing(self, tmp_path):
        home = tmp_path / "home"
        legacy = home / ".nber-cli" / "feed.db"
        legacy.parent.mkdir(parents=True)

        with sqlite3.connect(legacy) as connection:
            connection.execute("PRAGMA user_version = 1")
            connection.execute(
                """
                CREATE TABLE feed_items (
                    paper_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors_json TEXT NOT NULL,
                    abstract TEXT NOT NULL,
                    url TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    guid TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                )
                """
            )

        with patch("nber_cli.db.Path.home", return_value=home):
            resolved = db.get_database_path()

        assert resolved == legacy


class TestMigrateDatabase:
    def test_moves_file_and_wal_sidecar(self, tmp_path):
        old = tmp_path / "old" / "nber.db"
        new = tmp_path / "new" / "nber.db"
        db.init_database(old)
        old_wal = tmp_path / "old" / "nber.db-wal"
        old_wal.write_text("wal-data")

        old_path, new_path = db.migrate_database(new)

        assert old_path == old
        assert new_path == new
        assert not old.exists()
        assert not old_wal.exists()
        assert new.exists()
        assert (tmp_path / "new" / "nber.db-wal").read_text() == "wal-data"

    def test_rejects_same_path(self, tmp_path):
        path = tmp_path / "nber.db"
        db.init_database(path)

        with pytest.raises(ValueError, match="different"):
            db.migrate_database(path)

    def test_rejects_missing_source(self, tmp_path):
        with pytest.raises(ValueError, match="does not exist"):
            db.migrate_database(tmp_path / "new.db")

    def test_rejects_existing_target(self, tmp_path):
        old = tmp_path / "old.db"
        new = tmp_path / "new.db"
        db.init_database(old)
        new.write_text("existing")

        with pytest.raises(ValueError, match="already exists"):
            db.migrate_database(new)


class TestDatabasePathSecurity:
    def test_init_rejects_path_outside_home_on_unix(self, tmp_path):
        outside_path = tmp_path.parent / "outside.db"
        with patch("nber_cli.db.sys.platform", "linux"):
            with pytest.raises(ValueError, match="within the home directory"):
                db.init_database(outside_path)

    def test_init_allows_path_within_home_on_unix(self, tmp_path):
        inside_path = tmp_path / "nber.db"
        with patch("nber_cli.db.sys.platform", "linux"):
            db.init_database(inside_path)
        assert inside_path.exists()

    def test_migrate_rejects_path_outside_home_on_unix(self, tmp_path):
        old = tmp_path / "old.db"
        outside_new = tmp_path.parent / "outside_new.db"
        db.init_database(old)

        with patch("nber_cli.db.sys.platform", "linux"):
            with pytest.raises(ValueError, match="within the home directory"):
                db.migrate_database(outside_new)

    def test_migrate_allows_path_within_home_on_unix(self, tmp_path):
        old = tmp_path / "old.db"
        new = tmp_path / "new" / "nber.db"
        db.init_database(old)

        with patch("nber_cli.db.sys.platform", "linux"):
            db.migrate_database(new)

        assert new.exists()

    def test_init_allows_any_path_on_windows(self, tmp_path):
        outside_path = tmp_path.parent / "outside.db"
        with patch("nber_cli.db.sys.platform", "win32"):
            db.init_database(outside_path)
        assert outside_path.exists()
