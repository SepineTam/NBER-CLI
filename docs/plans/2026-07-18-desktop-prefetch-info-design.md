# Desktop Feed Metadata Prefetch Design

## Goal

Make normal Desktop startup and paper opening independent of the bundled Python worker. The worker remains the single implementation of NBER network and parsing behavior, but runs only during database initialization or Feed refresh.

## Data flow

1. On startup, Rust validates the configured SQLite schema. It starts the bundled worker only when the database is missing or needs initialization or migration.
2. Feed refresh starts one worker process. The worker fetches the RSS Feed, then fills missing or expired `info_cache` rows for the current Feed with bounded concurrency.
3. A failed paper metadata request is recorded in the refresh result but does not discard the successfully refreshed Feed or other metadata.
4. Opening a paper reads `feed_items`, `info_cache`, and `read_status` directly in Rust. When metadata is unavailable, Desktop returns the RSS title, authors, abstract, and URL with an empty date instead of making a network request.
5. Rust continues to write read/unread state directly to SQLite.

## Performance and safety

- Normal startup performs only local configuration and SQLite work.
- Opening a paper performs only local SQLite work and should complete without a network timeout.
- Feed refresh may take longer, especially the first time, because it prepares paper details in advance.
- Metadata requests use a small concurrency limit to avoid excessive load on NBER.
- SQLite cache writes continue to use the existing Python cache implementation, preserving one source of truth.

## Verification

- Python tests cover metadata prefetch success, cache hits, partial failures, and bounded work selection.
- Rust tests cover startup schema decisions and paper results with and without cached metadata.
- A packaged Desktop smoke test runs with an empty `PATH` and an already initialized database, proving normal startup does not require the worker.
- A real Feed refresh verifies that metadata rows are populated and paper opening reads them locally.
