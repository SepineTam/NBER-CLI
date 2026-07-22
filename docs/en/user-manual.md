# User Manual

This manual describes the released behavior of NBER-CLI **0.10.0**. It treats Desktop as the normal researcher interface and CLI/MCP as AI-agent or automation interfaces. When this manual differs from a command's `--help`, the installed version's help output is authoritative.

## 1. Product and Audience

NBER-CLI helps users follow public NBER working-paper metadata, inspect abstracts, organize a local reading feed, produce citation text, and obtain PDFs through agent-facing tools.

| User | Recommended interface | Developer tools required |
| --- | --- | --- |
| Researcher | Desktop | No |
| AI agent with MCP | MCP server | `uvx` or an installed Python package |
| AI agent with shell access | CLI | `uvx` or an installed Python package |
| Application developer | Python API or optional HTTP API | Python 3.11+ and the relevant dependencies |

The project is independent from NBER. It does not provide subscriptions, credentials, or a way to bypass NBER access controls.

## 2. Operating Requirements

### Desktop

- A matching macOS arm64/x64, Windows x64, or Linux x64 package from the official GitHub Release.
- Network access to NBER for Feed synchronization and paper metadata preparation.
- Optional access to GitHub's Releases API for manual update checks.
- Permission to create files under the user's home directory, normally `~/.nber-cli/`.
- A window at least 920 × 620 px; the initial window is 1120 × 760 px.

Desktop includes its own worker runtime. Do not install Python solely to run the app.

### Agent interfaces

- Python 3.11 or newer when installing the package directly.
- `uvx`, `uv tool`, `pipx`, or `pip`.
- An MCP-capable client for MCP mode, or shell access for CLI mode.

## 3. Install and Start Desktop

