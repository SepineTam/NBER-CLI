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
    observed: list[tuple[bool, Path]] = []

    def fake_fetch_feed(*, display_all, db_path):
        observed.append((display_all, db_path))
        return SimpleNamespace(
            total_fetched=12,
            new_count=4,
            items=[SimpleNamespace(paper_id="w123")],
        )

    async def fake_prefetch(paper_ids, *, db_path):
        assert paper_ids == ["w123"]
        return desktop_worker.FeedInfoPrefetchResult(1, 10, 1)

    monkeypatch.setattr(desktop_worker, "fetch_feed", fake_fetch_feed)
    monkeypatch.setattr(desktop_worker, "prefetch_feed_info", fake_prefetch)

    desktop_worker.main(["--db-path", str(db_path), "feed-fetch"])

    assert observed == [(True, db_path)]
    assert json.loads(capsys.readouterr().out) == {
        "fetched_count": 12,
        "new_count": 4,
        "info_fetched_count": 1,
        "info_cached_count": 10,
        "info_failed_count": 1,
    }


@pytest.mark.asyncio
async def test_prefetch_feed_info_keeps_partial_success(tmp_path, monkeypatch):
    db_path = tmp_path / "nber.db"
    observed: list[int] = []

    async def fake_get_paper(paper_id, *, db_path):
        observed.append(paper_id)
        if paper_id == 3:
            raise TimeoutError
        return SimpleNamespace(from_cache=paper_id == 2)

    monkeypatch.setattr(
        desktop_worker,
        "get_paper_with_info_cache_result",
        fake_get_paper,
    )
    monkeypatch.setattr(
        desktop_worker.config_store,
        "get_info_cache_settings",
        lambda: SimpleNamespace(cache_enabled=True),
    )

    result = await desktop_worker.prefetch_feed_info(
        ["w1", "w2", "w3", "w1"],
        db_path=db_path,
        budget_seconds=1,
    )
    assert sorted(observed) == [1, 2, 3]
    assert result == desktop_worker.FeedInfoPrefetchResult(
        fetched_count=1,
        cached_count=1,
        failed_count=1,
    )


@pytest.mark.asyncio
async def test_prefetch_refreshes_legacy_cache_without_tags(tmp_path, monkeypatch):
    calls: list[bool] = []

    async def fake_get_paper(paper_id, *, refresh=False, db_path):
        calls.append(refresh)
        if not refresh:
            paper = SimpleNamespace(topic=None, programs=None)
            return SimpleNamespace(from_cache=True, paper=paper)
        paper = SimpleNamespace(topic="Labor Economics", programs="Labor Studies")
        return SimpleNamespace(from_cache=False, paper=paper)

    monkeypatch.setattr(
        desktop_worker,
        "get_paper_with_info_cache_result",
        fake_get_paper,
    )

    status = await desktop_worker._prefetch_one_paper(
        123,
        db_path=tmp_path / "nber.db",
        semaphore=desktop_worker.asyncio.Semaphore(1),
    )

    assert calls == [False, True]
    assert status == "fetched"


@pytest.mark.asyncio
async def test_prefetch_feed_info_respects_concurrency(tmp_path, monkeypatch):
    active = 0
    max_active = 0

    async def fake_get_paper(paper_id, *, db_path):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await desktop_worker.asyncio.sleep(0.01)
        active -= 1
        return SimpleNamespace(from_cache=False)

    monkeypatch.setattr(
        desktop_worker,
        "get_paper_with_info_cache_result",
        fake_get_paper,
    )
    monkeypatch.setattr(
        desktop_worker.config_store,
        "get_info_cache_settings",
        lambda: SimpleNamespace(cache_enabled=True),
    )

    result = await desktop_worker.prefetch_feed_info(
        ["w1", "w2", "w3", "w4"],
        db_path=tmp_path / "nber.db",
        concurrency=2,
        budget_seconds=1,
    )

    assert max_active == 2
    assert result.fetched_count == 4


@pytest.mark.asyncio
async def test_prefetch_feed_info_stops_at_budget(tmp_path, monkeypatch):
    async def slow_get_paper(paper_id, *, db_path):
        await desktop_worker.asyncio.sleep(1)
        return SimpleNamespace(from_cache=False)

    monkeypatch.setattr(
        desktop_worker,
        "get_paper_with_info_cache_result",
        slow_get_paper,
    )
    monkeypatch.setattr(
        desktop_worker.config_store,
        "get_info_cache_settings",
        lambda: SimpleNamespace(cache_enabled=True),
    )

    result = await desktop_worker.prefetch_feed_info(
        ["w1", "w2"],
        db_path=tmp_path / "nber.db",
        budget_seconds=0.01,
    )

    assert result == desktop_worker.FeedInfoPrefetchResult(0, 0, 2)


@pytest.mark.asyncio
async def test_prefetch_feed_info_accepts_empty_feed(tmp_path):
    result = await desktop_worker.prefetch_feed_info(
        [],
        db_path=tmp_path / "nber.db",
    )

    assert result == desktop_worker.FeedInfoPrefetchResult(0, 0, 0)


@pytest.mark.asyncio
async def test_prefetch_feed_info_skips_when_cache_is_disabled(tmp_path, monkeypatch):
    async def unexpected_get_paper(*args, **kwargs):
        raise AssertionError("metadata should not be fetched when caching is disabled")

    monkeypatch.setattr(
        desktop_worker,
        "get_paper_with_info_cache_result",
        unexpected_get_paper,
    )
    monkeypatch.setattr(
        desktop_worker.config_store,
        "get_info_cache_settings",
        lambda: SimpleNamespace(cache_enabled=False),
    )

    result = await desktop_worker.prefetch_feed_info(
        ["w1"],
        db_path=tmp_path / "nber.db",
    )

    assert result == desktop_worker.FeedInfoPrefetchResult(0, 0, 0)


def test_worker_reports_json_error(tmp_path, monkeypatch, capsys):
    def fail_fetch(*, display_all, db_path):
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
