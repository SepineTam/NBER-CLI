# Use of Error Handling

NBER-CLI surfaces HTTP and network errors directly. This document explains how to interpret them and how to write robust scripts that fail safely.

## HTTP status codes

### 403 Forbidden

NBER denied access. Possible causes:

- The current IP or institution is not subscribed.
- A personal download quota has been reached.
- The paper is under restricted access.

Do not attempt proxy rotation, credential sharing, CAPTCHA bypass, or request-signature tampering. Stop and surface the error to the user.

### 404 Not Found

The paper or PDF endpoint does not exist. Check that the paper ID is correct and that NBER has published a PDF for it.

### Timeout and network errors

Retry once after a short delay, then stop. Persistent timeouts usually indicate a local network issue or NBER maintenance.

## Script patterns

### Check a command before using its output

```bash
if ! uvx nber-cli info w25000 --format json > /tmp/info.json 2>/tmp/info.err; then
  echo "Failed to fetch info: $(cat /tmp/info.err)"
  exit 1
fi
```

### Handle empty search results

```bash
COUNT=$(uvx nber-cli search "xyzabc123" --format json | jq '.results | length')
if [ "$COUNT" -eq 0 ]; then
  echo "No results found."
  exit 0
fi
```

### Skip failed downloads in batch

```bash
uvx nber-cli feed fetch --format json \
  | jq -r '.items[].paper_id' \
  | while read -r paper_id; do
      uvx nber-cli download "$paper_id" --save-base ./papers || echo "Skipped $paper_id"
    done
```

### Validate JSON shape

```bash
uvx nber-cli info w25000 --format json | jq -e '.paper_id and .title' || {
  echo "Unexpected response shape"
  exit 1
}
```

## Logging

```bash
uvx nber-cli feed fetch --format json > feed.json 2> feed.log
```

Always capture stderr in automated scripts so you can inspect the exact error message later.

## When to stop vs retry

- Retry: transient timeout, `5xx` server error.
- Stop: `403`, `404`, repeated failures after one retry.
