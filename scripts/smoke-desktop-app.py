from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test the bundled Desktop app.")
    parser.add_argument("--app-path", type=Path, default=None)
    parser.add_argument("--package-path", type=Path, default=None)
    parser.add_argument(
        "--install-from-package",
        action="store_true",
        help="Install the built package into a temporary directory before launch.",
    )
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    temp_home = Path(tempfile.mkdtemp(prefix="nber-cli-desktop-smoke-"))
    temp_install = Path(tempfile.mkdtemp(prefix="nber-cli-desktop-install-"))
    mounted_dmg: Path | None = None
    process: subprocess.Popen[str] | None = None
    try:
        if args.install_from_package:
            package = args.package_path or _default_package()
            executable, mounted_dmg = _install_package(package, temp_install)
        else:
            executable = args.app_path or _default_executable()
        if not executable.exists():
            raise SystemExit(f"desktop executable not found: {executable}")
        _assert_no_python_sidecar(executable)
        worker = _bundled_worker(executable)
        if worker is None:
            raise SystemExit(f"bundled one-shot worker not found beside {executable}")

        _seed_sample_environment(temp_home)
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        env["USERPROFILE"] = str(temp_home)
        env["NBER_DESKTOP_INIT_ONLY"] = "1"
        env["NBER_WORKER_PATH"] = str(temp_home / "missing-worker")
        env["PATH"] = ""
        process = subprocess.Popen(
            [str(executable)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if not _wait_for_desktop_runtime(process, temp_home, args.timeout):
            stdout, stderr = _process_output(process)
            raise SystemExit(
                "desktop app did not initialize its bundled data runtime\n"
                f"stdout:\n{stdout}\n"
                f"stderr:\n{stderr}"
            )
        print("desktop_runtime=ok")
        print(f"bundled_worker={worker}")
        print("python_sidecar=absent")
    finally:
        if process is not None:
            _terminate(process)
        if mounted_dmg is not None:
            _detach_macos_dmg(mounted_dmg)
        shutil.rmtree(temp_home, ignore_errors=True)
        shutil.rmtree(temp_install, ignore_errors=True)


def _default_executable() -> Path:
    target_dir = ROOT / "desktop" / "src-tauri" / "target"
    system = platform.system()
    if system == "Darwin":
        candidates = sorted(
            target_dir.glob("**/release/bundle/macos/NBER-CLI Desktop.app/Contents/MacOS/app")
        )
        return candidates[0] if candidates else target_dir / "release" / "app"
    if system == "Windows":
        candidates = sorted(target_dir.glob("**/release/app.exe"))
        return candidates[0] if candidates else target_dir / "release" / "app.exe"
    if system == "Linux":
        candidates = sorted(target_dir.glob("**/release/app"))
        return candidates[0] if candidates else target_dir / "release" / "app"
    raise RuntimeError("NBER-CLI Desktop supports macOS, Windows and Linux smoke tests")


def _default_package() -> Path:
    target_dir = ROOT / "desktop" / "src-tauri" / "target"
    system = platform.system()
    if system == "Darwin":
        candidates = sorted(target_dir.glob("**/release/bundle/dmg/*.dmg"))
    elif system == "Windows":
        candidates = sorted(target_dir.glob("**/release/bundle/**/*.exe"))
        candidates.extend(sorted(target_dir.glob("**/release/bundle/**/*.msi")))
    elif system == "Linux":
        candidates = sorted(target_dir.glob("**/release/bundle/**/*.AppImage"))
        candidates.extend(sorted(target_dir.glob("**/release/bundle/**/*.deb")))
    else:
        candidates = []
    if not candidates:
        raise SystemExit(f"desktop installer package not found under {target_dir}")
    return candidates[0]


def _install_package(package: Path, install_dir: Path) -> tuple[Path, Path | None]:
    if not package.exists():
        raise SystemExit(f"desktop installer package not found: {package}")
    system = platform.system()
    if system == "Darwin":
        executable, mounted_dmg = _install_macos_package(package, install_dir)
        print(f"installed_package={package}")
        return executable, mounted_dmg
    if system == "Windows":
        executable = _install_windows_package(package, install_dir)
        print(f"installed_package={package}")
        return executable, None
    if system == "Linux":
        executable = _install_linux_package(package, install_dir)
        print(f"installed_package={package}")
        return executable, None
    raise RuntimeError("NBER-CLI Desktop supports macOS, Windows and Linux smoke tests")


def _install_macos_package(package: Path, install_dir: Path) -> tuple[Path, Path | None]:
    mounted_dmg: Path | None = None
    source_app = package
    if package.suffix.lower() == ".dmg":
        mounted_dmg = install_dir / "dmg"
        mounted_dmg.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "hdiutil",
                "attach",
                str(package),
                "-nobrowse",
                "-readonly",
                "-mountpoint",
                str(mounted_dmg),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        apps = sorted(mounted_dmg.glob("*.app"))
        if not apps:
            raise SystemExit(f"mounted DMG does not contain an app bundle: {package}")
        source_app = apps[0]
    if source_app.suffix.lower() != ".app":
        raise SystemExit(f"macOS package is not a DMG or app bundle: {package}")
    installed_app = install_dir / source_app.name
    shutil.copytree(source_app, installed_app, symlinks=True)
    return installed_app / "Contents" / "MacOS" / "app", mounted_dmg


def _detach_macos_dmg(mountpoint: Path) -> None:
    subprocess.run(
        ["hdiutil", "detach", str(mountpoint), "-quiet"],
        check=False,
        capture_output=True,
        text=True,
    )


def _install_windows_package(package: Path, install_dir: Path) -> Path:
    suffix = package.suffix.lower()
    if suffix == ".exe":
        subprocess.run([str(package), "/S", f"/D={install_dir}"], check=True, timeout=180)
    elif suffix == ".msi":
        subprocess.run(
            ["msiexec", "/i", str(package), "/qn", f"TARGETDIR={install_dir}"],
            check=True,
            timeout=180,
        )
    else:
        raise SystemExit(f"Windows package is not an EXE or MSI installer: {package}")
    candidates = [
        install_dir / "NBER-CLI Desktop.exe",
        install_dir / "app.exe",
        *sorted(install_dir.glob("**/*.exe")),
    ]
    for candidate in candidates:
        if _is_windows_app_executable(candidate):
            return candidate
    raise SystemExit(f"installed Windows app executable not found under {install_dir}")


def _install_linux_package(package: Path, install_dir: Path) -> Path:
    suffix = package.suffix.lower()
    if suffix == ".appimage":
        subprocess.run(
            [str(package), "--appimage-extract"],
            cwd=install_dir,
            check=True,
            timeout=180,
        )
        app_dir = install_dir / "squashfs-root" / "usr" / "bin"
    elif suffix == ".deb":
        subprocess.run(
            ["dpkg-deb", "-x", str(package), str(install_dir)],
            check=True,
            timeout=180,
        )
        app_dir = install_dir / "usr" / "bin"
    else:
        raise SystemExit(f"Linux package is not an AppImage or DEB: {package}")
    app = app_dir / "app"
    if not app.exists():
        candidates = sorted(install_dir.glob("**/app"))
        if not candidates:
            raise SystemExit(f"installed Linux app executable not found under {install_dir}")
        app = candidates[0]
    app.chmod(app.stat().st_mode | 0o111)
    return app


def _is_windows_app_executable(path: Path) -> bool:
    name = path.name.lower()
    return (
        path.exists()
        and "uninstall" not in name
        and name not in {"nber-sidecar.exe", "nber-worker.exe"}
    )


def _assert_no_python_sidecar(executable: Path) -> None:
    candidates = [
        executable.parent / "nber-sidecar",
        executable.parent / "nber-sidecar.exe",
    ]
    existing = [path for path in candidates if path.exists()]
    if existing:
        raise SystemExit(f"unexpected bundled Python sidecar: {existing[0]}")


def _bundled_worker(executable: Path) -> Path | None:
    name = "nber-worker.exe" if platform.system() == "Windows" else "nber-worker"
    candidates = [
        executable.parent / name,
        executable.parent / "../Resources" / name,
    ]
    return next((path.resolve() for path in candidates if path.exists()), None)


def _wait_for_desktop_runtime(
    process: subprocess.Popen[str],
    temp_home: Path,
    timeout: float,
) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _desktop_runtime_ready(temp_home):
            return True
        if process.poll() is not None:
            return False
        time.sleep(0.25)
    return False


def _desktop_runtime_ready(temp_home: Path) -> bool:
    config_path = temp_home / ".nber-cli" / "config.json"
    db_path = temp_home / ".nber-cli" / "nber.db"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        configured_db = Path(config["feed"]["db-path"])
        schema_version = config["schema_version"]
    except (OSError, KeyError, json.JSONDecodeError):
        return False
    if configured_db != db_path or schema_version != 3:
        return False
    if not db_path.exists():
        return True
    try:
        with sqlite3.connect(db_path, timeout=1) as connection:
            user_version = connection.execute("PRAGMA user_version").fetchone()[0]
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
    except sqlite3.DatabaseError:
        return False
    required_tables = {"feed_items", "feed_fetches", "read_status", "info_cache"}
    return user_version == 3 and required_tables <= tables


def _seed_sample_environment(temp_home: Path) -> None:
    config_path = temp_home / ".nber-cli" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {"desktop": {"feed_refresh_interval_minutes": 60}},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _terminate(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _process_output(process: subprocess.Popen[str]) -> tuple[str, str]:
    if process.poll() is None:
        return "", ""
    return process.communicate(timeout=5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
