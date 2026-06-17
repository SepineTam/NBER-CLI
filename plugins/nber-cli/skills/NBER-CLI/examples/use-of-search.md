# Use of Search

The `search` command queries the historical NBER working paper catalog. Unlike [`use-of-feed.md`](./use-of-feed.md), it does not maintain a local cache; it is a one-shot lookup against NBER's public search endpoint.

## Basic search

```bash
uvx nber-cli search "labor economics"
uvx nber-cli search "minimum wage"
```

## Narrow by publication date

```bash
uvx nber-cli search "inflation" --start-date 2020-01-01 --end-date 2024-12-31
```

The date range refers to the paper's NBER issue date, not the download eligibility date.

## Machine-readable output

```bash
uvx nber-cli search "ChatGPT" --format json
uvx nber-cli search "inflation" --format json | jq '.results[] | {paper_id, title, authors}'
```

## Paginate large result sets

```bash
uvx nber-cli search "health" --page 1 --per-page 20
uvx nber-cli search "health" --format json | jq '.pagination'
```

## Combine search with download

```bash
uvx nber-cli search "remote work" --format json \
  | jq -r '.results[].paper_id' \
  | head -n 10 \
  | xargs uvx nber-cli download --batch --save-base ./papers/remote-work
```

## When to use search instead of feed

- You need papers older than the current RSS feed window.
- You want to estimate the size of a literature before deciding which papers to inspect.
- You know a keyword or author but not the exact paper ID.

## Caveats

- Search results are bounded by NBER's public search API. Very broad queries may hit page limits.
- A result in search does not guarantee PDF download access. Check [`use-of-download.md`](./use-of-download.md) for access handling.
