# Software Specification

This document records the functional and technical baseline of NBER-CLI **0.10.0**. It is intended for maintainers, reviewers, release evidence, and future software-registration document preparation. It describes only behavior traceable to this repository; applicant identity, ownership evidence, source-code deposits, screenshots, and jurisdiction-specific forms must be prepared separately.

## 1. Software Identity

| Item | Baseline |
| --- | --- |
| Software name | NBER-CLI |
| Desktop product name | NBER-CLI Desktop |
| Version | 0.10.0 |
| Package name | `nber-cli` |
| Desktop identifier | `com.sepinetam.nber-cli-desktop` |
| License | Apache-2.0 |
| Development status | Beta |
| Primary user interface | Desktop |
| AI and automation interfaces | CLI and MCP server |
| Additional integration interfaces | Python API and optional loopback HTTP API |
| Default local data root | `~/.nber-cli/` |

NBER is a third-party registered trademark. The project is independent and is not an NBER product, affiliate, or endorsed integration.

### Technology and environment profile

| Layer | Baseline technology or environment |
| --- | --- |
| Desktop UI | TypeScript 5.8, React 18, Zustand 5, Vite 6 |
| Desktop native shell | Rust, Tauri 2, SQLite through `rusqlite` |
| Shared application core | Python 3.11+, `aiohttp`, SQLModel/SQLAlchemy, `defusedxml` |
| Agent interface | Python MCP SDK / FastMCP |
| Optional local integration | FastAPI, Uvicorn, Alembic |
| Persistent formats | JSON configuration, SQLite database, PDF downloads, rotating text logs |
| Automated verification | Pytest, Vitest, TypeScript compiler, Cargo tests, strict MkDocs build |
| CI baseline | Python 3.11, Node.js 20, stable Rust toolchain, `uv`, npm |
| Release targets | macOS arm64/x64, Windows x64, Linux x64 |
| Special hardware | None required beyond a supported general-purpose computer and network connection |

Source-line totals, file counts, build-host versions, and package checksums are snapshot evidence rather than permanent product attributes. Calculate and archive them from the exact release tag used for a registration or audit; do not copy counts from a moving development branch.

## 2. Purpose and Scope

The software supports a local research loop around public NBER working-paper information:

1. Acquire Feed, search, metadata, and PDF responses from public NBER endpoints.
2. Parse the responses into structured paper models.
3. Store selected Feed, metadata, read-state, tag, and operation data locally.
4. Present a Desktop research workspace to human researchers.
5. Present structured MCP tools and scriptable CLI commands to AI agents.
6. Provide explicit Python and loopback HTTP integration surfaces.

### Out of scope

- Hosting or redistributing an NBER paper repository.
- Providing accounts, subscriptions, credentials, or access-control bypasses.
- Modifying NBER source records or writing Desktop tags back to NBER.
- Automatically installing Desktop updates.
- Providing a Desktop remote-search or in-app PDF-download workflow in 0.10.0.
- Guaranteeing completeness or continued availability of third-party pages and endpoints.

## 3. Actors and Interfaces

| Actor | Interface | Main intent |
| --- | --- | --- |
| Researcher | Desktop | Follow a local Feed, read abstracts, maintain reading state and tags, copy citations. |
| AI agent | MCP | Invoke structured search, lookup, and path-checked download tools. |
| AI agent / script | CLI | Run deterministic commands and consume text or JSON output. |
| Python developer | Python API | Reuse async fetch, parsing, download, cache, and database functions. |
| Local application | HTTP API | Use an explicit loopback JSON service for Feed, paper, read-state, and settings. |
| Maintainer | Repository tooling | Test, build, package, validate, and publish synchronized releases. |

## 4. Capability Matrix

`Yes` means the public interface exposes the capability in 0.10.0. `Internal` means code exists for shared operation but the interface does not present it as a user command or tool.

