import type { FeedItem } from '../types'

interface FeedItemRowProps {
  item: FeedItem
  selected: boolean
  onOpen: (paperId: string) => void
}

export function FeedItemRow({ item, selected, onOpen }: FeedItemRowProps) {
  return (
    <button
      className={`feed-row ${selected ? 'selected' : ''} ${item.is_read ? 'read' : 'unread'}`}
      type="button"
      onClick={() => onOpen(item.paper_id)}
    >
      <span className="read-dot" aria-label={item.is_read ? '已读' : '未读'} />
      <span className="paper-main">
        <strong>{item.title}</strong>
        <span>{formatAuthors(item.authors)}</span>
      </span>
      <span className="paper-date">{formatDate(item.last_seen_at)}</span>
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

function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value.slice(0, 10)
  }
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date)
}
