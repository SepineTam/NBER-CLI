import { Fragment } from 'react'
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
      {items.map((item, index) => {
        const dayKey = dateKey(item.last_seen_at)
        const previousDayKey = index > 0 ? dateKey(items[index - 1].last_seen_at) : null
        return (
          <Fragment key={item.paper_id}>
            {dayKey !== previousDayKey ? <div className="date-label">{formatDay(item.last_seen_at)}</div> : null}
            <FeedItemRow
              item={item}
              selected={selectedPaperId === item.paper_id}
              onOpen={onOpenPaper}
            />
          </Fragment>
        )
      })}
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

function dateKey(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value.slice(0, 10) : date.toISOString().slice(0, 10)
}

function formatDay(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value.slice(0, 10)
  }
  const today = new Date()
  const todayKey = dateKey(today.toISOString())
  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  const prefix = dateKey(value) === todayKey ? '今天' : dateKey(value) === dateKey(yesterday.toISOString()) ? '昨天' : ''
  const formatted = new Intl.DateTimeFormat('zh-CN', { month: 'long', day: 'numeric' }).format(date)
  return prefix ? `${prefix} · ${formatted}` : formatted
}
