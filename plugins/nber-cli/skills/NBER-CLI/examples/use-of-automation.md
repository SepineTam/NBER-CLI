# Use of Automation

This document combines the commands from other examples into larger automated workflows. It assumes you have already read [`use-of-feed.md`](./use-of-feed.md), [`use-of-download.md`](./use-of-download.md), and [`use-of-json-pipeline.md`](./use-of-json-pipeline.md).

## Design goals for automation

- Idempotency: running the same script twice should not duplicate work.
- Observability: log what happened and how many new items were found.
- Conservatism: do not retry aggressively after access errors.

## Weekly digest with email-style summary

Save as `weekly_digest.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

RESEARCH_DIR="$HOME/research"
WEEK_DIR="$RESEARCH_DIR/papers/$(date +%Y-%W)"
mkdir -p "$WEEK_DIR"

FEED_JSON="$RESEARCH_DIR/tmp/nber_feed_$(date +%s).json"
mkdir -p "$RESEARCH_DIR/tmp"

uvx nber-cli feed fetch --format json > "$FEED_JSON"
NEW_COUNT=$(jq '.new_count' "$FEED_JSON")

cat <<SUMMARY
NBER weekly digest for $(date +%Y-%m-%d)
New papers this fetch: $NEW_COUNT
SUMMARY

if [ "$NEW_COUNT" -gt 0 ]; then
  jq -r '.items[].paper_id' "$FEED_JSON" | while read -r paper_id; do
    uvx nber-cli download "$paper_id" --save-base "$WEEK_DIR" || true
  done
fi
```

The `|| true` prevents one failed download from aborting the loop. Inspect the logs afterward for 403 or 404 errors.

## Cron: daily fetch with JSONL log

```cron
0 9 * * * cd /home/user/research && uvx nber-cli feed fetch --format json | jq -c '.items[]' >> nber_feed_new.jsonl
```

## Cron: weekly download and summary

```cron
0 10 * * 1 /home/user/research/weekly_digest.sh >> /home/user/research/logs/weekly_digest.log 2>&1
```

## Systemd user timer

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

Enable:

```bash
systemctl --user daemon-reload
systemctl --user enable nber-feed.timer
systemctl --user start nber-feed.timer
```

## Topic alert script

```bash
#!/usr/bin/env bash
MATCHES=$(uvx nber-cli feed fetch --format json \
  | jq -r '.items[] | select(.title + .abstract | ascii_downcase | contains("artificial intelligence")) | "\(.paper_id): \(.title)"')

if [ -n "$MATCHES" ]; then
  echo "$MATCHES" | mail -s "New NBER papers on AI" user@example.com
fi
```

Replace `mail` with your preferred notification channel.

## Avoiding automation pitfalls

- Do not retry downloads automatically after a `403`; NBER may rate-limit or block your IP.
- Store logs outside the weekly paper folder so they are not accidentally deleted.
- Rotate the JSONL file periodically to prevent it from growing without bound.
- Test scripts manually before scheduling them.
