import type { FeedItem } from '../types'
import { FeedItemRow } from './FeedItemRow'

interface FeedListProps {
  items: FeedItem[]
  totalCount: number
  loading: boolean
  loadingMore: boolean
  selectedPaperId: string | null
  onOpenPaper: (paperId: string) => void
  onLoadMore: () => void
}

export function FeedList({
  items,
  totalCount,
  loading,
  loadingMore,
  selectedPaperId,
  onOpenPaper,
  onLoadMore,
}: FeedListProps) {
  if (loading) {
    return (
      <div className="feed-list skeleton-list" aria-label="正在获取最新论文">
        {Array.from({ length: 7 }).map((_, index) => (
          <div className="skeleton-row" key={index} />
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="empty-state">
        <strong>暂无论文</strong>
        <span>点击刷新获取最新 NBER working papers。</span>
      </div>
    )
  }

  const hasMore = items.length < totalCount

  return (
    <div className="feed-list">
      {items.map((item) => (
        <FeedItemRow
          item={item}
          key={item.paper_id}
          selected={selectedPaperId === item.paper_id}
          onOpen={onOpenPaper}
        />
      ))}
      {hasMore ? (
        <div className="load-more-row">
          <button className="secondary-button" type="button" onClick={onLoadMore} disabled={loadingMore}>
            {loadingMore ? '加载中' : `加载更多（${items.length}/${totalCount}）`}
          </button>
        </div>
      ) : null}
    </div>
  )
}