| Capability | Desktop | CLI | MCP | HTTP API | Python API |
| --- | --- | --- | --- | --- | --- |
| Browse synchronized Feed | Yes | No | No | Yes | No |
| Refresh NBER Feed | Yes | Yes | No | Yes | Yes |
| Clean Feed cache | No | Yes | No | No | Yes |
| Remote paper search | No | Yes | Yes | No | Yes |
| Retrieve paper metadata | Cached local view | Yes | Yes | Yes | Yes |
| Force metadata refresh | No | Yes | No | No | Yes |
| Download PDF | No | Yes | Yes | No | Yes |
| Read/unread state | Yes | No | No | Yes | Internal database package only |
| NBER-derived and local tags | Yes | No | No | No | No |
| Citation formatting | Yes | No | No | No | No |
| Config inspection/editing | Selected Desktop settings | Yes | No | Selected server settings | Yes |
| Database initialize/migrate | Initialize on first refresh | Yes | No | Automatic upgrade | Yes |
| Diagnostics / version repair | Manual update check | Yes | No | Health endpoint | No |

This matrix prevents an implementation on one surface from being advertised on another. New functionality must update the matrix, interface reference, tests, and changelog in the same release.

## 5. Functional Requirements

| ID | Requirement | Primary verification |
| --- | --- | --- |
| FR-01 | Desktop shall validate an existing shared schema-v3 SQLite database without starting a listening service; when no database exists, the first successful Feed refresh shall initialize it. | Desktop runtime, worker, and release smoke tests. |
| FR-02 | Desktop shall refresh the Feed through the bundled one-shot Python worker and exit the worker after the operation. | Worker and package tests. |
| FR-03 | Feed refresh shall store Feed rows and record the fetch. When `info.cache_enabled` is true, it shall also prepare paper metadata; when false, it shall skip metadata prefetch. The result shall report fetched/new/prepared/failed counts. | Python and Rust tests. |
| FR-04 | Desktop shall list paged local Feed rows and filter loaded rows by read state, text, and visible tag. | React component and page tests. |
| FR-05 | Opening a paper shall read local metadata and mark it read; manual read/unread changes shall persist. | Tauri database and frontend-store tests. |
| FR-06 | Desktop shall preserve raw NBER tags separately from user tags and locally hidden raw tags. | Rust database tests. |
| FR-07 | Desktop shall copy six supported citation formats from available local metadata. | Citation unit tests. |
| FR-08 | Desktop shall persist refresh interval and 14/16/18 px font size settings, and remember preview width locally. | Config, auto-refresh, and layout tests. |
| FR-09 | CLI shall expose download, info, search, db, feed, mcp-server, config, and doctor commands with documented exit/output behavior. | CLI tests and generated `--help`. |
| FR-10 | MCP shall expose `get_paper_info`, `search_papers`, and `download_paper`, normalize paper IDs, and apply the documented lexical path check to downloads. | MCP tests. |
| FR-11 | The optional HTTP API shall bind to loopback by default and expose handled responses under `/api/v1`. | Server tests. |
| FR-12 | Non-critical behavior-log or cache-write failures shall not unnecessarily prevent the primary fetch/search/download result. | Database and flow tests. |
| FR-13 | The software shall expose the current download-path check and its known `..`/symbolic-link limitation accurately, and reject writes to unsupported future database schemas. | Download and database tests plus documentation review. |
| FR-14 | English and Chinese public documentation shall describe the same released behavior and version. | Strict MkDocs build and release review. |

## 6. Core Workflows

### Desktop Feed flow

```text
User refresh
  -> Tauri command
  -> bundled one-shot worker
  -> Python Feed fetch
  -> metadata prefetch only when info cache is enabled
  -> shared SQLite database
  -> Rust raw-tag synchronization
  -> React reloads paged local rows
```

Startup and ordinary paper opening read local SQLite data. They do not start the worker for each paper. A refresh always requests RSS; it may also request paper details when info cache is enabled.

### Agent lookup flow

```text
Agent
  -> MCP tool or CLI command
  -> shared Python fetch/cache functions
  -> local SQLite cache and operation logs where applicable
  -> structured dictionary/JSON or human-readable text
```

### Download flow

```text
Validated paper ID and target
  -> lexical path check when enabled
  -> NBER PDF request with retry policy
  -> file write
  -> CLI behavior log where applicable
  -> success path or readable error
```

## 7. Data Specification

### Shared files

| File | Content |
| --- | --- |
| `~/.nber-cli/config.json` | Schema marker, database path, cache, download, and Desktop settings. |
| `~/.nber-cli/nber.db` | Shared schema-v3 SQLite data and Desktop extension tables. |
| `~/.nber-cli/debug.log` | Rotating Python/CLI warnings, errors, and optional debug records. |
| `~/.nber-cli/logs/` | Desktop diagnostic directory. |

