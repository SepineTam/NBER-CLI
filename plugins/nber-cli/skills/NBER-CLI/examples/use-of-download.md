# Use of Download

The `download` command fetches PDF files for one or more NBER papers. It is the only command that writes binary files. Use it after you have discovered paper IDs via [`use-of-search.md`](./use-of-search.md), [`use-of-feed.md`](./use-of-feed.md), or [`use-of-info.md`](./use-of-info.md).

## Download a single paper

```bash
uvx nber-cli download w34567
```

By default this saves to the current working directory.

## Choose the output location

```bash
uvx nber-cli download w34567 --save-base ~/papers/nber
uvx nber-cli download w34567 --file ~/papers/nber/w34567.pdf
```

`--save-base` creates a directory if it does not exist. `--file` sets an exact output path.

## Batch download

```bash
uvx nber-cli download --batch w34567 w25000 w32000 --save-base ~/papers/nber
```

You can also pipe IDs from another command:

```bash
jq -r '.items[].paper_id' feed.json \
  | xargs uvx nber-cli download --batch --save-base ./papers/this-week
```

## Restricted access handling

Some papers are restricted by NBER based on subscription, IP range, or download quotas. The CLI surfaces HTTP status codes without bypassing controls.

```bash
uvx nber-cli download w34567 --restrict true
```

If you receive `403`, stop and verify your access rights rather than retrying in a loop.

## Naming conventions

Downloaded files are named `{paper_id}.pdf` by default. When using `--file`, you control the name explicitly.

## Combine with feed for a weekly folder

```bash
WEEK_DIR="./papers/$(date +%Y-%W)"
mkdir -p "$WEEK_DIR"
uvx nber-cli feed fetch --format json \
  | jq -r '.items[].paper_id' \
  | xargs uvx nber-cli download --batch --save-base "$WEEK_DIR"
```

## Common failures

- `403`: access denied. Do not attempt proxy rotation or credential sharing.
- `404`: the PDF endpoint was not found; the paper may not have a public PDF.
- Timeout: retry later or check connectivity.
