import { fireEvent, renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { usePaperSearchShortcuts } from './keyboardShortcuts'

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
