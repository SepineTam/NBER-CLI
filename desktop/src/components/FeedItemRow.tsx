import type { FeedItem } from '../types'

interface FeedItemRowProps {
  item: FeedItem
  selected: boolean
  onOpen: (paperId: string) => void
}

export function FeedItemRow({ item, selected, onOpen }: FeedItemRowProps) {
  return (
    <button
      className={`paper-card ${selected ? 'selected' : ''} ${item.is_read ? 'read' : 'unread'}`}
      type="button"
      onClick={() => onOpen(item.paper_id)}
    >
      <span className="read-dot" aria-label={item.is_read ? '已读' : '未读'} />
      <span className="paper-main">
        <strong className="paper-title">{item.title}</strong>
        <span className="paper-authors">{formatAuthors(item.authors)}</span>
      </span>
      <time className="paper-time">{formatTime(item.last_seen_at)}</time>
    </button>
  )
}

function formatAuthors(authors: string[]) {
  if (authors.length === 0) {
    return 'Unknown authors'
  }
  if (authors.length <= 3) {
    return authors.join(', ')
  }
  return `${authors.slice(0, 3).join(', ')} et al.`
}

function formatTime(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value.slice(0, 10)
  }
  return new Intl.DateTimeFormat(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}
