# Use of Feed

This document expands on the feed workflows in [`../SKILL.md`](../SKILL.md). It is meant for users who want to monitor NBER's new working papers RSS feed (`https://www.nber.org/rss/new.xml`) automatically or integrate it into larger research pipelines.

## What the feed cache does

`nber-cli feed fetch` downloads the current RSS feed, parses every item, and stores them in a local SQLite database. Each item is keyed by NBER paper ID. On every subsequent fetch:

- Items already seen have their `last_seen_at` timestamp updated.
- Items never seen before are reported as "new" by default.
- A row is appended to `feed_fetches` recording when the fetch happened, how many items NBER returned, and how many were new.

This makes the feed cache ideal for answering "what is new since I last checked?" rather than "what has NBER ever published?"

## Basic examples

### First fetch

```bash
uvx nber-cli feed fetch
```

The first time you run this, every item in the current RSS feed is new and will be printed. It also creates the default database at `~/.nber-cli/nber.db`.

### Incremental fetch

Run the same command later:

```bash
uvx nber-cli feed fetch
```

Only papers not already in `feed_items` are printed.

### See everything NBER is advertising right now

```bash
uvx nber-cli feed fetch --display-all
```

### Limit output

```bash
uvx nber-cli feed fetch --max-items 10
```

When `--max-items` is set, `--display-all` is enabled automatically, so you see the most recent items regardless of cache state.

## JSON output and filtering

### Pretty-print the newest item

```bash
uvx nber-cli feed fetch --max-items 1 --format json | jq '.items[0]'
```

### List only paper IDs and titles

```bash
uvx nber-cli feed fetch --format json | jq -r '.items[] | "\(.paper_id): \(.title)"'
```

### Filter by author

```bash
uvx nber-cli feed fetch --display-all --format json \
  | jq '.items[] | select(.authors[] | ascii_downcase | contains("acemoglu"))'
```

### Filter by keyword in title or abstract

```bash
uvx nber-cli feed fetch --display-all --format json \
  | jq '.items[] | select(.title + .abstract | ascii_downcase | contains("minimum wage"))'
```

### Build a daily JSON Lines log

```bash
TODAY=$(date +%Y-%m-%d)
uvx nber-cli feed fetch --format json \
  | jq -c '.items[]' >> "feed-${TODAY}.jsonl"
```

## Complete research workflows

### Fetch, inspect, download

```bash
# 1. Discover the latest papers
uvx nber-cli feed fetch --max-items 20

# 2. Read metadata for one of them
uvx nber-cli info w32000 --all

# 3. Download the PDF
uvx nber-cli download w32000 --save-base ./papers
```

### Batch download all new papers

```bash
uvx nber-cli feed fetch --format json > /tmp/feed.json
jq -r '.items[].paper_id' /tmp/feed.json > /tmp/new_papers.txt
uvx nber-cli download --batch $(cat /tmp/new_papers.txt) --save-base ./papers/new-this-fetch
```

### Weekly digest script

Save as `weekly_digest.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

WEEK_DIR="./papers/$(date +%Y-%W)"
mkdir -p "$WEEK_DIR"

FEED_JSON="/tmp/nber_feed_$(date +%s).json"
uvx nber-cli feed fetch --format json > "$FEED_JSON"

NEW_COUNT=$(jq '.new_count' "$FEED_JSON")
echo "Found ${NEW_COUNT} new papers this week."

if [ "$NEW_COUNT" -gt 0 ]; then
  jq -r '.items[].paper_id' "$FEED_JSON" | while read -r paper_id; do
    uvx nber-cli download "$paper_id" --save-base "$WEEK_DIR"
  done
fi
```

Make it executable and run it on a schedule:

```bash
chmod +x weekly_digest.sh
```

### Alert when a specific topic appears

```bash
#!/usr/bin/env bash
MATCHES=$(uvx nber-cli feed fetch --format json \
  | jq -r '.items[] | select(.title + .abstract | ascii_downcase | contains("artificial intelligence")) | .paper_id')

if [ -n "$MATCHES" ]; then
  echo "New AI papers on NBER:"
  echo "$MATCHES"
  # Add notification hook here, e.g. mail, Slack, etc.
fi
```

## Cleanup and maintenance

### Default cleanup (items not seen in 30 days)

```bash
uvx nber-cli feed clean
```

### Aggressive cleanup (items not seen in 7 days)

```bash
uvx nber-cli feed clean --days 7
```

### Date range cleanup

```bash
uvx nber-cli feed clean --start-date 2026-01-01 --end-date 2026-03-31
```

### Reset the cache entirely

```bash
uvx nber-cli feed clean --all
```

This removes every row from `feed_items`. The next `feed fetch` will report everything as new, which is useful if you change your filtering logic and want to re-evaluate the current feed.

### Inspect the feed tables directly

```bash
sqlite3 ~/.nber-cli/nber.db "SELECT paper_id, title, first_seen_at, last_seen_at FROM feed_items ORDER BY last_seen_at DESC LIMIT 10;"
```

```bash
sqlite3 ~/.nber-cli/nber.db "SELECT fetched_at, total_count, new_count FROM feed_fetches ORDER BY fetched_at DESC LIMIT 10;"
```

## Automation recipes

### Cron: weekday morning fetch

```cron
0 9 * * 1-5 cd /home/user/research && uvx nber-cli feed fetch --format json | jq -c '.items[]' >> nber_feed_new.jsonl
```

### Cron: weekly download on Monday

```cron
0 10 * * 1 cd /home/user/research && ./weekly_digest.sh
```

### Systemd timer (user-level)

`~/.config/systemd/user/nber-feed.timer`:

```ini
[Unit]
Description=Fetch NBER feed every weekday morning

[Timer]
OnCalendar=Mon-Fri 09:00
Persistent=true

[Install]
WantedBy=timers.target
```

`~/.config/systemd/user/nber-feed.service`:

```ini
[Unit]
Description=Fetch NBER feed

[Service]
Type=oneshot
WorkingDirectory=%h/research
ExecStart=/bin/sh -c 'uvx nber-cli feed fetch --format json | jq -c ".items[]" >> %h/research/nber_feed_new.jsonl'
```

Enable and start:

```bash
systemctl --user daemon-reload
systemctl --user enable nber-feed.timer
systemctl --user start nber-feed.timer
```

## Tips and caveats

- The RSS feed only contains the papers NBER lists in `new.xml`. It is not a complete catalog. Use `nber-cli search` for historical discovery.
- `feed fetch` does not download PDFs. Combine it with `nber-cli download` if you want PDFs.
- The cache deduplicates by NBER paper ID, not by title or DOI. If a paper changes title, the existing row is updated on the next fetch.
- `feed_fetches` grows forever. If it becomes large, you can truncate it manually with `sqlite3`; there is no CLI command for that yet.
- NBER's RSS sometimes contains unusual characters. The parser repairs some common XML issues, but malformed items may be skipped silently to avoid aborting the whole fetch.

## See also

- [`../SKILL.md`](../SKILL.md) for the main skill documentation, including assumptions, common failures, and access policy.
- [`use-of-search.md`](./use-of-search.md) for historical catalog queries.
- [`use-of-download.md`](./use-of-download.md) for batch and restricted downloads.
- [`use-of-automation.md`](./use-of-automation.md) for larger scheduled workflows.
- `nber-cli feed --help`, `nber-cli feed fetch --help`, and `nber-cli feed clean --help` for the latest CLI options.
