# Usage Policy

> If there is any conflict or inconsistency between this English version and the Chinese version, the Chinese version shall prevail.

## NBER and NBER-CLI

The National Bureau of Economic Research (NBER) is an independent, non-profit, nonpartisan economic research organization that publishes and distributes working papers, research metadata, newsletters, and related materials through [nber.org](https://www.nber.org).

**NBER** is a registered trademark of the National Bureau of Economic Research. NBER-CLI is an independent open-source project and is not affiliated with, endorsed by, sponsored by, or operated by NBER.

NBER-CLI is a command-line, MCP, local HTTP, and Desktop utility for searching NBER working papers, reading publicly exposed paper metadata, following the public RSS feed, and requesting PDF downloads from NBER-hosted URLs. It does not host NBER content, provide a substitute distribution service, or create any separate entitlement to access NBER materials. Every use of NBER-CLI remains subject to NBER's [Website Privacy Policy](https://www.nber.org/nber-website-privacy-policy), [working paper access and authorization rules](https://www.nber.org/nber-help-working-papers-general-information), [copyright and permission rules](https://www.nber.org/nber-help-working-papers-general-information), [subscription terms of use](https://www.nber.org/subscribe/information-libraries), and any other policy or access condition that NBER publishes or updates.

## Project Boundaries

- **No project-side storage**: NBER-CLI does not operate servers, caches, mirrors, CDNs, or other infrastructure for storing NBER papers or metadata. Requests go directly from the user's machine or agent runtime to NBER's website.
- **Default local persistence on the user machine**: NBER-CLI does keep a local SQLite database at `~/.nber-cli/nber.db` (or the path / `sqlite:///...` URL configured by `nber-cli db init` / `db migrate`) and a user config file at `~/.nber-cli/config.json`. The database is accessed through SQLModel/SQLAlchemy and remains on the user's machine unless the user copies or exports it. By default the following commands and tools write to that database without any extra user input:
  - `nber-cli search` records every query, including the keyword, the applied filters, and the result count, in the `query_log` table.
  - `nber-cli download` records every attempt, including the paper ID, success or failure status, the saved PDF path, and the error message when relevant, in the `download_log` table. Single download and batch download both write one row per attempt.
  - `nber-cli info` and the MCP `get_paper_info` tool each write a row to the `info_log` table for the looked-up paper.
  - `nber-cli info` and the MCP `get_paper_info` tool, when the `info_cache` is enabled, also write and refresh the `info_cache` table (see [Configuration](configuration.md)).
  - `nber-cli feed fetch` writes every fetched RSS item to `feed_items` and appends a fetch summary to `feed_fetches`.
  - Desktop starts a loopback-only sidecar, reads the local feed, automatically fetches the RSS feed when the database is empty, and refreshes it at the configured interval while the app is active.
  - Opening a paper in Desktop can request its metadata from NBER, update `info_cache`, and write its read state to `read_status`. Manual read/unread changes also update that table.
  - Desktop creates or updates `~/.nber-cli/config.json` and writes sidecar output to `~/.nber-cli/logs/sidecar.stdout.log` and `sidecar.stderr.log`. Desktop 0.8.0 currently starts with the default `~/.nber-cli/nber.db` path even when the CLI has a custom database path configured; see the [Desktop guide](desktop.md).
- **Cleaning up local data**: the `feed clean` and `info cache clear` commands delete cache rows after an interactive confirmation. The `query_log`, `download_log`, and `info_log` tables currently have no CLI cleanup command; the only ways to remove them today are `nber-cli db migrate` to a new database, manual `sqlite3` operations, or deleting `nber.db`. `feed clean --all` deletes `feed_items` only and never touches the accumulating `feed_fetches` history.
- **User-controlled PDF files**: When a user runs a download command, any PDF is saved only to the local path selected by that user. The project does not receive, retain, index, or redistribute that file.
- **No access circumvention**: NBER-CLI does not bypass subscriptions, paywalls, account requirements, IP-based authorization, first-week or recent-paper restrictions, access limits, or other controls imposed by NBER. If NBER returns a denial, error, redirect, or unavailable response, the tool treats that response as authoritative.
- **No traffic masking**: NBER-CLI uses standard Python HTTP libraries and ordinary request headers. It does not provide proxy pools, IP rotation, credential sharing, CAPTCHA bypass, request-signature manipulation, or other evasion mechanisms.
- **No redistribution rights**: Installing or using NBER-CLI does not grant any license to repost, mirror, sell, sublicense, train on, or otherwise reuse NBER content beyond what NBER, the relevant authors, and applicable law allow.

## Access, Copyright, and User Responsibility

NBER decides what is available through its website and under what conditions. Access may depend on publication date, subscription status, institutional eligibility, geographic eligibility, account authorization, or other rules set by NBER. Users are responsible for confirming that their use is permitted before downloading, copying, quoting, sharing, or otherwise using any NBER material.

NBER states that copyright in NBER Working Papers is held by the respective authors rather than by NBER. NBER-CLI does not own paper content and cannot grant permissions for uses beyond the access made available by NBER or the rights provided by law. Requests for permission beyond fair use or other applicable exceptions should be directed to the appropriate rights holder.

NBER-CLI is intended for lawful personal research, education, and reproducible research workflows. It is not intended for systematic bulk harvesting, public mirroring, reposting, resale, unauthorized commercial use, or any workflow designed to avoid NBER's access decisions.

## Operational Transparency

Search and metadata features use NBER web pages and website endpoints that are part of the normal operation of nber.org. PDF downloads request files from URLs served by NBER. The project does not claim that these interfaces are official APIs, stable APIs, or approved integration points.

Metadata, abstracts, links, availability, and files are provided by NBER and may be incomplete, delayed, revised, removed, rate limited, or otherwise changed without notice. NBER-CLI may stop working if NBER changes its website structure, access policy, endpoints, authorization checks, or file locations.

## Allocation of Risk

NBER-CLI is provided as an independent open-source tool on an "as is" and "as available" basis. The maintainers do not control NBER's website, content, copyright permissions, access decisions, uptime, or policies, and do not promise continued access to any NBER material.

By using NBER-CLI, users accept responsibility for their own requests, downloads, storage choices, and downstream use of any materials obtained from NBER. The maintainers are not responsible for access denials, account or network restrictions, copyright or licensing disputes, data loss, service interruptions, policy violations, or other consequences arising from a user's use of NBER-CLI.
