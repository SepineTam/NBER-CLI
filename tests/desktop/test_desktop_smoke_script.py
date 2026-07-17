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


def test_linux_smoke_installs_native_appimage_without_sidecar(tmp_path):
    smoke = _load_smoke_script()
    package = tmp_path / "NBER-CLI-Desktop-v0-8-1-Linux-x64.AppImage"
    # Simulate --appimage-extract output layout.
    (tmp_path / "squashfs-root" / "usr" / "bin").mkdir(parents=True)
    app = tmp_path / "squashfs-root" / "usr" / "bin" / "app"
    app.write_bytes(b"app")

    # The helper expects the package to exist, so create a dummy executable script.
    package.write_text("#!/bin/sh\n:\n", encoding="utf-8")
    package.chmod(package.stat().st_mode | 0o111)

    executable = smoke._install_linux_package(package, tmp_path)

    assert executable == app


def test_windows_smoke_does_not_treat_sidecar_or_uninstaller_as_app(tmp_path):
    smoke = _load_smoke_script()
    sidecar = tmp_path / "nber-sidecar.exe"
    uninstaller = tmp_path / "Uninstall NBER-CLI Desktop.exe"
    app = tmp_path / "NBER-CLI Desktop.exe"
    for path in (sidecar, uninstaller, app):
        path.write_bytes(b"exe")

    assert smoke._is_windows_app_executable(sidecar) is False
    assert smoke._is_windows_app_executable(uninstaller) is False
    assert smoke._is_windows_app_executable(app) is True


def test_smoke_seed_uses_native_desktop_settings(tmp_path):
    smoke = _load_smoke_script()

    smoke._seed_sample_environment(tmp_path)

    config = json.loads((tmp_path / ".nber-cli" / "config.json").read_text())
    assert config["desktop"]["feed_refresh_interval_minutes"] == 60


def test_native_runtime_ready_requires_rust_schema_and_database_path(tmp_path):
    smoke = _load_smoke_script()
    smoke._seed_sample_environment(tmp_path)
    assert smoke._native_runtime_ready(tmp_path) is False

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

    assert smoke._native_runtime_ready(tmp_path) is True
