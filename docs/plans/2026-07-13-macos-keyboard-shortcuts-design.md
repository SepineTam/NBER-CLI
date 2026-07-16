# macOS Keyboard Shortcuts Design

## Scope

NBER-CLI Desktop should support the macOS shortcuts that map directly to an existing user action. The application will not add shortcuts for actions it does not provide, such as creating, opening, saving, or printing documents.

| Shortcut | Action | Source |
| --- | --- | --- |
| `Command+,` | Open settings | Native application menu |
| `Command+F` | Open the paper feed and focus search | Native Edit menu |
| `Command+K` | Open the paper feed and focus search | Application alias |
| `Command+R` | Synchronize the latest papers | Native View menu |
| `Command+1` | Open the paper feed | Native View menu |
| `Escape` | Close the citation format menu | Application behavior |
| Standard Edit shortcuts | Undo, redo, cut, copy, paste, select all | Tauri native menu |
| Standard window shortcuts | Minimize, full screen, close, hide, quit | Tauri native menu |

## Architecture

Discoverable shortcuts belong in the native macOS menu. A native menu action emits a small Tauri event to the React application. React owns the resulting page navigation, search focus, and feed synchronization so the native layer does not duplicate application state.

`Command+K` remains an alias for search because it is already displayed in the interface. Search shortcuts work from both the feed and settings views: they first open the feed, then focus the search field after it mounts.

## Testing and commits

Existing application shortcuts receive focused component tests. Every newly added shortcut receives unit coverage, a TypeScript build, a Rust check, and a macOS runtime check. Each existing-shortcut test or new shortcut is committed separately. A final full-suite and worktree audit confirms that unrelated server changes remain outside these commits.
