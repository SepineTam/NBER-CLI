# NBER-CLI Desktop

NBER-CLI Desktop is the desktop shell for NBER-CLI V1. It uses Tauri v2, React, TypeScript, a local FastAPI sidecar, and the default SQLite database at `~/.nber-cli/nber.db`. Desktop 0.8.0 does not yet honor the CLI's custom `feed.db-path`; see the [Desktop user guide](../docs/en/desktop.md).

## Development

From the repository root:

```bash
uv sync --dev --extra server
cd desktop
npm install
npm run tauri dev
```

In development, the Tauri shell starts the Python sidecar through:

```bash
uv run nber-sidecar --port 31527
```

## Python API

```bash
uv run nber-sidecar --host 127.0.0.1 --port 31527
```

Useful endpoints:

- `GET /api/v1/health`
- `GET /api/v1/feed`
- `POST /api/v1/feed/refresh`
- `GET /api/v1/papers/{paper_id}`
- `POST /api/v1/papers/{paper_id}/mark-read`
- `GET /api/v1/settings`
- `PATCH /api/v1/settings`

See the [Local HTTP API reference](../docs/en/http-api.md) for query parameters, request bodies, response envelopes, error codes, and endpoint side effects.

## Build Sidecar

```bash
uv sync --extra server --group desktop-build
uv run python scripts/build-sidecar.py --clean
```

The script writes the platform-specific sidecar to `desktop/src-tauri/binaries/` using Tauri's expected target triple naming.

## Build App

```bash
cd desktop
npm run build
npm run tauri build
```

Code signing requires the Apple Developer ID and Windows code signing secrets listed in the Release section below.

## Verification

Run the repository gates before preparing a desktop build:

```bash
uv run ruff check .
uv run pytest tests
cd desktop
npm run lint
npm run test
npm run build
cd src-tauri
cargo check
```

After building a macOS package, verify size and install/start behavior from the DMG:

```bash
uv run python scripts/check-desktop-release.py --platform macos --max-mb 80
uv run python scripts/smoke-desktop-app.py --install-from-package --exercise-live-refresh
```

On Windows CI or a Windows machine, use the same release checker and smoke script with `--platform windows`.

## Release

GitHub Actions builds Desktop artifacts from the same `v*` tag used by the Python package release, or when the Desktop workflow is manually dispatched. Pushing a tag such as `v0.8.0` runs the full checks and creates one draft GitHub Release containing the macOS and Windows installers. Publishing that same Release triggers the PyPI workflow, so the CLI and Desktop ship under one version and one Release.

Desktop releases are unsigned by default. To require signed Windows artifacts plus signed and notarized macOS artifacts in the future, set the repository variable `DESKTOP_REQUIRE_SIGNING` to `true` and configure the signing secrets below.

Before tagging, keep these versions aligned:

- `pyproject.toml`
- `desktop/package.json` and `desktop/package-lock.json`
- `desktop/src-tauri/tauri.conf.json`, `Cargo.toml`, and `Cargo.lock`
- Claude and Codex plugin manifests

Required release signing inputs:

- macOS: `APPLE_CERTIFICATE`, `APPLE_CERTIFICATE_PASSWORD`, `KEYCHAIN_PASSWORD`, `APPLE_ID`, `APPLE_PASSWORD`, `APPLE_TEAM_ID`
- Windows: `WINDOWS_CERTIFICATE`, `WINDOWS_CERTIFICATE_PASSWORD`

Optional signing inputs:

- macOS: `APPLE_PROVIDER_SHORT_NAME`
- Windows: `WINDOWS_DIGEST_ALGORITHM`, `WINDOWS_TIMESTAMP_URL`
