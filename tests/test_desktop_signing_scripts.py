from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_signing_validator():
    script = ROOT / "scripts" / "validate-desktop-signing.py"
    spec = importlib.util.spec_from_file_location("validate_desktop_signing", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_signing_preparer():
    script = ROOT / "scripts" / "prepare-tauri-signing.py"
    spec = importlib.util.spec_from_file_location("prepare_tauri_signing", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_macos_signing_validation_lists_missing_required_variables(monkeypatch):
    validator = _load_signing_validator()
    for name in validator.MACOS_REQUIRED:
        monkeypatch.delenv(name, raising=False)

    assert validator.missing_signing_variables("macos") == list(validator.MACOS_REQUIRED)


def test_windows_signing_validation_accepts_required_variables(monkeypatch):
    validator = _load_signing_validator()
    for name in validator.WINDOWS_REQUIRED:
        monkeypatch.setenv(name, "configured")

    assert validator.missing_signing_variables("windows") == []


def test_required_signing_validation_does_not_print_secret_values(monkeypatch, capsys):
    validator = _load_signing_validator()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate-desktop-signing.py",
            "--platform",
            "windows",
            "--require-signed",
        ],
    )
    monkeypatch.setenv("WINDOWS_CERTIFICATE", "secret-certificate-data")
    monkeypatch.delenv("WINDOWS_CERTIFICATE_PASSWORD", raising=False)

    with pytest.raises(SystemExit) as error:
        validator.main()

    assert error.value.code == 1
    output = capsys.readouterr().out
    assert "WINDOWS_CERTIFICATE_PASSWORD" in output
    assert "secret-certificate-data" not in output


def test_prepare_tauri_signing_writes_macos_and_windows_config(tmp_path, monkeypatch):
    preparer = _load_signing_preparer()
    config_path = tmp_path / "tauri.conf.json"
    config_path.write_text(json.dumps({"bundle": {"active": True}}))
    monkeypatch.setattr(preparer, "TAURI_CONFIG", config_path)
    monkeypatch.setenv("APPLE_SIGNING_IDENTITY", "Developer ID Application: Example")
    monkeypatch.setenv("APPLE_PROVIDER_SHORT_NAME", "TEAMSHORT")
    monkeypatch.setenv("WINDOWS_CERTIFICATE_THUMBPRINT", "ABC123")
    monkeypatch.delenv("WINDOWS_DIGEST_ALGORITHM", raising=False)
    monkeypatch.delenv("WINDOWS_TIMESTAMP_URL", raising=False)

    preparer.main()

    config = json.loads(config_path.read_text())
    assert config["bundle"]["macOS"] == {
        "signingIdentity": "Developer ID Application: Example",
        "providerShortName": "TEAMSHORT",
    }
    assert config["bundle"]["windows"] == {
        "certificateThumbprint": "ABC123",
        "digestAlgorithm": "sha256",
        "timestampUrl": "http://timestamp.sectigo.com",
    }


def test_prepare_tauri_signing_removes_empty_platform_config(tmp_path, monkeypatch):
    preparer = _load_signing_preparer()
    config_path = tmp_path / "tauri.conf.json"
    config_path.write_text(json.dumps({"bundle": {"active": True, "macOS": {}, "windows": {}}}))
    monkeypatch.setattr(preparer, "TAURI_CONFIG", config_path)
    for name in (
        "APPLE_SIGNING_IDENTITY",
        "APPLE_PROVIDER_SHORT_NAME",
        "WINDOWS_CERTIFICATE_THUMBPRINT",
        "WINDOWS_DIGEST_ALGORITHM",
        "WINDOWS_TIMESTAMP_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    preparer.main()

    config = json.loads(config_path.read_text())
    assert "macOS" not in config["bundle"]
    assert "windows" not in config["bundle"]
