---
name: NBER-CLI
description: "Use this skill when the user needs to search NBER working papers, inspect NBER paper metadata, download NBER paper PDFs, run NBER-CLI commands, or configure NBER-CLI as an MCP server."
---

# NBER-CLI

## When to Use

Use this skill when the user wants to use NBER-CLI for NBER working papers, including:

- Searching NBER working papers by keyword, paper ID, author, abstract, or date range.
- Inspecting metadata or abstracts for a known NBER paper ID.
- Downloading one or more NBER PDF files to a chosen filesystem path.
- Getting machine-readable JSON output for agent workflows.
- Configuring NBER-CLI as an MCP server.
- Understanding common access errors such as 403, 404, timeout, access denied, or download limits.

## Assumptions

- The user may not have this repository checked out.
- Do not assume `nber-cli` is already installed.
- Prefer `uvx nber-cli ...` for one-off usage because it can run the published package without requiring a checked-out project or preinstalled command.
- If the user already installed the command, `nber-cli ...` is also fine.
- NBER-CLI does not grant access rights beyond what NBER allows for the user's current IP, institution, account, or session.

## CLI Usage

Check the command:

```bash
uvx nber-cli --help
uvx nber-cli --version
```

Search working papers:

```bash
uvx nber-cli search "labor economics"
uvx nber-cli search "minimum wage" --start-date 2024-01-01 --end-date 2024-12-31
uvx nber-cli search "ChatGPT" --format json
```

Show paper metadata:

```bash
uvx nber-cli info w25000
uvx nber-cli info w25000 --all
uvx nber-cli info w25000 --format json
```

Download papers:

```bash
uvx nber-cli download w34567
uvx nber-cli download w34567 --save-base ~/papers/nber
uvx nber-cli download w34567 --file ~/papers/nber/w34567.pdf
uvx nber-cli download --batch w34567 w25000 w32000 --save-base ~/papers/nber
```

Run the MCP server:

```bash
uvx nber-cli mcp-server
uvx nber-cli mcp-server --transport streamable_http --port 8000
```

## Output Formats

Use default text output for humans. Use JSON when the result should be consumed by another program or agent:

```bash
uvx nber-cli search "inflation" --format json
uvx nber-cli info w25000 --format json
```

## Common Failures

Interpret download errors conservatively:

- `403` means NBER denied access for the current IP, institution, account, session, download limit, or paper access policy.
- `404` means the paper or PDF endpoint was not found.
- Timeout or network errors usually mean the user should retry later or check connectivity.
- A paper's publication date alone does not prove the current user can download the PDF.

## Access Policy

NBER-CLI must not bypass NBER controls. Do not suggest proxy rotation, credential sharing, CAPTCHA bypass, account automation, request-signature tampering, or other access-circumvention behavior. If NBER returns denial, limits, redirects, or access pages, surface the response clearly and stop.

## Report Issues

If the user finds a bug or unexpected behavior in NBER-CLI, direct them to report it at `https://github.com/sepinetam/nber-cli/issues`.
