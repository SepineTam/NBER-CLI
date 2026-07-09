interface RefreshButtonProps {
  refreshing: boolean
  onRefresh: () => void
}

export function RefreshButton({ refreshing, onRefresh }: RefreshButtonProps) {
  return (
    <button className="primary-button" type="button" onClick={onRefresh} disabled={refreshing}>
      <span aria-hidden="true">{refreshing ? '↻' : '⟳'}</span>
      {refreshing ? '刷新中' : '刷新'}
    </button>
  )
}
