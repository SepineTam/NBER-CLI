from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_release_checker():
    script = ROOT / "scripts" / "check-desktop-release.py"
    spec = importlib.util.spec_from_file_location("check_desktop_release", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_windows_release_check_requires_bundled_sidecar(tmp_path, monkeypatch):
    checker = _load_release_checker()
    monkeypatch.setattr(checker, "TARGET_DIR", tmp_path)
    release_dir = tmp_path / "release"
    bundle_dir = release_dir / "bundle" / "nsis"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "NBER-CLI Desktop_0.8.0_x64-setup.exe").write_bytes(b"installer")
    (release_dir / "app.exe").write_bytes(b"app")

    with pytest.raises(SystemExit, match="missing bundled Windows sidecar"):
        checker._check_windows(max_mb=80, require_signed=False)


def test_windows_release_check_accepts_sidecar_and_app_exe(tmp_path, monkeypatch):
    checker = _load_release_checker()
    monkeypatch.setattr(checker, "TARGET_DIR", tmp_path)
    release_dir = tmp_path / "release"
    bundle_dir = release_dir / "bundle" / "nsis"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "NBER-CLI Desktop_0.8.0_x64-setup.exe").write_bytes(b"installer")
    (release_dir / "app.exe").write_bytes(b"app")
    (release_dir / "nber-sidecar.exe").write_bytes(b"sidecar")

    checker._check_windows(max_mb=80, require_signed=False)


def test_windows_release_check_requires_signatures_for_installer_app_and_sidecar(
    tmp_path,
    monkeypatch,
):
    checker = _load_release_checker()
    monkeypatch.setattr(checker, "TARGET_DIR", tmp_path)
    release_dir = tmp_path / "release"
    bundle_dir = release_dir / "bundle" / "nsis"
    bundle_dir.mkdir(parents=True)
    installer = bundle_dir / "NBER-CLI Desktop_0.8.0_x64-setup.exe"
    app = release_dir / "app.exe"
    sidecar = release_dir / "nber-sidecar.exe"
    installer.write_bytes(b"installer")
    app.write_bytes(b"app")
    sidecar.write_bytes(b"sidecar")
    checked_paths: list[Path] = []

    def fake_signature_is_valid(path: Path) -> bool:
        checked_paths.append(path)
        return True

    monkeypatch.setattr(checker, "_windows_signature_is_valid", fake_signature_is_valid)

    checker._check_windows(max_mb=80, require_signed=True)

    assert checked_paths == [installer, app, sidecar]
