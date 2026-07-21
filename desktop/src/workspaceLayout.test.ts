import { describe, expect, it } from 'vitest'
import {
  DEFAULT_DETAIL_PANE_WIDTH,
  MAX_DETAIL_PANE_WIDTH,
  MIN_DETAIL_PANE_WIDTH,
  clampDetailPaneWidth,
  readStoredDetailPaneWidth,
} from './workspaceLayout'

describe('workspace detail pane sizing', () => {
  it('keeps the requested width inside desktop limits', () => {
    expect(clampDetailPaneWidth(200)).toBe(MIN_DETAIL_PANE_WIDTH)
    expect(clampDetailPaneWidth(520.4)).toBe(520)
    expect(clampDetailPaneWidth(900)).toBe(MAX_DETAIL_PANE_WIDTH)
  })

  it('preserves the minimum feed width in a smaller workspace', () => {
    expect(clampDetailPaneWidth(600, 960)).toBe(512)
    expect(clampDetailPaneWidth(500, 760)).toBe(MIN_DETAIL_PANE_WIDTH)
  })

  it('loads a valid stored width and ignores invalid storage', () => {
    expect(readStoredDetailPaneWidth({ getItem: () => '510' })).toBe(510)
    expect(readStoredDetailPaneWidth({ getItem: () => 'invalid' })).toBe(DEFAULT_DETAIL_PANE_WIDTH)
    expect(readStoredDetailPaneWidth()).toBe(DEFAULT_DETAIL_PANE_WIDTH)
  })
})