### Shared schema-v3 tables

`feed_items`, `feed_fetches`, `read_status`, `info_cache`, `query_log`, `download_log`, and `info_log` are created and versioned by the Python database layer.

### Desktop extension tables

`desktop_raw_tags`, `desktop_user_tags`, `desktop_hidden_raw_tags`, and `desktop_raw_tag_sync_state` are created idempotently by Desktop. They do not increment `PRAGMA user_version`; this preserves compatibility with CLI schema v3 while keeping Desktop-only tag state separate.

The exact columns, writers, cleanup behavior, and backup rules are documented in [Persistence](persistence.md).

## 8. Configuration and State Rules

- Shared persistent configuration uses JSON under the user home directory.
- Desktop supports integer refresh intervals from 1 through 65535 minutes and exactly 14, 16, or 18 px detail text.
- Preview width is a device-local WebView preference, not part of shared `config.json`.
- On macOS and Linux, Desktop database paths must normalize inside the user home directory.
- Malformed Desktop JSON is a hard initialization error and is not silently overwritten.
- CLI configuration readers may fall back to documented defaults for missing or malformed supported fields; `config verify` reports schema type/range errors.
- SQLite `PRAGMA user_version` is currently 3. Newer versions are rejected by older code.

## 9. External Dependencies and Boundaries

| Boundary | Behavior |
| --- | --- |
| NBER web/search/RSS/PDF endpoints | Third-party source; network, structure, availability, and access policy can change. |
| GitHub Releases API | Desktop accesses it only after manual update check. |
| Local filesystem | Stores config, database, logs, and requested downloads. |
| Clipboard | Receives citation text after an explicit Desktop action. |
| System browser | Opens NBER or GitHub pages after an explicit action. |
| MCP HTTP transports | No built-in authentication; must remain local or be protected externally. |
| Optional HTTP API | Defaults to loopback; not used by Desktop. |

No project API key or user credential is required. Local research data is not sent to project-owned infrastructure by the application code.

## 10. Non-Functional Requirements

### Safety and privacy

- Enable the documented lexical path check by default for CLI and always for MCP, while treating operating-system isolation—not that check—as the security boundary for untrusted paths.
- Avoid listening network services in the default Desktop path.
- Preserve malformed configuration for manual recovery rather than overwriting it.
- Refuse writes to unsupported future schema versions.
- Keep source tags, user tags, and hiding preferences separate.

### Reliability

- Retry eligible network failures.
- Use SQLite transactions for multi-step updates where required.
- Keep existing local Feed data when a later network refresh fails.
- Treat selected logging and cache operations as soft failures.
- Validate packaged Desktop worker presence and reject legacy HTTP sidecars.

### Usability and accessibility

- Provide human-readable default CLI output plus JSON where automation needs it.
- Provide keyboard shortcuts and a keyboard-operable resize divider.
- Keep the main Desktop window resizable with a minimum supported size.
- Report visible, readable error and completion states.

### Portability

- Python package requires Python 3.11+.
- Desktop release workflow targets macOS arm64/x64, Windows x64, and Linux x64.
- Shared persisted data uses JSON and SQLite.

## 11. Source Traceability

