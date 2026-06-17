# Use of Info

The `info` command retrieves metadata for a known NBER paper ID. It is the fastest way to read an abstract, check authors, or confirm a paper's program area.

## Basic metadata

```bash
uvx nber-cli info w25000
```

## Full record

```bash
uvx nber-cli info w25000 --all
```

`--all` usually includes the abstract, programs, and any available NBER fields.

## JSON for downstream processing

```bash
uvx nber-cli info w25000 --format json
uvx nber-cli info w25000 --all --format json | jq '.abstract'
```

## Batch inspect a list of IDs

```bash
for id in w25000 w32000 w34567; do
  uvx nber-cli info "$id" --format json >> metadata.jsonl
done
```

## Validate IDs before downloading

```bash
uvx nber-cli info w34567 --format json | jq -e '.paper_id' > /dev/null \
  && uvx nber-cli download w34567 --save-base ./papers
```

## Common failures

- `404`: the paper ID does not exist or has not been published by NBER.
- Empty abstract: NBER may not expose the abstract for some papers; this is not a CLI bug.
