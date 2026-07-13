import { useEffect } from 'react'
import { isTauri } from '@tauri-apps/api/core'
import { listen, type UnlistenFn } from '@tauri-apps/api/event'

export interface NativeMenuHandlers {
  openFeed: () => void
  openSearch: () => void
  openSettings: () => void
  refreshFeed: () => void
}

export function useNativeMenu({ openFeed, openSearch, openSettings, refreshFeed }: NativeMenuHandlers) {
  useNativeMenuEvent('open-feed', openFeed)
  useNativeMenuEvent('open-search', openSearch)
  useNativeMenuEvent('open-settings', openSettings)
  useNativeMenuEvent('refresh-feed', refreshFeed)
}

function useNativeMenuEvent(eventName: string, handler: () => void) {
  useEffect(() => {
    if (!isTauri()) {
      return undefined
    }

    let disposed = false
    let unlisten: UnlistenFn | undefined

    void listen(eventName, handler).then((stopListening) => {
      if (disposed) {
        stopListening()
      } else {
        unlisten = stopListening
      }
    })

    return () => {
      disposed = true
      unlisten?.()
    }
  }, [eventName, handler])
}
