# NBER-CLI Desktop

NBER-CLI Desktop is a Tauri v2 and React research workspace. Since Desktop 0.9.0, its Rust core talks directly to the shared SQLite database and NBER endpoints. The application does not start, bundle, or require a Python sidecar.

Desktop and the Python CLI share the configured database, including `feed_items`, `info_cache`, and `read_status`. A custom `feed.db-path` created by `nber-cli db migrate` is honored when it points inside the user's home directory.

## Development

From the repository root:

```bash
cd desktop
npm install
npm run tauri dev
```

The React frontend calls these native Tauri commands:

- `get_config`
- `get_feed`
- `refresh_feed`
- `get_paper`
- `set_paper_read_status`
- `get_settings`
- `save_settings`

The optional Python HTTP API remains available for other local integrations, but Desktop does not use it.

## Build App

```bash
cd desktop
npm run build
npm run tauri build
```

No Python runtime or sidecar build step is required. Code signing remains optional because the project currently ships unsigned packages.

## Verification

Run the repository gates before preparing a Desktop build:

```bash
uv run ruff check .
uv run pytest
cd desktop
npm run lint
npm run test
npm run build
cd src-tauri
cargo test --locked
```

After building a package, verify its contents and native startup flow:

```bash
uv run python scripts/check-desktop-release.py --platform macos --max-mb 80
uv run python scripts/smoke-desktop-app.py --install-from-package
```

Use the corresponding `windows` or `linux` platform argument on those systems. The package check fails if a Python sidecar is present.

## Release

GitHub Actions builds macOS arm64/x64, Windows x64, and Linux x64 artifacts from a `v*` tag. The same tag is used for the Python package and Desktop app. Pushing `v0.9.0` creates or updates a draft GitHub Release; publish it after all platform artifacts have uploaded successfully.

Before tagging, keep these versions aligned:

- `pyproject.toml`
- `desktop/package.json` and `desktop/package-lock.json`
- `desktop/src-tauri/tauri.conf.json`, `Cargo.toml`, and `Cargo.lock`
- Claude and Codex plugin manifests

Signing is not required. If paid certificates are added later, set `DESKTOP_REQUIRE_SIGNING=true` and configure the signing secrets documented in the release workflow.
