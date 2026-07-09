from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TAURI_CONFIG = ROOT / "desktop" / "src-tauri" / "tauri.conf.json"


def main() -> None:
    config = json.loads(TAURI_CONFIG.read_text())
    bundle = _ensure_object(config, "bundle")

    macos = _ensure_object(bundle, "macOS")
    apple_signing_identity = os.environ.get("APPLE_SIGNING_IDENTITY")
    apple_provider_short_name = os.environ.get("APPLE_PROVIDER_SHORT_NAME")
    if apple_signing_identity:
        macos["signingIdentity"] = apple_signing_identity
    if apple_provider_short_name:
        macos["providerShortName"] = apple_provider_short_name
    if not macos:
        bundle.pop("macOS", None)

    windows_thumbprint = os.environ.get("WINDOWS_CERTIFICATE_THUMBPRINT")
    windows_digest = os.environ.get("WINDOWS_DIGEST_ALGORITHM") or "sha256"
    windows_timestamp_url = os.environ.get("WINDOWS_TIMESTAMP_URL") or "http://timestamp.sectigo.com"
    windows = _ensure_object(bundle, "windows")
    if windows_thumbprint:
        windows["certificateThumbprint"] = windows_thumbprint
        windows["digestAlgorithm"] = windows_digest
        windows["timestampUrl"] = windows_timestamp_url
    if not windows:
        bundle.pop("windows", None)

    TAURI_CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    print(f"updated {TAURI_CONFIG}")


def _ensure_object(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        value = {}
        parent[key] = value
    return value


if __name__ == "__main__":
    main()
