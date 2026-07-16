from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TAURI_CONFIG = ROOT / "desktop" / "src-tauri" / "tauri.conf.json"
TARGET_DIR = ROOT / "desktop" / "src-tauri" / "target"

PLATFORM_LABELS = {
    "macos": "macOS",
    "windows": "Windows",
    "linux": "Linux",
}
ARCH_LABELS = {
    "aarch64-apple-darwin": "arm64",
    "x86_64-apple-darwin": "x64",
    "x86_64-pc-windows-msvc": "x64",
    "x86_64-unknown-linux-gnu": "x64",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize desktop release artifact names.")
    parser.add_argument("--platform", choices=sorted(PLATFORM_LABELS), required=True)
    parser.add_argument("--target-triple", choices=sorted(ARCH_LABELS), required=True)
    args = parser.parse_args()

    base_name = build_base_name(args.platform, args.target_triple)
    if args.platform == "macos":
        renamed = rename_macos_artifacts(base_name)
    elif args.platform == "linux":
        renamed = rename_linux_artifacts(base_name)
    else:
        renamed = rename_windows_artifacts(base_name)

    if not renamed:
        raise SystemExit(f"no {args.platform} artifacts found to rename")

    for path in renamed:
        print(f"artifact={path}")


def build_base_name(platform_name: str, target_triple: str) -> str:
    version = read_version().replace(".", "-")
    platform_label = PLATFORM_LABELS[platform_name]
    arch_label = ARCH_LABELS[target_triple]
    return f"NBER-CLI-Desktop-v{version}-{platform_label}-{arch_label}"


def read_version() -> str:
    with TAURI_CONFIG.open(encoding="utf-8") as handle:
        config = json.load(handle)
    version = config.get("version")
    if not isinstance(version, str) or not version:
        raise SystemExit(f"missing version in {TAURI_CONFIG}")
    return version


def rename_macos_artifacts(base_name: str) -> list[Path]:
    renamed: list[Path] = []
    for dmg in _bundle_paths("dmg", "*.dmg"):
        renamed.append(_rename(dmg, f"{base_name}.dmg"))
    return renamed


def rename_linux_artifacts(base_name: str) -> list[Path]:
    renamed: list[Path] = []
    for pattern, suffix in (
        ("appimage", "*.AppImage"),
        ("deb", "*.deb"),
        ("rpm", "*.rpm"),
    ):
        for path in _bundle_paths(pattern, suffix):
            if "uninstall" in path.name.lower():
                continue
            renamed.append(_rename(path, f"{base_name}{path.suffix}"))
    return renamed


def rename_windows_artifacts(base_name: str) -> list[Path]:
    renamed: list[Path] = []
    installers = [
        path
        for path in _bundle_paths("", "*.exe")
        if "uninstall" not in path.name.lower()
    ]
    installers.extend(_bundle_paths("", "*.msi"))
    for installer in installers:
        renamed.append(_rename(installer, f"{base_name}{installer.suffix.lower()}"))
    return renamed


def _bundle_paths(bundle_type: str, pattern: str) -> list[Path]:
    roots = [root / "bundle" for root in _release_roots()]
    paths: list[Path] = []
    for root in roots:
        search_root = root / bundle_type if bundle_type else root
        if search_root.exists():
            paths.extend(search_root.glob(f"**/{pattern}"))
    return sorted(set(paths))


def _release_roots() -> list[Path]:
    return [TARGET_DIR / "release", *TARGET_DIR.glob("*/release")]


def _rename(source: Path, target_name: str) -> Path:
    target = source.with_name(target_name)
    if source == target:
        return source
    if target.exists():
        target.unlink()
    source.rename(target)
    return target


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
