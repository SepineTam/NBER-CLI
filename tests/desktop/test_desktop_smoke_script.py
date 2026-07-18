from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_smoke_script():
    script = ROOT / "scripts" / "smoke-desktop-app.py"
    spec = importlib.util.spec_from_file_location("smoke_desktop_app", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_linux_smoke_installs_appimage_with_bundled_worker(tmp_path):
    smoke = _load_smoke_script()
    package = tmp_path / "NBER-CLI-Desktop-v0-8-1-Linux-x64.AppImage"
    # Simulate --appimage-extract output layout.
    (tmp_path / "squashfs-root" / "usr" / "bin").mkdir(parents=True)
    app = tmp_path / "squashfs-root" / "usr" / "bin" / "app"
    app.write_bytes(b"app")
    (app.parent / "nber-worker").write_bytes(b"worker")

    # The helper expects the package to exist, so create a dummy executable script.
    package.write_text("#!/bin/sh\n:\n", encoding="utf-8")
    package.chmod(package.stat().st_mode | 0o111)

    executable = smoke._install_linux_package(package, tmp_path)

    assert executable == app


def test_windows_smoke_does_not_treat_sidecar_or_uninstaller_as_app(tmp_path):
    smoke = _load_smoke_script()
    sidecar = tmp_path / "nber-sidecar.exe"
    worker = tmp_path / "nber-worker.exe"
    uninstaller = tmp_path / "Uninstall NBER-CLI Desktop.exe"
    app = tmp_path / "NBER-CLI Desktop.exe"
    for path in (sidecar, worker, uninstaller, app):
        path.write_bytes(b"exe")

    assert smoke._is_windows_app_executable(sidecar) is False
    assert smoke._is_windows_app_executable(worker) is False
    assert smoke._is_windows_app_executable(uninstaller) is False
    assert smoke._is_windows_app_executable(app) is True


def test_smoke_seed_uses_desktop_settings(tmp_path):
    smoke = _load_smoke_script()

    smoke._seed_sample_environment(tmp_path)

    config = json.loads((tmp_path / ".nber-cli" / "config.json").read_text())
    assert config["desktop"]["feed_refresh_interval_minutes"] == 60


def test_smoke_uses_headless_desktop_runtime_mode():
    script = (ROOT / "scripts" / "smoke-desktop-app.py").read_text(encoding="utf-8")

    assert 'env["NBER_DESKTOP_INIT_ONLY"] = "1"' in script
    assert 'env["PATH"] = ""' in script


def test_desktop_runtime_ready_requires_schema_and_database_path(tmp_path):
    smoke = _load_smoke_script()
    smoke._seed_sample_environment(tmp_path)
    assert smoke._desktop_runtime_ready(tmp_path) is False

    config_path = tmp_path / ".nber-cli" / "config.json"
    db_path = tmp_path / ".nber-cli" / "nber.db"
    config = json.loads(config_path.read_text())
    config["feed"] = {"db-path": str(db_path)}
    config_path.write_text(json.dumps(config), encoding="utf-8")
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE read_status (paper_id TEXT PRIMARY KEY, is_read BOOLEAN, updated_at TEXT)"
        )
        connection.execute("PRAGMA user_version = 3")

    assert smoke._desktop_runtime_ready(tmp_path) is True


def test_bundled_worker_is_found_beside_executable(tmp_path, monkeypatch):
    smoke = _load_smoke_script()
    monkeypatch.setattr(smoke.platform, "system", lambda: "Linux")
    app = tmp_path / "app"
    worker = tmp_path / "nber-worker"
    app.write_bytes(b"app")
    worker.write_bytes(b"worker")

    assert smoke._bundled_worker(app) == worker
