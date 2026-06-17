# Use of DB

The `db` command manages the SQLite cache used by the feed subsystem. You normally do not need to interact with it directly, but it is useful for custom paths, migrations, and manual inspection.

## Initialize the database

```bash
uvx nber-cli db init
```

This creates the default database at `~/.nber-cli/nber.db` and writes the path to `~/.nber-cli/config.json`.

## Use a custom database path

```bash
uvx nber-cli db init --db-path ~/research/nber.db
```

Subsequent `feed fetch` commands will use this path automatically.

## Migrate an existing database

```bash
uvx nber-cli db migrate ~/Dropbox/research/nber.db
```

`db migrate` moves the database file and its SQLite sidecar files to the new location and updates the config.

## Inspect the schema

```bash
sqlite3 ~/.nber-cli/nber.db ".schema"
```

The two main tables are:

- `feed_items`: one row per paper ID seen in the RSS feed.
- `feed_fetches`: one row per fetch attempt, recording time, total count, and new count.

## Query recent feed items

```bash
sqlite3 ~/.nber-cli/nber.db \
  "SELECT paper_id, title, first_seen_at, last_seen_at FROM feed_items ORDER BY last_seen_at DESC LIMIT 10;"
```

## Query fetch history

```bash
sqlite3 ~/.nber-cli/nber.db \
  "SELECT fetched_at, total_count, new_count FROM feed_fetches ORDER BY fetched_at DESC LIMIT 10;"
```

## Backup the database

```bash
cp ~/.nber-cli/nber.db ~/.nber-cli/nber.db.bak
```

SQLite files are self-contained, so ordinary file copies are valid backups.

## Reset everything

If you want to wipe the cache and start over:

```bash
uvx nber-cli feed clean --all
```

This empties `feed_items` but preserves `feed_fetches`. To remove everything, delete the database file and run `db init` again.
