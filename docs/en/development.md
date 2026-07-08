# Development

This page covers local development, testing, documentation, and release preparation.

For the detailed fixture and mocking layout, see [Test Infrastructure](testing.md). For runtime component relationships, see [System Architecture](architecture.md).

## Repository Layout

```text
.
├── src/nber_cli/          # Package source
├── tests/                 # Pytest suite
├── docs/                  # MkDocs documentation source
├── .github/workflows/     # CI, release, and docs workflows
├── pyproject.toml         # Package metadata and dependency groups
└── uv.lock                # Locked dependency graph
```

## Local Setup

```bash
uv sync --dev --group docs
```

Run the CLI from the working tree:

```bash
uv run nber-cli --help
uv run nber-cli search "inflation"
```

## Tests

```bash
uv run pytest
```

Run a specific test file:

```bash
uv run pytest tests/test_cli.py
```

## Linting

```bash
uv run ruff check .
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
- Publishing to PyPI when a GitHub release is published.

## Release Checklist

The following checks all need to pass before tagging a release. Each one catches a different class of release-time failure, and skipping any of them has historically let a regression ship.

### Code and dependencies

1. Bump the version in `pyproject.toml`.
2. Update [Changelog](changelog.md). Keep the root `CHANGELOG.md` and `docs/en/changelog.md` / `docs/zh/changelog.md` consistent.
3. Run `uv lock` and commit the resulting `uv.lock`.

### Static checks

4. Run `uv run pytest -q`.
5. Run `uv run ruff check .`.
6. Run `uv run --group docs mkdocs build --strict`.

### Cross-surface consistency

7. **Package version matches the plugin manifests.** The Claude plugin manifest (`plugins/nber-cli/.claude-plugin/plugin.json`), the Codex plugin manifest (`plugins/nber-cli/.codex-plugin/plugin.json`), and the marketplace files (`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`) must all carry the same `version` field as `pyproject.toml`. A small shell loop is enough:
   ```bash
   grep -H '"version"' pyproject.toml \
     plugins/nber-cli/.claude-plugin/plugin.json \
     plugins/nber-cli/.codex-plugin/plugin.json \
     .claude-plugin/marketplace.json
   ```
8. **Marketplace files and skill paths are tracked in Git.** Run `git ls-files plugins/ .claude-plugin/ .agents/ | sort` and confirm every path the docs reference is present. On a case-sensitive Linux checkout, `plugins/nber-cli/skills/nber-cli/SKILL.md` (lowercase) does **not** exist; the tracked path is `plugins/nber-cli/skills/NBER-CLI/SKILL.md`.
9. **Top-level imports in docs are real.** Every `from nber_cli import ...` and `import nber_cli.x as ...` example in `docs/en/` and `docs/zh/` must point to a name listed in `nber_cli.__all__`, or to a documented module-level helper. Run the snippet below and confirm the diff is empty:
   ```bash
   uv run python -c "from nber_cli import __all__; import re, pathlib; missing=[]; [missing.append((p, m)) for p in pathlib.Path('docs').rglob('*.md') for m in re.findall(r'(?:from nber_cli import|import nber_cli\.)\s*([A-Za-z0-9_]+)', p.read_text()) if m not in __all__ and not m.startswith('nber_cli.')]; print(missing)"
   ```
10. **Public `__all__` symbols are documented.** Every name in `nber_cli.__all__` should appear in `docs/en/python-api.md` and `docs/zh/python-api.md`. A future sweep can use the snippet above in reverse to flag undocumented names.
11. **CLI help text and MCP tool schemas are sane.** Run `uv run nber-cli --help` and skim each subcommand's `--help`. The MCP tool schemas are derived from the Python type hints and docstrings of `src/nber_cli/mcp.py`; review any change to that file against `docs/en/mcp.md` and `docs/zh/mcp.md`.

### Build and smoke test

12. Run `uv build` and confirm both `dist/*.whl` and `dist/*.tar.gz` are produced.
13. **Install the built wheel in a throwaway environment and run a smoke test.** This catches packaging mistakes that do not show up in the dev install:
    ```bash
    uv venv /tmp/nber-cli-smoke
    /tmp/nber-cli-smoke/bin/pip install dist/*.whl
    /tmp/nber-cli-smoke/bin/nber-cli --version
    /tmp/nber-cli-smoke/bin/nber-cli info cache
    /tmp/nber-cli-smoke/bin/nber-cli mcp-server --help
    ```
14. **Run `git diff --check` on the release branch.** This catches trailing-whitespace and conflict-marker mistakes that the other checks can miss.

### Publish

15. Create and publish a GitHub release. The `publish.yml` workflow builds the package and uploads it to PyPI; the version in `pyproject.toml` at release time is what gets published, which is why step 1 is non-negotiable.

### Optional but recommended

- Cross-check the docs index against the file system: `git ls-files docs/ | sort` should match the nav declared in `mkdocs.yml`.
- From a clean checkout on a case-sensitive filesystem (Linux CI is enough), run `uv sync --dev --group docs` and `uv run nber-cli --help` to make sure no path or import is sensitive to case.

## Coding Style

- Python code targets Python 3.11 or newer.
- Variable names should follow PEP 8 and use clear English names.
- Code comments should be written in English.
- Keep CLI behavior script-friendly: stable exit codes, readable errors, and JSON output where automation needs it.
