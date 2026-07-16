from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "scripts" / "nber_sidecar_entry.py"
BUILD_DIR = ROOT / "build" / "pyinstaller"
DIST_DIR = ROOT / "build" / "sidecar-dist"
TAURI_BINARIES = ROOT / "desktop" / "src-tauri" / "binaries"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the NBER Python sidecar.")
    parser.add_argument("--target-triple", default=detect_target_triple())
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    if args.clean:
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        shutil.rmtree(DIST_DIR, ignore_errors=True)

    TAURI_BINARIES.mkdir(parents=True, exist_ok=True)
    data_separator = ";" if platform.system() == "Windows" else ":"
    migrations_data = (
        f"{ROOT / 'src' / 'nber_cli' / 'migrations'}"
        f"{data_separator}nber_cli/migrations"
    )
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "nber-sidecar",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--collect-submodules",
        "nber_cli",
        "--hidden-import",
        "uvicorn",
        "--hidden-import",
        "fastapi",
        "--add-data",
        migrations_data,
        str(ENTRY),
    ]
    subprocess.run(command, cwd=ROOT, check=True)

    source_name = "nber-sidecar.exe" if platform.system() == "Windows" else "nber-sidecar"
    source = DIST_DIR / source_name
    if not source.exists():
        raise FileNotFoundError(source)

    target_name = f"nber-sidecar-{args.target_triple}"
    if platform.system() == "Windows":
        target_name += ".exe"
    target = TAURI_BINARIES / target_name
    shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | 0o111)
    print(f"sidecar: {target}")
    print(f"size_mb: {target.stat().st_size / 1024 / 1024:.1f}")


def detect_target_triple() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Darwin":
        return "aarch64-apple-darwin" if machine in {"arm64", "aarch64"} else "x86_64-apple-darwin"
    if system == "Windows":
        return "x86_64-pc-windows-msvc"
    if system == "Linux":
        return "x86_64-unknown-linux-gnu"
    raise RuntimeError("NBER-CLI Desktop V1 only supports macOS, Windows and Linux sidecar builds")


if __name__ == "__main__":
    main()
