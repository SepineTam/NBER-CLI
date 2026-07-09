import { FeedList } from '../components/FeedList'
import { PaperDetail } from '../components/PaperDetail'
import { RefreshButton } from '../components/RefreshButton'
import { useAppStore } from '../stores/appStore'

export function FeedPage() {
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

  return (
    <main className="workspace">
      <section className="feed-panel">
        <header className="page-header">
          <div>
            <h1>Feed</h1>
            <p>{lastUpdatedAt ? `上次更新：${formatRelative(lastUpdatedAt)}` : '等待首次刷新'}</p>
          </div>
          <RefreshButton refreshing={refreshing} onRefresh={() => void refresh()} />
        </header>
        <FeedList
          items={feedItems}
          totalCount={feedTotalCount}
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
