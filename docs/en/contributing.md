# Contributing

Contributions are welcome. The best contributions keep the CLI small, predictable, and useful for research workflows.

## Good First Contributions

- Improve documentation examples.
- Add tests for CLI edge cases.
- Improve error messages for network and download failures.
- Add formatter coverage for fields exposed by NBER.
- File issues with reproducible command output.

## Before Opening a Pull Request

Run the local checks:

```bash
uv sync --dev --group docs
uv run pytest tests
uv run ruff check .
uv run --group docs mkdocs build --strict
```

## Pull Request Expectations

- Keep changes focused.
- Add or update tests when behavior changes.
- Update English and Chinese documentation together when user-facing behavior changes.
- Avoid unrelated formatting churn.
- Explain any compatibility impact in the pull request description.

## Documentation Changes

When adding a new documentation page:

1. Add the English page under `docs/`.
2. Add the Simplified Chinese page under `docs/zh/`.
3. Register both pages in `mkdocs.yml`.
4. Run `uv run --group docs mkdocs build --strict`.

## Issue Reports

Useful issue reports include:

- The command that failed.
- The installed NBER-CLI version from `nber-cli --version`.
- The operating system and Python version.
- The full error output.
- Whether the same paper is accessible in a browser.
