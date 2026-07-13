import { useEffect } from 'react'
import { isTauri } from '@tauri-apps/api/core'
import { listen, type UnlistenFn } from '@tauri-apps/api/event'

export interface NativeMenuHandlers {
  openSearch: () => void
  openSettings: () => void
}

export function useNativeMenu({ openSearch, openSettings }: NativeMenuHandlers) {
  useNativeMenuEvent('open-search', openSearch)
  useNativeMenuEvent('open-settings', openSettings)
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