| Module or evidence | Primary repository paths |
| --- | --- |
| Package identity and dependencies | `pyproject.toml` |
| CLI command model | `src/nber_cli/cli.py` |
| Public Python exports | `src/nber_cli/__init__.py` |
| Search and metadata parser | `src/nber_cli/fetch/fetcher.py` |
| Feed parser and synchronization | `src/nber_cli/fetch/feed.py` |
| PDF download engine | `src/nber_cli/fetch/download.py` |
| Shared models | `src/nber_cli/core/models.py` |
| Shared SQLite layer | `src/nber_cli/db/db.py`, `src/nber_cli/db/info_cache.py` |
| Configuration | `src/nber_cli/config/config_store.py`, `src/nber_cli/config/config.schema.json` |
| MCP tools | `src/nber_cli/mcp/mcp.py` |
| Optional HTTP API | `src/nber_server/main.py`, `src/nber_server/routers/` |
| Desktop worker entry | `src/nber_cli/desktop_worker.py` |
| Desktop React application | `desktop/src/App.tsx`, `desktop/src/pages/`, `desktop/src/components/`, `desktop/src/stores/` |
| Desktop native commands/config/data | `desktop/src-tauri/src/commands.rs`, `config.rs`, `database.rs`, `worker.rs` |
| Desktop package identity | `desktop/package.json`, `desktop/src-tauri/tauri.conf.json`, `desktop/src-tauri/Cargo.toml` |
| Automated tests | `tests/`, `desktop/src/**/*.test.*`, Rust `#[cfg(test)]` modules |
| CI and release evidence | `.github/workflows/`, `scripts/`, `release/`, `CHANGELOG.md` |
| Visual and interaction design | `DESIGN.md`, `DESKTOP_UX.md` |
| Public documentation navigation | `mkdocs.yml`, `docs/en/`, `docs/zh/` |

## 12. Verification Baseline

Before a release or formal documentation snapshot, run:

```bash
uv run ruff check .
uv run pytest
uv run mypy src
uv run --group docs mkdocs build --strict
cd desktop
npm run lint
npm run test
npm run build
cd src-tauri
cargo test --locked
```

Packaged applications additionally require the repository's Desktop artifact checks and smoke tests. The [Development Guide](development.md) records the full release checklist and platform-specific commands.

## 13. Registration-Evidence Maintenance

Create a frozen copy of this control record for the release used in an application. Do not fill snapshot fields from a moving branch:

| Control field | Value for this living document | Registration snapshot action |
| --- | --- | --- |
| Product baseline | NBER-CLI 0.10.0 | Record the exact released version and tag. |
| Document revision | Living repository documentation | Assign a dated, immutable revision identifier. |
| Source revision | Current working tree | Record the full commit hash from the frozen tag. |
| Verification date | Not fixed | Record the date, operator, operating system, and result bundle. |
| Build identity | Not fixed | Archive installer/package filenames and SHA-256 checksums. |
| Ownership/applicant record | Outside repository scope | Attach the authoritative jurisdiction-specific evidence. |

Use a function-to-evidence index so every claimed screen and behavior can be reproduced from the same source revision:

| Function group | Primary source | Automated evidence | Snapshot evidence to capture |
| --- | --- | --- | --- |
| Desktop Feed and details | `desktop/src/pages/FeedPage.tsx`, Tauri commands, Desktop worker | React, Rust, Feed, and cache tests | First refresh, Feed list, detail pane, completion notice. |
| Read state and tags | Desktop stores/components and Rust database layer | React and Rust database tests | Unread filter, tag create/edit/hide, persisted restart state. |
| Citation and settings | Desktop detail/settings components | Citation, layout, and config tests | Six citation choices, font size, refresh interval, local paths. |
| CLI | `src/nber_cli/cli.py` | CLI and release tests | `--help`, representative JSON/text output, failure exit. |
| MCP | `src/nber_cli/mcp/mcp.py` | MCP tests | Tool schema and one successful structured response per tool. |
| Persistence and recovery | Python/Rust database and config layers | Database, migration, config, and smoke tests | Database version, backup procedure, malformed-config behavior. |

Screenshots are supporting evidence, not a substitute for source and test traceability. Redact personal paths, local research history, credentials, and third-party paper content beyond what is necessary to identify the function.

For any future software-copyright or similar registration snapshot:

1. Freeze a released tag and record the exact version, commit, date, and supported platforms.
2. Keep package, Desktop, Rust, plugin, changelog, release-note, and documentation versions aligned.
3. Export source-code material from that tag, excluding dependencies, generated builds, local databases, secrets, and unrelated planning files.
4. Capture screenshots from installers built from the same tag; label each screenshot with the function it proves.
5. Preserve build logs, test results, release checksums, license text, contributor/ownership records, and third-party notices.
6. Use this specification and the [User Manual](user-manual.md) as technical baselines, then add the applicant and jurisdiction-specific declarations outside the code repository.
7. Re-run source-path, internal-link, bilingual-parity, and strict-site checks before submission.

This repository documentation can support technical consistency, but it is not legal advice and does not by itself establish ownership or satisfy a specific registration authority.
