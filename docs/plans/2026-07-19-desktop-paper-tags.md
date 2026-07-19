# Desktop Paper Tags Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Add Desktop-only paper tags seeded from NBER info metadata and editable by the user without overwriting raw metadata.

**Architecture:** Rust owns three Desktop-only SQLite tables for raw, user, and hidden raw tags. Feed refresh continues to use the bundled Python worker for Feed and info retrieval, then Rust synchronizes raw tags from `info_cache`. Tauri commands expose tag CRUD, while React renders and filters the combined visible tag set.

**Tech Stack:** Python 3.12, SQLite, Rust/Tauri 2, React 19, TypeScript, Zustand, Vitest

---

### Task 1: Carry topic parsing into the 0.9.2 branch

**Files:**
- Modify: `src/nber_cli/fetch/fetcher.py`
- Test: `tests/fetch/test_fetcher.py`

Merge the completed topic parser fix from `master` and run its focused tests.

### Task 2: Add Desktop tag storage and synchronization

**Files:**
- Modify: `desktop/src-tauri/src/models.rs`
- Modify: `desktop/src-tauri/src/database.rs`
- Test: `desktop/src-tauri/src/database.rs`

Create Desktop-only tables, normalize and split semicolon-separated raw metadata, return visible tags with feed items and papers, and implement add/rename/remove operations with tests.

### Task 3: Expose tag commands to the Desktop UI

**Files:**
- Modify: `desktop/src-tauri/src/commands.rs`
- Modify: `desktop/src-tauri/src/lib.rs`
- Modify: `desktop/src/types/index.ts`
- Modify: `desktop/src/api/papers.ts`
- Test: `desktop/src/api/papers.test.ts`

Add typed Tauri commands for tag CRUD and register them in the invoke handler.

### Task 4: Render and edit tags

**Files:**
- Modify: `desktop/src/components/FeedItemRow.tsx`
- Modify: `desktop/src/components/PaperDetail.tsx`
- Create: `desktop/src/components/TagEditor.tsx`
- Modify: `desktop/src/stores/appStore.ts`
- Modify: `desktop/src/App.css`
- Test: component and store tests under `desktop/src/`

Show compact tags in the feed, add an inline editor in paper details, and immediately update local state after successful edits.

### Task 5: Search and filter by tags

**Files:**
- Modify: `desktop/src/pages/FeedPage.tsx`
- Modify: relevant feed tests under `desktop/src/`

Include tag text in search and add a compact all-tags selector based on loaded feed items.

### Task 6: Refresh stale metadata and verify the full application

**Files:**
- Modify: `src/nber_cli/desktop_worker.py`
- Test: `tests/desktop/test_desktop_worker.py`

Refetch legacy cached info records that lack both Topics and Programs, then run Python, Rust, frontend, build, and real refresh smoke checks.

