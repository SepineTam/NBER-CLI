import { describe, expect, it } from 'vitest'
import { autoRefreshIntervalMs, canAutoRefresh } from './autoRefresh'

describe('auto refresh helpers', () => {
  it('converts a positive minute interval into milliseconds', () => {
    expect(autoRefreshIntervalMs(15)).toBe(900_000)
    expect(autoRefreshIntervalMs(0)).toBeNull()
    expect(autoRefreshIntervalMs(undefined)).toBeNull()
  })

  it('only allows automatic refresh while the app is visible and local data is ready', () => {
    expect(canAutoRefresh('visible', true)).toBe(true)
    expect(canAutoRefresh('hidden', true)).toBe(false)
    expect(canAutoRefresh('visible', false)).toBe(false)
  })
})
