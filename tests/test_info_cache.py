#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : test_info_cache.py

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from nber_cli import db
from nber_cli.config_store import InfoCacheSettings
from nber_cli.core.models import NBER


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "nber.db"
    db.init_database(path)
    return path


def _make_paper(paper_id: int = 1234) -> NBER:
    return NBER(
        paper_id=paper_id,
        title="A Paper",
        authors=["Author A", "Author B"],
        date="2024-01-15",
        abstract="An abstract.",
        url="https://www.nber.org/papers/w1234",
        published_version="Published in J. Econ.",
        topic="Labor Studies",
        programs="Labor Studies",
    )


def _utc_timestamp(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(
        timespec="seconds"
    )


def _set_cache_timestamps(
    db_path,
    paper_id: str,
    *,
    first_cached_at: str | None = None,
    last_fetched_at: str | None = None,
) -> None:
    assignments = []
    values = []
    if first_cached_at is not None:
        assignments.append("first_cached_at = ?")
        values.append(first_cached_at)
    if last_fetched_at is not None:
        assignments.append("last_fetched_at = ?")
        values.append(last_fetched_at)
    values.append(paper_id)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            f"UPDATE info_cache SET {', '.join(assignments)} WHERE paper_id = ?",
            values,
        )


class TestReadInfoCache:
    def test_returns_none_when_db_missing(self, tmp_path):
        path = tmp_path / "missing.db"
        assert db.read_info_cache(path, 1234) is None

    def test_returns_none_when_paper_not_cached(self, db_path):
        assert db.read_info_cache(db_path, 1234) is None

    def test_returns_paper_after_write(self, db_path):
        db.write_info_cache(db_path, _make_paper())

        paper = db.read_info_cache(db_path, 1234)

        assert paper is not None
        assert paper.paper_id == 1234
        assert paper.title == "A Paper"
        assert paper.authors == ["Author A", "Author B"]
        assert paper.date == "2024-01-15"
        assert paper.abstract == "An abstract."
        assert paper.published_version == "Published in J. Econ."

    def test_accepts_paper_id_with_w_prefix(self, db_path):
        db.write_info_cache(db_path, _make_paper())

        paper = db.read_info_cache(db_path, "w1234")
        assert paper is not None
        assert paper.paper_id == 1234

    def test_returns_none_without_querying_db_when_cache_disabled(self, db_path):
        with (
            patch(
                "nber_cli.db.config_store.get_info_cache_settings",
                return_value=InfoCacheSettings(cache_enabled=False, cache_ttl_days=30),
            ),
            patch("nber_cli.db.sqlite3.connect") as mock_connect,
        ):
            paper = db.read_info_cache(db_path, 1234)

        assert paper is None
        mock_connect.assert_not_called()

    def test_returns_none_when_last_fetched_at_is_expired(self, db_path):
        db.write_info_cache(db_path, _make_paper())
        _set_cache_timestamps(db_path, "w1234", last_fetched_at=_utc_timestamp(31))

        assert db.read_info_cache(db_path, 1234, ttl_days=30) is None

    def test_expiration_uses_last_fetched_at_not_first_cached_at(self, db_path):
        db.write_info_cache(db_path, _make_paper())
        _set_cache_timestamps(
            db_path,
            "w1234",
            first_cached_at=_utc_timestamp(90),
            last_fetched_at=_utc_timestamp(1),
        )

        assert db.read_info_cache(db_path, 1234, ttl_days=30) is not None

    def test_fresh_first_cached_at_does_not_hide_expired_last_fetched_at(self, db_path):
        db.write_info_cache(db_path, _make_paper())
        _set_cache_timestamps(
            db_path,
            "w1234",
            first_cached_at=_utc_timestamp(1),
            last_fetched_at=_utc_timestamp(90),
        )

        assert db.read_info_cache(db_path, 1234, ttl_days=30) is None


