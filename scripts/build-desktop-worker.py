from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts" / "nber_desktop_worker_entry.py"
BUILD_DIR = ROOT / "build" / "desktop-worker-pyinstaller"
DIST_DIR = ROOT / "build" / "desktop-worker-dist"
TAURI_BINARIES = ROOT / "desktop" / "src-tauri" / "binaries"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the one-shot Desktop worker.")
    parser.add_argument("--target-triple", default=detect_target_triple())
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    if args.clean:
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        shutil.rmtree(DIST_DIR, ignore_errors=True)

    TAURI_BINARIES.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "nber-worker",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--specpath",
        str(BUILD_DIR),
        "--collect-submodules",
        "nber_cli",
        "--collect-data",
        "fake_useragent",
        str(ENTRY),
    ]
    subprocess.run(command, cwd=ROOT, check=True)

    source_name = "nber-worker.exe" if platform.system() == "Windows" else "nber-worker"
    source = DIST_DIR / source_name
    if not source.exists():
        raise FileNotFoundError(source)

    target_name = f"nber-worker-{args.target_triple}"
    if platform.system() == "Windows":
        target_name += ".exe"
    target = TAURI_BINARIES / target_name
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | 0o111)
    print(f"worker={target}")
    print(f"size_mb={target.stat().st_size / 1024 / 1024:.1f}")


def detect_target_triple() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Darwin":
        return "aarch64-apple-darwin" if machine in {"arm64", "aarch64"} else "x86_64-apple-darwin"
    if system == "Windows":
        return "x86_64-pc-windows-msvc"
    if system == "Linux":
        return "x86_64-unknown-linux-gnu"
    raise RuntimeError("NBER-CLI Desktop supports macOS, Windows and Linux workers")


if __name__ == "__main__":
    main()
