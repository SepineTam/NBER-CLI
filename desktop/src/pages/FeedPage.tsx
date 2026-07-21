import { useMemo, useState } from 'react'
import { FeedList } from '../components/FeedList'
import { PaperDetail } from '../components/PaperDetail'
import { RefreshButton } from '../components/RefreshButton'
import { SearchIcon } from '../components/Icons'
import { useAppStore } from '../stores/appStore'
import type { FeedItem } from '../types'
import { PAPER_SEARCH_INPUT_ID } from '../keyboardShortcuts'

type FeedFilter = 'all' | 'unread'

export function FeedPage() {
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<FeedFilter>('all')
  const [tagFilter, setTagFilter] = useState('')
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
    addTag,
    renameTag,
    removeTag,
  } = useAppStore()

  const unreadCount = feedItems.filter((item) => !item.is_read).length
  const availableTags = useMemo(
    () => collectAvailableTags(feedItems),
    [feedItems],
  )
  const visibleItems = useMemo(
    () => filterFeedItems(feedItems, filter, query, tagFilter),
    [feedItems, filter, query, tagFilter],
  )

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
                id={PAPER_SEARCH_INPUT_ID}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="搜索标题、作者、编号或标签"
              />
              <kbd>⌘ K</kbd>
            </label>
            <RefreshButton refreshing={refreshing} onRefresh={() => void refresh()} />
          </div>

          <div className="feed-status">
            <span>{lastUpdatedAt ? `上次同步：${formatRelative(lastUpdatedAt)}` : '等待首次同步'}</span>
          </div>
        </header>

        <div className="filter-row" role="group" aria-label="论文筛选">
          <button
            aria-pressed={filter === 'all'}
            className={filter === 'all' ? 'active' : ''}
            type="button"
            onClick={() => setFilter('all')}
          >
            全部 <span>{feedItems.length}</span>
          </button>
          <button
            aria-pressed={filter === 'unread'}
            className={filter === 'unread' ? 'active' : ''}
            type="button"
            onClick={() => setFilter('unread')}
          >
            未读 <span>{unreadCount}</span>
          </button>
          <label className="tag-filter">
            <span>标签</span>
            <select value={tagFilter} onChange={(event) => setTagFilter(event.target.value)}>
              <option value="">全部标签</option>
              {availableTags.map((tag) => <option value={tag} key={tag}>{tag}</option>)}
            </select>
          </label>
        </div>

        <FeedList
          items={visibleItems}
          totalCount={query || filter !== 'all' || tagFilter ? visibleItems.length : feedTotalCount}
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
        onAddTag={addTag}
        onRenameTag={renameTag}
        onRemoveTag={removeTag}
      />
    </main>
  )
}

export function collectAvailableTags(items: FeedItem[]) {
  return Array.from(new Set(items.flatMap((item) => item.tags.map((tag) => tag.name))))
    .sort((left, right) => left.localeCompare(right))
}

export function filterFeedItems(
  items: FeedItem[],
  filter: FeedFilter,
  query: string,
  tagFilter: string,
) {
  const normalizedQuery = query.trim().toLowerCase()
  return items.filter((item) => {
    const matchesFilter = filter === 'all' || !item.is_read
    const matchesQuery =
      !normalizedQuery ||
      item.title.toLowerCase().includes(normalizedQuery) ||
      item.paper_id.toLowerCase().includes(normalizedQuery) ||
      item.authors.some((author) => author.toLowerCase().includes(normalizedQuery)) ||
      item.tags.some((tag) => tag.name.toLowerCase().includes(normalizedQuery))
    const matchesTag = !tagFilter || item.tags.some((tag) => tag.name === tagFilter)
    return matchesFilter && matchesQuery && matchesTag
  })
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
