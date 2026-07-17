from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = ROOT / "desktop" / "src-tauri" / "target"


def main() -> None:
    parser = argparse.ArgumentParser(description="Check desktop release artifacts.")
    parser.add_argument("--max-mb", type=float, default=80.0)
    parser.add_argument("--require-signed", action="store_true")
    parser.add_argument("--require-notarized", action="store_true")
    parser.add_argument("--platform", choices=["macos", "windows", "linux"], default=_default_platform())
    args = parser.parse_args()

    if args.platform == "macos":
        _check_macos(args.max_mb, args.require_signed, args.require_notarized)
    elif args.platform == "linux":
        _check_linux(args.max_mb, args.require_signed)
    else:
        _check_windows(args.max_mb, args.require_signed)


def _check_macos(max_mb: float, require_signed: bool, require_notarized: bool) -> None:
    apps = _bundle_paths("macos", "*.app")
    dmgs = _bundle_paths("dmg", "*.dmg")
    if not apps:
        raise SystemExit("missing macOS .app bundle")
    if not dmgs:
        raise SystemExit("missing macOS .dmg bundle")

    for path in [*apps, *dmgs]:
        _check_size(path, max_mb)

    app = apps[0]
    sidecar = app / "Contents" / "MacOS" / "nber-sidecar"
    if sidecar.exists():
        raise SystemExit(f"unexpected bundled Python sidecar: {sidecar}")

    signed = _macos_signature_is_developer_id(app)
    print(f"macos_signed={signed}")
    if require_signed and not signed:
        raise SystemExit("macOS app is not signed with Developer ID")

    if require_notarized:
        for path in [app, *dmgs]:
            notarized = _macos_artifact_is_notarized(path)
            print(f"macos_notarized={notarized} path={path}")
            if not notarized:
                raise SystemExit(f"macOS artifact is not notarized: {path}")


def _check_linux(max_mb: float, require_signed: bool) -> None:
    installers = (
        _bundle_paths("appimage", "*.AppImage")
        + _bundle_paths("deb", "*.deb")
        + _bundle_paths("rpm", "*.rpm")
    )
    if not installers:
        raise SystemExit("missing Linux installer")

    app = _first_existing(root / "app" for root in _release_roots())
    if app is None:
        raise SystemExit("missing Linux app executable")

    sidecar = _first_existing(root / "nber-sidecar" for root in _release_roots())
    if sidecar is not None:
        raise SystemExit(f"unexpected bundled Linux sidecar: {sidecar}")

    for path in installers:
        _check_size(path, max_mb)

    if require_signed:
        print("linux_signed=skipped (code signing is not applicable on Linux)")


def _check_windows(max_mb: float, require_signed: bool) -> None:
    installers = _bundle_paths("", "*.exe") + _bundle_paths("", "*.msi")
    if not installers:
        raise SystemExit("missing Windows installer")

    app_exe = _first_existing(root / "app.exe" for root in _release_roots())
    if app_exe is None:
        raise SystemExit("missing Windows app executable")

    sidecar = _first_existing(root / "nber-sidecar.exe" for root in _release_roots())
    if sidecar is not None:
        raise SystemExit(f"unexpected bundled Windows sidecar: {sidecar}")

    for path in installers:
        _check_size(path, max_mb)
    if require_signed:
        for path in [*installers, app_exe]:
            signed = _windows_signature_is_valid(path)
            print(f"windows_signed={signed} path={path}")
            if not signed:
                raise SystemExit(f"Windows artifact is not signed: {path}")


def _check_size(path: Path, max_mb: float) -> None:
    size_mb = _path_size(path) / 1024 / 1024
    print(f"artifact={path} size_mb={size_mb:.1f}")
    if size_mb > max_mb:
        raise SystemExit(f"{path} is {size_mb:.1f}MB, above {max_mb:.1f}MB")


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


def _first_existing(paths) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _path_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(child.stat().st_size for child in path.rglob("*") if child.is_file())


def _macos_signature_is_developer_id(app: Path) -> bool:
    verify_result = subprocess.run(
        ["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(app)],
        check=False,
        capture_output=True,
        text=True,
    )
    if verify_result.returncode != 0:
        return False

    metadata_result = subprocess.run(
        ["codesign", "-dv", str(app)],
        check=False,
        capture_output=True,
        text=True,
    )
    output = metadata_result.stdout + metadata_result.stderr
    return (
        metadata_result.returncode == 0
        and "Signature=adhoc" not in output
        and "TeamIdentifier=not set" not in output
        and "Authority=Developer ID Application" in output
    )


def _macos_artifact_is_notarized(path: Path) -> bool:
    result = subprocess.run(
        ["xcrun", "stapler", "validate", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _windows_signature_is_valid(path: Path) -> bool:
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "$signature = Get-AuthenticodeSignature -FilePath "
        f"{str(path)!r}; "
        "Write-Host $signature.Status; "
        "if ($signature.Status -eq 'Valid') { exit 0 } else { exit 1 }",
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    return result.returncode == 0


def _default_platform() -> str:
    system = platform.system()
    if system == "Windows":
        return "windows"
    if system == "Linux":
        return "linux"
    return "macos"


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
