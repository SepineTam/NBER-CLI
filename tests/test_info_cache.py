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

import pytest

from nber_cli import db
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
