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

  it('opens settings when the native menu event is received', async () => {
    const openSettings = vi.fn()
    const stopListening = vi.fn<UnlistenFn>()
    let eventCallback: EventCallback<unknown> | undefined

    listenMock.mockImplementation(async (event, callback) => {
      expect(event).toBe('open-settings')
      eventCallback = callback as EventCallback<unknown>
      return stopListening
    })

    const { unmount } = renderHook(() => useNativeMenu(openSettings))
    await act(async () => undefined)

    act(() => {
      eventCallback?.({ event: 'open-settings', id: 1, payload: null } as Event<unknown>)
    })

    expect(openSettings).toHaveBeenCalledOnce()
    unmount()
    expect(stopListening).toHaveBeenCalledOnce()
  })

  it('does not register native events in a regular browser', () => {
    isTauriMock.mockReturnValue(false)

    renderHook(() => useNativeMenu(vi.fn()))

    expect(listenMock).not.toHaveBeenCalled()
  })
})
