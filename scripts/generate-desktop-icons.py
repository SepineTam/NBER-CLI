from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESKTOP_DIR = ROOT / "desktop"
SOURCE_ICON = DESKTOP_DIR / "assets" / "brand" / "nber-cli-desktop-logo.png"
TAURI_ICONS_DIR = DESKTOP_DIR / "src-tauri" / "icons"
PUBLIC_FAVICON = DESKTOP_DIR / "public" / "favicon.png"
UNUSED_TAURI_ICON_PATHS = [
    "64x64.png",
    "android",
    "ios",
    "mipmap-hdpi",
    "mipmap-mdpi",
    "mipmap-xhdpi",
    "mipmap-xxhdpi",
    "mipmap-xxxhdpi",
]


def main() -> None:
    if not SOURCE_ICON.exists():
        raise FileNotFoundError(SOURCE_ICON)

    TAURI_ICONS_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_FAVICON.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "npm",
            "run",
            "tauri",
            "--",
            "icon",
            str(SOURCE_ICON.relative_to(DESKTOP_DIR)),
            "--output",
            str(TAURI_ICONS_DIR.relative_to(DESKTOP_DIR)),
        ],
        cwd=DESKTOP_DIR,
        check=True,
    )
    clean_unused_icons()
    shutil.copy2(TAURI_ICONS_DIR / "32x32.png", PUBLIC_FAVICON)

    print(f"source_icon={SOURCE_ICON}")
    print(f"tauri_icons={TAURI_ICONS_DIR}")
    print(f"public_favicon={PUBLIC_FAVICON}")


def clean_unused_icons() -> None:
    for path_name in UNUSED_TAURI_ICON_PATHS:
        path = TAURI_ICONS_DIR / path_name
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


if __name__ == "__main__":
    main()
