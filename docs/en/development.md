# Development

This page covers local development, testing, documentation, and release preparation.

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

1. Update the version in `pyproject.toml`.
2. Update [Changelog](changelog.md).
3. Run `uv lock`.
4. Run `uv run pytest`.
5. Run `uv run ruff check .`.
6. Run `uv run --group docs mkdocs build --strict`.
7. Create and publish a GitHub release to trigger PyPI publishing.

## Coding Style

- Python code targets Python 3.11 or newer.
- Variable names should follow PEP 8 and use clear English names.
- Code comments should be written in English.
- Keep CLI behavior script-friendly: stable exit codes, readable errors, and JSON output where automation needs it.
