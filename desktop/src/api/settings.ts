import { apiClient, unwrap } from './client'
import type { Settings } from '../types'

export function fetchSettings() {
  return unwrap<Settings>(apiClient.get('/settings'))
}

export function saveSettings(input: {
  server_port?: number
  feed_refresh_interval_minutes?: number
}) {
  return unwrap<Settings>(apiClient.patch('/settings', input))
}
