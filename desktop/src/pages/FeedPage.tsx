import { useEffect, useMemo, useRef, useState } from 'react'
import { FeedList } from '../components/FeedList'
import { PaperDetail } from '../components/PaperDetail'
import { RefreshButton } from '../components/RefreshButton'
import { SearchIcon } from '../components/Icons'
import { useAppStore } from '../stores/appStore'

type FeedFilter = 'all' | 'unread'

export function FeedPage() {
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<FeedFilter>('all')
  const searchRef = useRef<HTMLInputElement>(null)
  const {
    feedItems,
    feedTotalCount,
    loadingFeed,
    loadingMoreFeed,
    refreshing,
    selectedPaperId,
    selectedPaper,
    paperError,
    loadingPaper,
    lastUpdatedAt,
    refresh,
    loadMoreFeed,
    openPaper,
    closePaper,
    toggleRead,
  } = useAppStore()

  useEffect(() => {
    function focusSearch(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        searchRef.current?.focus()
      }
    }
    document.addEventListener('keydown', focusSearch)
    return () => document.removeEventListener('keydown', focusSearch)
  }, [])

  const unreadCount = feedItems.filter((item) => !item.is_read).length
  const visibleItems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    return feedItems.filter((item) => {
      const matchesFilter = filter === 'all' || !item.is_read
      const matchesQuery =
        !normalizedQuery ||
        item.title.toLowerCase().includes(normalizedQuery) ||
        item.paper_id.toLowerCase().includes(normalizedQuery) ||
        item.authors.some((author) => author.toLowerCase().includes(normalizedQuery))
      return matchesFilter && matchesQuery
    })
  }, [feedItems, filter, query])

  return (
    <main className="workspace">
      <section className="feed-panel">
        <header className="feed-header">
          <p className="eyebrow">Research desk · 研究工作台</p>
          <div className="title-row">
            <h1>Working Papers</h1>
            <div className="issue-meta">
              <strong>{formatWeek()}</strong>
              <span>{feedTotalCount} papers indexed locally</span>
            </div>
          </div>

          <div className="toolbar">
            <label className="feed-search">
              <SearchIcon />
              <input
                ref={searchRef}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="搜索标题、作者或论文编号"
              />
              <kbd>⌘ K</kbd>
            </label>
            <RefreshButton refreshing={refreshing} onRefresh={() => void refresh()} />
          </div>

          <div className="feed-status">
            <span>{lastUpdatedAt ? `上次同步：${formatRelative(lastUpdatedAt)}` : '等待首次同步'}</span>
          </div>
        </header>

        <div className="filter-row" role="tablist" aria-label="论文筛选">
          <button className={filter === 'all' ? 'active' : ''} type="button" onClick={() => setFilter('all')}>
            全部 <span>{feedItems.length}</span>
          </button>
          <button className={filter === 'unread' ? 'active' : ''} type="button" onClick={() => setFilter('unread')}>
            未读 <span>{unreadCount}</span>
          </button>
        </div>

        <FeedList
          items={visibleItems}
          totalCount={query || filter !== 'all' ? visibleItems.length : feedTotalCount}
          loading={loadingFeed}
          loadingMore={loadingMoreFeed}
          selectedPaperId={selectedPaperId}
          onOpenPaper={(paperId) => void openPaper(paperId)}
          onLoadMore={() => void loadMoreFeed()}
        />
      </section>
      <PaperDetail
        paperId={selectedPaperId}
        paper={selectedPaper}
        error={paperError}
        loading={loadingPaper}
        onClose={closePaper}
        onRetry={(paperId) => void openPaper(paperId)}
        onToggleRead={(paperId, isRead) => void toggleRead(paperId, isRead)}
      />
    </main>
  )
}

function formatWeek() {
  const date = new Date()
  const firstDay = new Date(Date.UTC(date.getUTCFullYear(), 0, 1))
  const dayOffset = (date.getUTCDay() + 6) % 7
  const thursday = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() - dayOffset + 3))
  const week = 1 + Math.round((thursday.getTime() - firstDay.getTime()) / 604_800_000)
  return `${date.getFullYear()} · Week ${week}`
}

function formatRelative(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  const minutes = Math.max(0, Math.round((Date.now() - date.getTime()) / 60000))
  if (minutes < 1) {
    return '刚刚'
  }
  if (minutes < 60) {
    return `${minutes} 分钟前`
  }
  const hours = Math.round(minutes / 60)
  if (hours < 24) {
    return `${hours} 小时前`
  }
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}
