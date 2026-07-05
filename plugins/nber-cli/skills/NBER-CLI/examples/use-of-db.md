# Use of DB

The `db` command manages the local database used by `info`, `search`, `download`, and `feed` for cache and behavior logs. You normally do not need to interact with it directly, but it is useful for custom paths, `sqlite:///...` URLs, migrations, and manual inspection.

The database is a local SQLite file accessed through SQLModel/SQLAlchemy. It stays on the user's machine unless the user copies or exports it. On macOS and Linux, `db init` and `db migrate` require the selected database file to be inside the user's home directory.

## Initialize the database

```bash
uvx nber-cli db init
```

This creates the default database at `~/.nber-cli/nber.db` and writes the path to `~/.nber-cli/config.json`.

## Use a custom database path

```bash
uvx nber-cli db init --db-path ~/research/nber.db
```

You can also use a SQLite URL:

```bash
uvx nber-cli db init --db-path sqlite:////Users/name/research/nber.db
```

Subsequent commands that touch the local database will use this location automatically.

## Migrate an existing database

```bash
uvx nber-cli db migrate ~/Dropbox/research/nber.db
```

`db migrate` moves the database file and its SQLite sidecar files to the new location and updates the config.

## Inspect the schema

```bash
sqlite3 ~/.nber-cli/nber.db ".schema"
```

The feed tables are:

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
