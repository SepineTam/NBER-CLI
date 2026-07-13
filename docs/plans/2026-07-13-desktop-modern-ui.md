# Desktop Modern UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the existing Desktop interface with the approved modern research-desk design while preserving all real feed, paper, settings, and sidecar behavior.

**Architecture:** Keep the existing Zustand store and HTTP/Tauri boundaries unchanged. Recompose the React view into a compact navigation rail, a searchable/filterable feed workspace, and a paper inspector; keep citation formatting as a pure frontend helper so it is testable and does not expand the Python API.

**Tech Stack:** React 18, TypeScript, Zustand, Vite, Vitest, Testing Library, Tauri v2, local WOFF2 fonts.

---

### Task 1: Citation formatting helper

**Files:**
- Create: `desktop/src/citation.ts`
- Create: `desktop/src/citation.test.ts`

**Step 1:** Add failing tests for BibTeX as the default and for APA, MLA, Harvard, Chicago, and GB/T 7714—2025 output.

**Step 2:** Run `npm test -- --run src/citation.test.ts` from `desktop/` and confirm the helper is missing.

**Step 3:** Implement typed citation style metadata, formatters, NBER URL fallback, author-name handling, and clipboard fallback as pure functions plus one DOM adapter.

**Step 4:** Run the citation tests and confirm all formats pass.

### Task 2: Local font assets and global visual system

**Files:**
- Create: `desktop/src/assets/fonts/SourceSans3VF-Upright.woff2`
- Create: `desktop/src/assets/fonts/SourceSerif4Variable-Roman.woff2`
- Create: `desktop/src/assets/fonts/SourceSans3-LICENSE.md`
- Create: `desktop/src/assets/fonts/SourceSerif4-LICENSE.md`
- Modify: `desktop/src/index.css`
- Modify: `desktop/src/App.css`

**Step 1:** Move the approved OFL-licensed font assets into the production source tree with their license files.

**Step 2:** Define local `@font-face` rules and the approved navy, paper, orange, typography, spacing, and motion tokens.

**Step 3:** Replace the old 232px sidebar and generic panel styles with the compact rail, editorial feed, inspector, alerts, settings, loading, and responsive rules.

**Step 4:** Run `npm run lint` and resolve CSS-adjacent TypeScript issues before continuing.

### Task 3: Application shell and feed workspace

**Files:**
- Modify: `desktop/src/App.tsx`
- Modify: `desktop/src/components/Sidebar.tsx`
- Modify: `desktop/src/components/RefreshButton.tsx`
- Modify: `desktop/src/pages/FeedPage.tsx`
- Modify: `desktop/src/components/FeedList.tsx`
- Modify: `desktop/src/components/FeedItemRow.tsx`
- Modify: `desktop/src/components/FeedItemRow.test.tsx`
- Modify: `desktop/src/components/FeedList.test.tsx`

**Step 1:** Update component tests for accessible icon labels, filtering, grouped dates, and the approved refresh wording.

**Step 2:** Run the affected tests and confirm they fail against the old UI.

**Step 3:** Implement the compact rail, local-service state, research-desk header, paper count, client-side search, all/unread filters, date groups, selected styling, and load-more behavior.

**Step 4:** Run the affected tests and confirm feed interaction remains intact.

### Task 4: Paper inspector and citation split button

**Files:**
- Modify: `desktop/src/components/PaperDetail.tsx`
- Modify: `desktop/src/components/PaperDetail.test.tsx`

**Step 1:** Add tests that confirm the PDF download action is absent, BibTeX is the default copy action, the menu exposes all approved formats, and selecting GB/T 7714—2025 changes the primary action.

**Step 2:** Run the test and confirm it fails against the old detail drawer.

**Step 3:** Implement the editorial paper inspector, real metadata, read toggle, save/open URL behavior already supported by the app, citation split button, click-outside handling, Escape handling, and copy status feedback.

**Step 4:** Run the component tests and confirm the citation and read-status flows pass.

### Task 5: Settings and final verification

**Files:**
- Modify: `desktop/src/pages/SettingsPage.tsx`

**Step 1:** Restyle settings using the same research-desk system without changing settings API behavior.

**Step 2:** Run `npm test`, `npm run lint`, and `npm run build` from `desktop/`.

**Step 3:** Start the Vite page, inspect it at 1440×900 and a narrower desktop width, and exercise search, unread filtering, paper selection, citation format selection, copy, refresh feedback, and settings navigation.

**Step 4:** Capture the final screenshot under `output/playwright/`, run `git diff --check`, and review `git status` to ensure `.claude/` and `.superpowers/` remain untouched.

**Step 5:** Do not stage or commit until the user approves the migrated UI.