1. Open the [latest official Release](https://github.com/sepinetam/nber-cli/releases/latest).
2. Choose the package that matches the operating system and CPU architecture.
3. Install it using the operating system's normal package flow.
4. If the operating system warns about an unidentified publisher, verify the source before overriding the warning. Follow the exact platform guidance in the [Desktop Guide](desktop.md#unsigned-release-notice).
5. Start **NBER-CLI Desktop**.

On first start, Desktop writes supported defaults to `~/.nber-cli/config.json` and validates an existing configured database. If the database does not exist, the first successful **同步最新论文 (Refresh)** creates it and its schema. Desktop does not start a local server.

## 4. Screen Layout

| Area | Purpose |
| --- | --- |
| Left navigation | Switch between the paper Feed and Settings; show local readiness. |
| Feed header | Show local paper count and last successful synchronization time. |
| Search and filters | Filter loaded records by text, read state, or visible tag. |
| Paper list | Show locally cached Feed rows and load additional local pages. |
| Detail pane | Show metadata, abstract, tags, read control, citation controls, and the NBER page action. |
| Settings | Change refresh interval and detail font size; inspect local paths; check for updates. |

## 5. First Synchronization

**Precondition:** Desktop is open and NBER is reachable.

1. Open the Feed view.
2. Select **同步最新论文 (Refresh)**.
3. Wait until the progress state ends.
4. Read the completion notice.

**Expected result:** Feed rows are stored in SQLite, new-row and detail-preparation counts are reported, and the list refreshes from local data. If `info.cache_enabled` is false, the prepared count remains zero and metadata prefetch is skipped.

**Local side effects:** `feed_items`, `feed_fetches`, `info_cache`, and Desktop raw-tag synchronization tables may be inserted or updated. No PDF is downloaded.

## 6. Daily Desktop Tasks

| Task | Action | Expected result | Persistent effect |
| --- | --- | --- | --- |
| Find a loaded paper | Type title, author, ID, or tag in search. | Matching loaded rows remain visible. | None. |
| Show unread papers | Select **未读 (Unread)**. | Loaded read rows are hidden. | None. |
| Filter by tag | Select a visible tag. | Loaded rows with that tag remain visible. | None. |
| Read details | Select a Feed row. | Cached metadata opens in the right pane. | Paper is marked read. |
| Change read state | Select the eye control. | Row and detail state update. | `read_status` is updated. |
| Add a tag | Enter a tag in the detail pane and select **添加 (Add)**. | Tag appears on the paper and Feed row. | `desktop_user_tags` is updated. |
| Edit a source tag | Edit a Topic/Program tag. | Original is hidden locally; edited text appears as a user tag. | Hidden-source and user-tag rows are updated. |
| Remove a tag | Select the remove control. | User tag disappears, or source tag is hidden locally. | Desktop tag tables are updated. |
| Copy a citation | Choose a style and select copy. | Citation text is placed on the clipboard. | None. |
| Open the source page | Select **NBER 页面 (NBER Page)**. | The system browser opens the public paper URL. | None. |
| Load more | Select **加载更多 (Load more)**. | The next local page is appended. | None. |

Desktop search is local and operates on rows already loaded into the list. Use CLI `search` or MCP `search_papers` when an AI agent should query NBER's remote search endpoint.

## 7. Reading Controls

- Drag the detail divider between 360 and 640 px.
- Double-click it to restore 420 px.
- When the divider has keyboard focus, use Left/Right, Shift+Left/Right, Home, or End.
- Select 14, 16, or 18 px from Settings for paper-detail text.
- Use `Command/Ctrl+F` or `Command/Ctrl+K` to focus Feed search.
- Use `Command/Ctrl+R` to synchronize and `Command/Ctrl+1` to return to the Feed.

The divider width is stored in WebView local storage. Other Desktop settings are stored in `config.json`.

## 8. Configure Automatic Refresh

1. Open **设置 (Settings)**.
2. Enter a positive integer number of minutes (`1`–`65535`).
3. Choose the paper-detail font size.
4. Select **保存设置 (Save Settings)**.

Automatic refresh runs only while Desktop is open, local initialization succeeded, the document is visible, and no refresh is already running. It is not a background operating-system service.

## 9. Use an AI Agent

### MCP

Configure the agent to run:

```bash
uvx nber-cli mcp-server
```

The agent receives three tools: `get_paper_info`, `search_papers`, and `download_paper`. In 0.10.0, MCP applies a lexical working-directory check to download paths; this is not a security sandbox. Run the server in an isolated working directory and use simple relative filenames. See [MCP Server](mcp.md) for parameters and return objects.

### CLI

Agents with shell access can use:

```bash
uvx nber-cli search "minimum wage" --format json
uvx nber-cli info w25000 --format json
uvx nber-cli download w34567
```

The CLI also manages Feed data, cache, configuration, database paths, and diagnostics. Use [CLI Reference](cli.md) for exact options. Human researchers do not need these commands for ordinary Desktop use.

## 10. Data, Backup, and Recovery

Default data locations are:

| Data | Default location |
| --- | --- |
| Shared configuration | `~/.nber-cli/config.json` |
| Shared SQLite database | `~/.nber-cli/nber.db` |
| CLI rotating diagnostic log | `~/.nber-cli/debug.log` |
| Desktop diagnostic directory | `~/.nber-cli/logs/` |
| Detail-pane width | WebView local storage |

For a file-level backup, close every Desktop, CLI, MCP, and HTTP process that uses the database. Copy `nber.db` and any `nber.db-wal` and `nber.db-shm` files together. For a live database, use SQLite's `.backup` command as documented in [Persistence](persistence.md#backup).

If `config.json` is malformed, Desktop stops rather than replacing it. Restore a known-good file or repair the JSON. If a database schema is newer than the app supports, install a newer Desktop version; do not force an older version to write it.

## 11. Update and Remove

Desktop does not update itself. In **设置 (Settings)**, select **检查更新 (Check for Updates)**. If a newer release exists, open the official Release, close Desktop, and install the matching package over the existing application.

To remove the software:

1. Close Desktop and stop CLI/MCP/HTTP processes.
2. Remove the application through the operating system.
3. Keep `~/.nber-cli/` if the local library may be reused.
4. Delete `~/.nber-cli/` separately only when the database, tags, settings, caches, and logs are no longer needed.

Deleting the data directory cannot be undone unless a backup exists.

## 12. Known Boundaries

- Desktop browses the synchronized Feed; it does not expose remote full-text NBER search.
- Desktop opens the NBER page but has no in-app PDF download button.
- Citations are generated from available metadata and must be reviewed before formal use.
- Desktop tags are local and do not modify NBER.
- Update checks are manual and installation is manual.
- Current public installers may be unsigned.
- Source pages, search endpoints, and PDFs can be unavailable, restricted, or changed by NBER.
- Non-stdio MCP transports and the optional HTTP API need explicit network-security review before exposure beyond the local machine.

## 13. Acceptance Checklist

After installation or upgrade, confirm:

- Desktop opens without starting a local server.
- Feed refresh completes or returns a readable network error without deleting prior rows.
- A paper opens from local data and can be marked read/unread.
- A local tag can be added, edited, and removed.
- At least one citation style copies text.
- Refresh interval and font size persist after restart.
- Manual update check either reports a version result or a readable GitHub connectivity error.

Developers should additionally run the repository checks in [Testing](testing.md) and [Development](development.md).
