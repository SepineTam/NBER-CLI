from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_smoke_script():
    script = ROOT / "scripts" / "smoke-desktop-app.py"
    spec = importlib.util.spec_from_file_location("smoke_desktop_app", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_windows_smoke_requires_sidecar_next_to_installed_app(tmp_path):
    smoke = _load_smoke_script()
    app = tmp_path / "NBER-CLI Desktop.exe"
    app.write_bytes(b"app")

    with pytest.raises(SystemExit, match="installed Windows sidecar not found"):
        smoke._assert_windows_sidecar_installed(app)


def test_windows_smoke_accepts_sidecar_next_to_installed_app(tmp_path):
    smoke = _load_smoke_script()
    app = tmp_path / "NBER-CLI Desktop.exe"
    sidecar = tmp_path / "nber-sidecar.exe"
    app.write_bytes(b"app")
    sidecar.write_bytes(b"sidecar")

    smoke._assert_windows_sidecar_installed(app)


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


def test_smoke_seed_writes_requested_desktop_port(tmp_path):
    smoke = _load_smoke_script()

    smoke._seed_sample_environment(tmp_path, 31528)

    config = json.loads((tmp_path / ".nber-cli" / "config.json").read_text())
    assert config["desktop"]["server_port"] == 31528
    assert config["desktop"]["feed_refresh_interval_minutes"] == 60