class TestWriteInfoCache:
    def test_inserts_new_record(self, db_path):
        db.write_info_cache(db_path, _make_paper())

        with sqlite3.connect(db_path) as connection:
            row = connection.execute(
                "SELECT title, authors_json, fetch_count FROM info_cache "
                "WHERE paper_id = 'w1234'"
            ).fetchone()

        assert row[0] == "A Paper"
        assert json.loads(row[1]) == ["Author A", "Author B"]
        assert row[2] == 0

    def test_upsert_preserves_first_cached_at(self, db_path):
        paper = _make_paper()
        db.write_info_cache(db_path, paper)
        with sqlite3.connect(db_path) as connection:
            first = connection.execute(
                "SELECT first_cached_at FROM info_cache WHERE paper_id = 'w1234'"
            ).fetchone()[0]

        paper.title = "Updated"
        db.write_info_cache(db_path, paper)

        with sqlite3.connect(db_path) as connection:
            row = connection.execute(
                "SELECT title, first_cached_at FROM info_cache WHERE paper_id = 'w1234'"
            ).fetchone()

        assert row[0] == "Updated"
        assert row[1] == first

    def test_upsert_does_not_reset_fetch_count(self, db_path):
        db.write_info_cache(db_path, _make_paper())
        db.touch_info_cache(db_path, 1234)
        db.touch_info_cache(db_path, 1234)

        db.write_info_cache(
            db_path,
            NBER(
                paper_id=1234,
                title="New Title",
                authors=["Author A"],
                date="2024-01-15",
                abstract="An abstract.",
            ),
        )

        with sqlite3.connect(db_path) as connection:
            count = connection.execute(
                "SELECT fetch_count FROM info_cache WHERE paper_id = 'w1234'"
            ).fetchone()[0]

        assert count == 2


class TestTouchInfoCache:
    def test_updates_last_fetched_at_and_increments_count(self, db_path):
        db.write_info_cache(db_path, _make_paper())

        db.touch_info_cache(db_path, 1234)
        db.touch_info_cache(db_path, 1234)

        with sqlite3.connect(db_path) as connection:
            row = connection.execute(
                "SELECT fetch_count, last_fetched_at FROM info_cache "
                "WHERE paper_id = 'w1234'"
            ).fetchone()

        assert row[0] == 2
        assert row[1] is not None

    def test_no_op_when_paper_not_cached(self, db_path):
        db.touch_info_cache(db_path, 9999)

        with sqlite3.connect(db_path) as connection:
            count = connection.execute("SELECT COUNT(*) FROM info_cache").fetchone()[0]

        assert count == 0


class TestClearInfoCache:
    def test_clear_days_uses_last_fetched_at(self, db_path):
        db.write_info_cache(db_path, _make_paper(1234))
        db.write_info_cache(db_path, _make_paper(5678))
        _set_cache_timestamps(db_path, "w1234", last_fetched_at=_utc_timestamp(10))
        _set_cache_timestamps(db_path, "w5678", last_fetched_at=_utc_timestamp(1))

        preview = db.clear_info_cache(days=7, dry_run=True, db_path=db_path)
        result = db.clear_info_cache(days=7, db_path=db_path)

        assert preview.matched_count == 1
        assert preview.deleted_count == 0
        assert result.deleted_count == 1
        with sqlite3.connect(db_path) as connection:
            rows = [
                row[0]
                for row in connection.execute(
                    "SELECT paper_id FROM info_cache ORDER BY paper_id"
                )
            ]
        assert rows == ["w5678"]

    def test_clear_all_deletes_everything(self, db_path):
        db.write_info_cache(db_path, _make_paper(1234))
        db.write_info_cache(db_path, _make_paper(5678))

        result = db.clear_info_cache(delete_all=True, db_path=db_path)

        assert result.mode == "all"
        assert result.deleted_count == 2
        assert db.count_info_cache(db_path) == 0

    def test_clear_date_range_matches_fetched_dates(self, db_path):
        db.write_info_cache(db_path, _make_paper(1234))
        db.write_info_cache(db_path, _make_paper(5678))
        _set_cache_timestamps(db_path, "w1234", last_fetched_at="2026-05-10T00:00:00+00:00")
        _set_cache_timestamps(db_path, "w5678", last_fetched_at="2026-06-01T00:00:00+00:00")

        result = db.clear_info_cache(
            start_date="2026-05-01",
            end_date="2026-05-31",
            db_path=db_path,
        )

        assert result.mode == "date-range"
        assert result.deleted_count == 1
        with sqlite3.connect(db_path) as connection:
            row = connection.execute("SELECT paper_id FROM info_cache").fetchone()
        assert row[0] == "w5678"

    def test_clear_rejects_mixed_modes(self, db_path):
        with pytest.raises(ValueError, match="choose only one"):
            db.clear_info_cache(days=7, delete_all=True, db_path=db_path)

    def test_clear_requires_end_date_when_start_date_is_provided(self, db_path):
        with pytest.raises(ValueError, match="end-date is required"):
            db.clear_info_cache(start_date="2026-05-01", db_path=db_path)
