const MINUTE_MS = 60_000

export function autoRefreshIntervalMs(intervalMinutes: number | null | undefined) {
  if (!Number.isFinite(intervalMinutes) || intervalMinutes === null || intervalMinutes === undefined) {
    return null
  }
  if (intervalMinutes <= 0) {
    return null
  }
  return Math.max(1, Math.round(intervalMinutes)) * MINUTE_MS
}

export function canAutoRefresh(visibilityState: DocumentVisibilityState, localReady: boolean) {
  return localReady && visibilityState === 'visible'
}
