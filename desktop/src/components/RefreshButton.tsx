import { RefreshIcon } from './Icons'

interface RefreshButtonProps {
  refreshing: boolean
  onRefresh: () => void
}

export function RefreshButton({ refreshing, onRefresh }: RefreshButtonProps) {
  return (
    <button
      aria-label={refreshing ? '正在同步' : '同步最新论文'}
      className={`refresh-button ${refreshing ? 'loading' : ''}`}
      type="button"
      onClick={onRefresh}
      disabled={refreshing}
    >
      <RefreshIcon />
      <span>{refreshing ? '正在同步' : '同步最新论文'}</span>
    </button>
  )
}
