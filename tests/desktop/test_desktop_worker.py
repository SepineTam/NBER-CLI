from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from nber_cli import desktop_worker


def test_worker_initializes_database(tmp_path, capsys):
    db_path = tmp_path / "nber.db"

    desktop_worker.main(["--db-path", str(db_path), "init"])

    payload = json.loads(capsys.readouterr().out)
    assert payload["database_path"] == str(db_path)
    assert payload["schema_version"] == 3
    assert db_path.exists()


def test_worker_feed_fetch_uses_existing_python_fetcher(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "nber.db"
    observed: list[Path] = []

    def fake_fetch_feed(*, db_path):
        observed.append(db_path)
        return SimpleNamespace(total_fetched=12, new_count=4)

    monkeypatch.setattr(desktop_worker, "fetch_feed", fake_fetch_feed)

    desktop_worker.main(["--db-path", str(db_path), "feed-fetch"])

    assert observed == [db_path]
    assert json.loads(capsys.readouterr().out) == {
        "fetched_count": 12,
        "new_count": 4,
    }


def test_worker_paper_info_uses_existing_python_cache(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "nber.db"
    observed: list[tuple[int, Path]] = []

    async def fake_get_paper(paper_id, *, db_path):
        observed.append((paper_id, db_path))
        paper = SimpleNamespace(
            paper_id=12345,
            title="A Paper",
            authors=["Ada Lovelace"],
            date="2026-07-18",
            abstract="An abstract",
            url=None,
            published_version=None,
            topic="Economics",
            programs="EFG",
        )
        return SimpleNamespace(paper=paper, from_cache=True)

    recorded: list[tuple[Path, int]] = []
    monkeypatch.setattr(
        desktop_worker,
        "get_paper_with_info_cache_result",
        fake_get_paper,
    )
    monkeypatch.setattr(
        desktop_worker.db,
        "record_info",
        lambda path, paper_id: recorded.append((path, paper_id)),
    )

    desktop_worker.main(["--db-path", str(db_path), "paper-info", "w12345"])

    payload = json.loads(capsys.readouterr().out)
    assert observed == [(12345, db_path)]
    assert recorded == [(db_path, 12345)]
    assert payload["paper_id"] == "w12345"
    assert payload["url"] == "https://www.nber.org/papers/w12345"
    assert payload["from_cache"] is True


def test_worker_reports_json_error(tmp_path, monkeypatch, capsys):
    def fail_fetch(*, db_path):
        raise RuntimeError(f"cannot update {db_path.name}")

    monkeypatch.setattr(desktop_worker, "fetch_feed", fail_fetch)

    with pytest.raises(SystemExit, match="1"):
        desktop_worker.main(
            ["--db-path", str(tmp_path / "nber.db"), "feed-fetch"]
        )

    payload = json.loads(capsys.readouterr().err)
    assert payload["error"] == "RuntimeError"
    assert payload["message"] == "cannot update nber.db"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("123", 123), ("w00123", 123), (" W42 ", 42)],
)
def test_worker_normalizes_paper_id(value, expected):
    assert desktop_worker._paper_number(value) == expected


def test_worker_rejects_invalid_paper_id():
    with pytest.raises(Exception, match="paper_id must look like"):
        desktop_worker._paper_number("paper")
