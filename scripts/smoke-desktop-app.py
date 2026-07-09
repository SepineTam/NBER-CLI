from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORT = 31527
SAMPLE_PAPER_ID = "w12345"


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test the built desktop app.")
    parser.add_argument("--app-path", type=Path, default=None)
    parser.add_argument("--package-path", type=Path, default=None)
    parser.add_argument(
        "--install-from-package",
        action="store_true",
        help="Install the built DMG/NSIS/MSI package into a temporary directory before launch.",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--exercise-live-refresh",
        action="store_true",
        help="Call the real NBER RSS refresh endpoint after the deterministic smoke flow.",
    )
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

        _assert_port_free(args.port)
        _seed_sample_environment(temp_home, args.port)
        env = os.environ.copy()
        env["HOME"] = str(temp_home)
        env["USERPROFILE"] = str(temp_home)
        process = subprocess.Popen(
            [str(executable)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        payload = _wait_for_health(args.port, args.timeout)
        if payload is None:
            stdout, stderr = _process_output(process)
            raise SystemExit(
                "desktop app did not expose sidecar health endpoint\n"
                f"stdout:\n{stdout}\n"
                f"stderr:\n{stderr}"
            )
        print(payload)
        _assert_database_migrated(temp_home)
        _exercise_seeded_flow(args.port)
        _exercise_settings_flow(args.port, args.port)
        if args.exercise_live_refresh:
            _exercise_live_refresh(args.port)
    finally:
        if process is not None:
            _terminate(process)
        if mounted_dmg is not None:
            _detach_macos_dmg(mounted_dmg)
        shutil.rmtree(temp_home, ignore_errors=True)
        shutil.rmtree(temp_install, ignore_errors=True)


def _default_executable() -> Path:
    system = platform.system()
    if system == "Darwin":
        target_dir = ROOT / "desktop" / "src-tauri" / "target"
        candidates = sorted(
            target_dir.glob("**/release/bundle/macos/NBER-CLI Desktop.app/Contents/MacOS/app")
        )
        if candidates:
            return candidates[0]
        return (
            target_dir
            / "release"
            / "bundle"
            / "macos"
            / "NBER-CLI Desktop.app"
            / "Contents"
            / "MacOS"
            / "app"
        )
    if system == "Windows":
        candidates = sorted((ROOT / "desktop" / "src-tauri" / "target").glob("**/release/app.exe"))
        if candidates:
            return candidates[0]
        return ROOT / "desktop" / "src-tauri" / "target" / "release" / "app.exe"
    raise RuntimeError("NBER-CLI Desktop V1 only supports macOS and Windows smoke tests")


def _default_package() -> Path:
    target_dir = ROOT / "desktop" / "src-tauri" / "target"
    system = platform.system()
    if system == "Darwin":
        candidates = sorted(target_dir.glob("**/release/bundle/dmg/*.dmg"))
    elif system == "Windows":
        candidates = sorted(target_dir.glob("**/release/bundle/**/*.exe"))
        candidates.extend(sorted(target_dir.glob("**/release/bundle/**/*.msi")))
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
    raise RuntimeError("NBER-CLI Desktop V1 only supports macOS and Windows smoke tests")


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
        subprocess.run(
            [str(package), "/S", f"/D={install_dir}"],
            check=True,
            timeout=180,
        )
    elif suffix == ".msi":
        subprocess.run(
            [
                "msiexec",
                "/i",
                str(package),
                "/qn",
                f"TARGETDIR={install_dir}",
            ],
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
            _assert_windows_sidecar_installed(candidate)
            return candidate
    raise SystemExit(f"installed Windows app executable not found under {install_dir}")


def _is_windows_app_executable(path: Path) -> bool:
    name = path.name.lower()
    return path.exists() and "uninstall" not in name and name != "nber-sidecar.exe"


def _assert_windows_sidecar_installed(executable: Path) -> None:
    sidecar = executable.parent / "nber-sidecar.exe"
    if not sidecar.exists():
        raise SystemExit(f"installed Windows sidecar not found next to app executable: {sidecar}")


def _wait_for_health(port: int, timeout: float) -> str | None:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/api/v1/health"
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1) as response:
                return response.read().decode("utf-8")
        except (OSError, URLError):
            time.sleep(0.5)
    return None


def _assert_port_free(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        if probe.connect_ex(("127.0.0.1", port)) == 0:
            raise SystemExit(f"smoke port {port} is already in use; stop the existing NBER sidecar first")


def _exercise_seeded_flow(port: int) -> None:
    feed = _request_json("GET", port, "/api/v1/feed?limit=2")
    items = feed["data"]["items"]
    if len(items) != 2:
        raise SystemExit(f"seeded feed flow failed: expected 2 first-page items, got {len(items)}")
    if feed["data"]["total_count"] != 3:
        raise SystemExit(f"seeded feed flow failed: expected total_count=3, got {feed['data']['total_count']}")
    first_item = items[0]
    if first_item["paper_id"] != SAMPLE_PAPER_ID:
        raise SystemExit(f"seeded feed flow failed: expected {SAMPLE_PAPER_ID}, got {first_item['paper_id']}")
    if first_item["is_read"]:
        raise SystemExit("seeded feed flow failed: sample paper should start unread")

    next_page = _request_json("GET", port, "/api/v1/feed?limit=2&offset=2")
    next_items = next_page["data"]["items"]
    if len(next_items) != 1 or next_items[0]["paper_id"] != "w12343":
        raise SystemExit(f"seeded pagination flow failed: unexpected next page {next_items}")

    paper = _request_json("GET", port, f"/api/v1/papers/{SAMPLE_PAPER_ID}")
    paper_data = paper["data"]
    if paper_data["paper_id"] != SAMPLE_PAPER_ID:
        raise SystemExit("seeded detail flow failed: wrong paper id")
    if not paper_data["is_read"]:
        raise SystemExit("seeded detail flow failed: opening detail did not mark paper read")

    _assert_feed_read_state(port, True, "read state")

    mark_unread = _request_json(
        "POST",
        port,
        f"/api/v1/papers/{SAMPLE_PAPER_ID}/mark-read",
        body={"is_read": False},
    )
    if mark_unread["data"]["is_read"]:
        raise SystemExit("seeded read-status flow failed: mark unread did not return unread state")
    _assert_feed_read_state(port, False, "unread state")

    mark_read = _request_json(
        "POST",
        port,
        f"/api/v1/papers/{SAMPLE_PAPER_ID}/mark-read",
        body={"is_read": True},
    )
    if not mark_read["data"]["is_read"]:
        raise SystemExit("seeded read-status flow failed: mark read did not return read state")
    _assert_feed_read_state(port, True, "restored read state")
    print("seeded_flow=ok")


def _assert_feed_read_state(port: int, expected: bool, label: str) -> None:
    last_feed: dict | None = None
    for _ in range(10):
        last_feed = _request_json("GET", port, "/api/v1/feed?limit=10")
        items = last_feed["data"]["items"]
        if items and items[0]["paper_id"] == SAMPLE_PAPER_ID and items[0]["is_read"] is expected:
            return
        time.sleep(0.2)
    raise SystemExit(
        "seeded read-status flow failed: "
        f"feed did not reflect {label}; expected={expected} feed={last_feed}"
    )


def _exercise_settings_flow(port: int, expected_server_port: int) -> None:
    settings = _request_json("GET", port, "/api/v1/settings")["data"]
    if settings["server_port"] != expected_server_port:
        raise SystemExit(
            f"settings flow failed: expected port {expected_server_port}, got {settings}"
        )
    log_dir = Path(settings["log_dir"])
    for log_name in ("sidecar.stdout.log", "sidecar.stderr.log"):
        if not (log_dir / log_name).exists():
            raise SystemExit(f"settings flow failed: expected sidecar log file {log_dir / log_name}")

    updated = _request_json(
        "PATCH",
        port,
        "/api/v1/settings",
        body={"feed_refresh_interval_minutes": 45},
    )["data"]
    if updated["feed_refresh_interval_minutes"] != 45:
        raise SystemExit(f"settings flow failed: interval was not updated {updated}")
    print("settings_flow=ok")


def _exercise_live_refresh(port: int) -> None:
    refresh = _request_json("POST", port, "/api/v1/feed/refresh")
    data = refresh["data"]
    if data["fetched_count"] <= 0 or data["total_count"] <= 0:
        raise SystemExit(f"live refresh failed: unexpected counts {data}")

    feed = _request_json("GET", port, "/api/v1/feed?limit=10")
    items = feed["data"]["items"]
    if not items:
        raise SystemExit("live refresh failed: feed list is empty after refresh")
    print(f"live_refresh=ok fetched_count={data['fetched_count']} total_count={data['total_count']}")


def _request_json(method: str, port: int, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("code") != 0:
        raise SystemExit(f"{method} {path} failed: {payload}")
    return payload


def _assert_database_migrated(temp_home: Path) -> None:
    db_path = temp_home / ".nber-cli" / "nber.db"
    with sqlite3.connect(db_path) as connection:
        revision_row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    if revision_row is None or revision_row[0] != "20260708_0001":
        raise SystemExit(f"migration flow failed: unexpected alembic revision {revision_row}")
    if user_version != 3:
        raise SystemExit(f"migration flow failed: unexpected user_version {user_version}")
    print("migration_flow=ok")


def _seed_sample_environment(temp_home: Path, port: int) -> None:
    config_path = temp_home / ".nber-cli" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "desktop": {
                    "server_port": port,
                    "feed_refresh_interval_minutes": 60,
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _seed_sample_database(temp_home)


def _seed_sample_database(temp_home: Path) -> None:
    db_path = temp_home / ".nber-cli" / "nber.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    now = "2026-07-08T00:00:00+00:00"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS feed_items (
                paper_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors_json TEXT NOT NULL,
                abstract TEXT NOT NULL,
                url TEXT NOT NULL,
                source_url TEXT NOT NULL,
                guid TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS feed_fetches (
                id INTEGER PRIMARY KEY,
                source_url TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                total_count INTEGER NOT NULL,
                new_count INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS read_status (
                paper_id TEXT PRIMARY KEY,
                is_read BOOLEAN NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS info_cache (
                paper_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                authors_json TEXT NOT NULL,
                date TEXT NOT NULL,
                abstract TEXT NOT NULL,
                url TEXT,
                published_version TEXT,
                topic TEXT,
                programs TEXT,
                first_cached_at TEXT NOT NULL,
                last_fetched_at TEXT NOT NULL,
                fetch_count INTEGER DEFAULT 0
            );
            PRAGMA user_version = 3;
            """
        )
        authors_json = json.dumps(["Ada Lovelace", "Grace Hopper"])
        _insert_feed_item(connection, SAMPLE_PAPER_ID, "Desktop Smoke Test Paper", authors_json, now)
        _insert_feed_item(
            connection,
            "w12344",
            "Older Desktop Smoke Test Paper",
            authors_json,
            "2026-07-07T00:00:00+00:00",
        )
        _insert_feed_item(
            connection,
            "w12343",
            "Oldest Desktop Smoke Test Paper",
            authors_json,
            "2026-07-06T00:00:00+00:00",
        )
        connection.execute(
            """
            INSERT INTO info_cache (
                paper_id, title, authors_json, date, abstract, url,
                first_cached_at, last_fetched_at, fetch_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                SAMPLE_PAPER_ID,
                "Desktop Smoke Test Paper",
                authors_json,
                "2026-07-08",
                "Seeded detail abstract.",
                f"https://www.nber.org/papers/{SAMPLE_PAPER_ID}",
                now,
                now,
                0,
            ),
        )
        connection.commit()


def _insert_feed_item(
    connection: sqlite3.Connection,
    paper_id: str,
    title: str,
    authors_json: str,
    seen_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO feed_items (
            paper_id, title, authors_json, abstract, url, source_url, guid,
            first_seen_at, last_seen_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            paper_id,
            title,
            authors_json,
            "Seeded feed abstract.",
            f"https://www.nber.org/papers/{paper_id}",
            f"https://www.nber.org/papers/{paper_id}#rss",
            f"https://www.nber.org/papers/{paper_id}",
            seen_at,
            seen_at,
        ),
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
    stdout, stderr = process.communicate(timeout=5)
    return stdout, stderr


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
