export const DEFAULT_DETAIL_PANE_WIDTH = 420
export const MIN_DETAIL_PANE_WIDTH = 360
export const MAX_DETAIL_PANE_WIDTH = 640
export const MIN_FEED_PANE_WIDTH = 440
export const WORKSPACE_RESIZE_HANDLE_WIDTH = 8
export const DETAIL_PANE_WIDTH_STORAGE_KEY = 'nber-desktop-detail-pane-width'

export function clampDetailPaneWidth(requestedWidth: number, workspaceWidth = Number.POSITIVE_INFINITY) {
  const availableMaximum = Number.isFinite(workspaceWidth)
    ? workspaceWidth - MIN_FEED_PANE_WIDTH - WORKSPACE_RESIZE_HANDLE_WIDTH
    : MAX_DETAIL_PANE_WIDTH
  const maximum = Math.max(
    MIN_DETAIL_PANE_WIDTH,
    Math.min(MAX_DETAIL_PANE_WIDTH, availableMaximum),
  )
  return Math.min(maximum, Math.max(MIN_DETAIL_PANE_WIDTH, Math.round(requestedWidth)))
}

export function readStoredDetailPaneWidth(storage: Pick<Storage, 'getItem'> | null = null) {
  const stored = storage?.getItem(DETAIL_PANE_WIDTH_STORAGE_KEY)
  const parsed = stored ? Number(stored) : Number.NaN
  return Number.isFinite(parsed)
    ? clampDetailPaneWidth(parsed)
    : DEFAULT_DETAIL_PANE_WIDTH
}
