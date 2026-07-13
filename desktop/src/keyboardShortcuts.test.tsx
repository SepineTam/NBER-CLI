import { fireEvent, renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { usePaperSearchShortcuts, useRefreshShortcut } from './keyboardShortcuts'

describe('paper search keyboard shortcuts', () => {
  it.each([
    ['Command+F', 'f'],
    ['Command+K', 'k'],
  ])('opens paper search with %s', (_label, key) => {
    const openSearch = vi.fn()
    renderHook(() => usePaperSearchShortcuts(openSearch))

    fireEvent.keyDown(document, { key, metaKey: true })

    expect(openSearch).toHaveBeenCalledOnce()
  })
})

describe('feed refresh keyboard shortcut', () => {
  it('synchronizes papers with Command+R', () => {
    const refreshFeed = vi.fn()
    renderHook(() => useRefreshShortcut(refreshFeed))

    fireEvent.keyDown(document, { key: 'r', metaKey: true })

    expect(refreshFeed).toHaveBeenCalledOnce()
  })
})
