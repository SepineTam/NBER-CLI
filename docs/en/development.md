# Development

This page covers local development, testing, documentation, and release preparation.

For the detailed fixture and mocking layout, see [Test Infrastructure](testing.md). For runtime component relationships, see [System Architecture](architecture.md).

## Repository Layout

```text
.
├── src/nber_cli/          # CLI, MCP, core logic, persistence, and migrations
├── src/nber_server/       # Optional local FastAPI service
├── desktop/               # React frontend and Tauri/Rust shell
├── scripts/               # Desktop build, signing, artifact, and smoke helpers
├── tests/                 # Python and release-tooling tests
├── docs/                  # MkDocs documentation source
├── .github/workflows/     # CI, release, Desktop, and docs workflows
└── pyproject.toml         # Package metadata and dependency groups
```

`uv.lock` can be generated locally, but this repository currently ignores it and does not treat it as a release artifact.

## Local Setup

```bash
uv sync --dev --extra server --group docs
```

Run the CLI from the working tree:

```bash
uv run nber-cli --help
uv run nber-cli search "inflation"
uv run nber-server --help
```

For Desktop development, also install Node dependencies and run the Tauri development shell:

```bash
cd desktop
npm ci
npm run tauri dev
```

## Tests

```bash
uv run pytest tests
cd desktop
npm run test
```

Run a specific test file:

```bash
uv run pytest tests/cli/test_cli.py
```

## Linting

```bash
uv run ruff check .
cd desktop
npm run lint
cd src-tauri
cargo check
```

## Documentation

Serve the docs locally:

```bash
uv run --group docs mkdocs serve
```

Build the docs in strict mode:

```bash
uv run --group docs mkdocs build --strict
```

The generated site is written to `site/`, which should not be committed.

## GitHub Actions

The project uses separate workflows for:

- Linting with Ruff.
- Running Pytest.
- Building MkDocs documentation.
- Deploying documentation to GitHub Pages on pushes to `master`.
- Checking the React frontend on pull requests and pushes.
- Building macOS, Windows, and Linux Desktop installers on `v*` tags or manual dispatch.
- Publishing to PyPI when a GitHub release is published.

The normal pull-request Desktop check runs Python, TypeScript, frontend tests, the Vite build, and Rust unit tests. Full platform installer builds run only for tags or manual workflow dispatch.

## Release Checklist

The following checks all need to pass before tagging a release. Each one catches a different class of release-time failure, and skipping any of them has historically let a regression ship.

### Code and dependencies

1. Bump the version in `pyproject.toml`, `desktop/package.json`, `desktop/package-lock.json`, `desktop/src-tauri/tauri.conf.json`, `desktop/src-tauri/Cargo.toml`, `desktop/src-tauri/Cargo.lock`, `tests/release/test_release_metadata.py`, the Claude/Codex plugin manifests, and `.claude-plugin/marketplace.json`.
2. Update [Changelog](changelog.md). Keep the root `CHANGELOG.md` and `docs/en/changelog.md` / `docs/zh/changelog.md` consistent.
3. Run `uv run pytest tests/release/test_release_metadata.py -q` and confirm all release versions are synchronized. Do not add `uv.lock`; it is intentionally ignored under the current repository policy.

### Static checks

4. Run `uv run pytest tests -q`.
5. Run `uv run ruff check .`.
6. Run `uv run --group docs mkdocs build --strict`.
7. In `desktop/`, run `npm ci`, `npm run lint`, `npm run test`, and `npm run build`; then run `cargo check` in `desktop/src-tauri/`.

### Cross-surface consistency

