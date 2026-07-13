# Desktop App

NBER-CLI Desktop provides a local research workspace for following new NBER working papers. It bundles the Python HTTP sidecar, stores its state on your machine, and does not require a separate Python installation.

## Supported Downloads

Download installers only from the project's [GitHub Releases](https://github.com/sepinetam/nber-cli/releases) page.

| Platform | Package label | Use when |
| --- | --- | --- |
| macOS Apple silicon | `macOS-arm64.dmg` | Mac with an M-series processor |
| macOS Intel | `macOS-x64.dmg` | Intel-based Mac |
| Windows | `Windows-x64.exe` | 64-bit Windows |

Linux installers are not currently produced. The Desktop and Python package use the same version number and are published in the same GitHub Release.

## Unsigned Release Notice

Current Desktop releases are not code-signed or notarized because the project does not yet have paid Apple and Windows certificates. This means macOS Gatekeeper or Windows SmartScreen may warn before the first launch. A warning does not prove that a file is safe.

Before overriding a platform warning:

1. Confirm that the installer came from the official `SepineTam/NBER-CLI` GitHub Release.
2. Confirm that its file name, version, platform, and CPU architecture match the release you selected.
3. Do not continue if the file came from a mirror, chat attachment, or other source you do not trust.

On macOS, after Gatekeeper blocks the first launch, open **System Settings → Privacy & Security** and use **Open Anyway** only after completing those checks. On Windows, expand **More info** in SmartScreen and choose **Run anyway** only when you trust the official release file.

## First Launch

Desktop starts a bundled local HTTP service bound to `127.0.0.1`. It then loads the local feed database. If the feed is empty, it automatically requests the current NBER RSS feed.

The following local files and directories may be created or updated:

| Path | Purpose |
| --- | --- |
| `~/.nber-cli/config.json` | Desktop port and automatic refresh interval |
| `~/.nber-cli/nber.db` | Feed items, metadata cache, logs, and read/unread state |
| `~/.nber-cli/logs/sidecar.stdout.log` | Local service standard output |
| `~/.nber-cli/logs/sidecar.stderr.log` | Local service errors and diagnostics |

The service stops when the Desktop application exits normally.

!!! warning "Current database-path limitation"
    Desktop 0.8.0 always starts its sidecar with `~/.nber-cli/nber.db`. It does not yet honor a custom `feed.db-path` created by `nber-cli db migrate`, and starting Desktop may write the default path back to `config.json`. Back up the config and database before opening Desktop if you use a custom or legacy database path.

## Main Workflows

- **Refresh the feed** to fetch the latest NBER working-paper RSS items.
- **Open a paper** to load its metadata and mark it as read.
- **Mark read or unread** to manage the local reading state stored in `read_status`.
- **Open on NBER** to view the paper on the NBER website.
- **Copy a citation** as BibTeX, APA, MLA, Harvard, Chicago, or GB/T 7714.
- **Load more** to page through locally cached feed entries.

Opening a paper can make a network request to NBER when its metadata is not already cached. The app does not download a PDF automatically.

## Settings

The Settings page exposes:

- **Local service port**: `31527` by default; valid range `1024`–`65535`. Restart Desktop after changing it.
- **Feed refresh interval**: `60` minutes by default. The app refreshes only while it is running, the local service is ready, and the window is visible.
- **Local paths**: shows the database and config locations and can open the sidecar log directory.

Configuration remains on the local machine. See [Configuration](configuration.md) and [Persistence Layer](persistence.md) for the complete storage model.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Local service is unavailable | Make sure the configured port is not used by another process, then restart Desktop. |
| Feed is empty | Check network access to `nber.org`, then use the refresh button. |
| Paper details fail | The paper may have been removed, restricted, or temporarily unavailable; inspect the sidecar logs. |
| Settings changed but the port did not | Port changes apply after restarting Desktop. |
| Expected custom database is missing | Read the database-path limitation above; Desktop currently uses the default database. |

Logs are under `~/.nber-cli/logs/`. They can contain error details and local paths, so review them before sharing.

## Upgrade, Backup, and Removal

Desktop does not currently update itself automatically. Download the newer installer from the official GitHub Release and install it over the existing application.

Before backing up or deleting local data, close Desktop and stop any separately running `nber-server` or MCP process. Back up `nber.db` together with `nber.db-wal` and `nber.db-shm` when those files exist. See [Persistence Layer](persistence.md#backup) for the live SQLite backup command.

Removing the application does not automatically delete `~/.nber-cli`. Delete that directory separately only when you no longer need its configuration, database, logs, or reading history.
