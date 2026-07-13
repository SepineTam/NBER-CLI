import { useEffect } from 'react'
import { isTauri } from '@tauri-apps/api/core'
import { listen, type UnlistenFn } from '@tauri-apps/api/event'

const OPEN_SETTINGS_EVENT = 'open-settings'

export function useNativeMenu(openSettings: () => void) {
  useEffect(() => {
    if (!isTauri()) {
      return undefined
    }

    let disposed = false
    let unlisten: UnlistenFn | undefined

    void listen(OPEN_SETTINGS_EVENT, openSettings).then((stopListening) => {
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
  }, [openSettings])
}