8. **Tracked plugin files and skill paths exist.** Run `git ls-files plugins/ .claude-plugin/ | sort`. On a case-sensitive checkout, the tracked skill path is `plugins/nber-cli/skills/NBER-CLI/SKILL.md`.
9. **Top-level imports in docs are real.** Every `from nber_cli import ...` and `import nber_cli.x as ...` example in `docs/en/` and `docs/zh/` must point to a name listed in `nber_cli.__all__`, or to a documented module-level helper. Run the snippet below and confirm the output is empty:
   ```bash
   uv run python -c "from nber_cli import __all__; import re, pathlib; missing=[]; [missing.append((p, m)) for p in pathlib.Path('docs').rglob('*.md') for m in re.findall(r'(?:from nber_cli import|import nber_cli\.)\s*([A-Za-z0-9_]+)', p.read_text()) if m not in __all__ and not m.startswith('nber_cli.')]; print(missing)"
   ```
10. **Public `__all__` symbols are documented.** Every name in `nber_cli.__all__` should appear in `docs/en/python-api.md` and `docs/zh/python-api.md`. A future sweep can use the snippet above in reverse to flag undocumented names.
11. **CLI help text and MCP tool schemas are sane.** Run `uv run nber-cli --help` and skim each subcommand's `--help`. The MCP tool schemas are derived from the Python type hints and docstrings of `src/nber_cli/mcp/mcp.py`; review any change to that file against `docs/en/mcp.md` and `docs/zh/mcp.md`.
12. **HTTP routes match the public contract.** Run `uv run pytest tests/server/test_server.py -q` and review route or schema changes against `docs/en/http-api.md` and `docs/zh/http-api.md`.

### Build and smoke test

13. Build from a clean checkout with `uv build` and confirm both `dist/*.whl` and `dist/*.tar.gz` are produced.
14. **Inspect the artifacts before installation.** The wheel must contain both `nber_cli/` and `nber_server/`, including `nber_cli/db/migrations/`. The sdist must not contain local databases or logs, `.dev`, `.agents`, `.conductor`, `.superpowers`, `tmp`, `output`, `node_modules`, Rust `target`, or bundled sidecar binaries. Treat an unexpectedly large sdist as a release blocker.
    ```bash
    unzip -l dist/*.whl | less
    tar -tzf dist/*.tar.gz | less
    ```
15. **Install the built wheel in a throwaway environment and test every console entry point.** This catches missing packages that do not show up in the development install:
    ```bash
    uv venv --seed /tmp/nber-cli-smoke
    /tmp/nber-cli-smoke/bin/pip install dist/*.whl
    /tmp/nber-cli-smoke/bin/nber-cli --version
    /tmp/nber-cli-smoke/bin/nber-cli info cache
    /tmp/nber-cli-smoke/bin/nber-cli mcp-server --help
    /tmp/nber-cli-smoke/bin/nber-server --help
    /tmp/nber-cli-smoke/bin/nber-sidecar --help
    ```
16. Run the Desktop package checker and native installer smoke test on every release platform, then confirm macOS arm64/x64, Windows x64, and Linux x64 artifacts were uploaded.
17. **Run `git diff --check` on the release branch.** This catches trailing whitespace and conflict markers.

### Publish

18. Before creating the tag, verify that the intended tag is exactly `v` plus the `pyproject.toml` version. The workflows currently accept any `v*` tag, so this remains a manual release gate.
19. Push the matching tag and wait for the Desktop workflow to create or update the draft GitHub Release. Review every uploaded artifact before publishing it.
20. Publish the GitHub Release only after the draft is complete. Publishing triggers `publish.yml`, which rebuilds and uploads the Python wheel and sdist to PyPI.

### Optional but recommended

- Cross-check the English and Chinese public docs against the nav declared in `mkdocs.yml`. Internal files under `docs/desktop/` are intentionally outside the public nav.
- From a clean checkout on a case-sensitive filesystem (Linux CI is enough), run `uv sync --dev --group docs` and `uv run nber-cli --help` to make sure no path or import is sensitive to case.

## Coding Style

- Python code targets Python 3.11 or newer.
- Variable names should follow PEP 8 and use clear English names.
- Code comments should be written in English.
- Keep CLI behavior script-friendly: stable exit codes, readable errors, and JSON output where automation needs it.
