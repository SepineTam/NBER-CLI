import { act, renderHook } from '@testing-library/react'
import type { Event, EventCallback, UnlistenFn } from '@tauri-apps/api/event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { isTauri } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { useNativeMenu } from './nativeMenu'

vi.mock('@tauri-apps/api/core', () => ({
  isTauri: vi.fn(),
}))

vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn(),
}))

const isTauriMock = vi.mocked(isTauri)
const listenMock = vi.mocked(listen)

describe('useNativeMenu', () => {
  beforeEach(() => {
    isTauriMock.mockReturnValue(true)
    listenMock.mockReset()
  })

  it.each([
    ['open-search', 'openSearch'],
    ['open-settings', 'openSettings'],
    ['refresh-feed', 'refreshFeed'],
  ] as const)('handles the %s native menu event', async (eventName, handlerName) => {
    const openSearch = vi.fn()
    const openSettings = vi.fn()
    const refreshFeed = vi.fn()
    const stopListening = vi.fn<UnlistenFn>()
    const eventCallbacks = new Map<string, EventCallback<unknown>>()

    listenMock.mockImplementation(async (event, callback) => {
      eventCallbacks.set(event, callback as EventCallback<unknown>)
      return stopListening
    })

    const { unmount } = renderHook(() => useNativeMenu({ openSearch, openSettings, refreshFeed }))
    await act(async () => undefined)

    act(() => {
      eventCallbacks.get(eventName)?.({ event: eventName, id: 1, payload: null } as Event<unknown>)
    })

    expect({ openSearch, openSettings, refreshFeed }[handlerName]).toHaveBeenCalledOnce()
    unmount()
    expect(stopListening).toHaveBeenCalledTimes(3)
  })

  it('does not register native events in a regular browser', () => {
    isTauriMock.mockReturnValue(false)

    renderHook(() => useNativeMenu({
      openSearch: vi.fn(),
      openSettings: vi.fn(),
      refreshFeed: vi.fn(),
    }))

    expect(listenMock).not.toHaveBeenCalled()
  })
})
