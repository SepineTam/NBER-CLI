import { invoke } from '@tauri-apps/api/core'
import type { Settings } from '../types'

export function fetchSettings() {
  return invoke<Settings>('get_settings')
}

export function saveSettings(input: {
  feed_refresh_interval_minutes?: number
}) {
  return invoke<Settings>('save_settings', {
    input: {
      feedRefreshIntervalMinutes: input.feed_refresh_interval_minutes,
    },
  })
}
