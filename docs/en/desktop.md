# Desktop App

NBER-CLI Desktop is a local research workspace for following new NBER working papers. Desktop 0.9.1 bundles a one-shot worker built from the same Python implementation as the CLI. Users do not install Python or uv, and Desktop does not start a local web server or long-running sidecar.

## Supported Downloads

Download installers only from the project's [GitHub Releases](https://github.com/sepinetam/nber-cli/releases) page.

| Platform | Package label | Use when |
| --- | --- | --- |
| macOS Apple silicon | `macOS-arm64.dmg` | Mac with an M-series processor |
| macOS Intel | `macOS-x64.dmg` | Intel-based Mac |
| Windows | `Windows-x64.exe` | 64-bit Windows |
| Linux | `Linux-x64.AppImage` or `.deb` | 64-bit Linux desktop |

Desktop and the Python package use the same version number and GitHub Release.

## Unsigned Release Notice

Current Desktop releases are not code-signed or notarized because the project does not have paid Apple and Windows certificates. macOS Gatekeeper or Windows SmartScreen may therefore warn on first launch.

Before overriding a warning, confirm that the file came from the official `SepineTam/NBER-CLI` GitHub Release and that its version, platform, and CPU architecture match your computer. Do not continue with files from mirrors or chat attachments.

On macOS, use **System Settings → Privacy & Security → Open Anyway** only after those checks. On Windows, use **More info → Run anyway** only for the official download you verified.

## First Launch and Local Data

Desktop opens the configured local database. On first launch, the bundled worker initializes the same database schema used by the CLI.

| Path | Purpose |
| --- | --- |
| `~/.nber-cli/config.json` | Database location, cache settings, and automatic refresh interval |
| `~/.nber-cli/nber.db` | Feed items, metadata cache, history, and read/unread state |
| `~/.nber-cli/logs/` | Local diagnostic directory; no long-running sidecar logs are created |

Desktop honors `feed.db-path` from the shared CLI configuration, including a path set by `nber-cli db migrate`. On macOS and Linux, the path must stay inside the user's home directory.

If `config.json` is malformed, Desktop stops with an error instead of replacing the file. Repair or restore the file, then reopen the app.

## Main Workflows

- **Refresh the feed** starts the bundled worker for one operation, calls the existing Python `fetch_feed` implementation, updates the database, and exits.
- **Open a paper** uses the existing Python metadata/cache implementation in the same one-shot worker, then Rust marks the paper read.
- **Mark read or unread** updates the shared `read_status` table directly.
- **Open on NBER** opens the public paper page.
- **Copy a citation** supports BibTeX, APA, MLA, Harvard, Chicago, and GB/T 7714.
- **Load more** pages through locally cached feed items.

## Settings

The Settings page exposes the automatic feed refresh interval and local config/database/log paths. There is no service-port setting because Desktop does not run a local HTTP process. The optional `nber-server` command keeps its own server settings for users who explicitly run that integration.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Feed refresh fails | Check access to `nber.org`, then retry. Existing local data remains available. |
| Paper details fail | The paper may be removed, restricted, or temporarily unavailable. The feed summary remains local. |
| Expected custom database is missing | Check `feed.db-path` in `~/.nber-cli/config.json`; it must point inside the home directory on macOS/Linux. |
| Database is reported as newer | Upgrade Desktop; an older app refuses to write a database with a newer schema. |

Desktop does not update itself automatically. Download a newer installer from the official GitHub Release and install it over the current version.

Before backing up or deleting local data, close Desktop and stop any separately running CLI, MCP, or HTTP process. Back up `nber.db` together with `nber.db-wal` and `nber.db-shm` if present. See [Persistence Layer](persistence.md#backup) for an online backup command.
