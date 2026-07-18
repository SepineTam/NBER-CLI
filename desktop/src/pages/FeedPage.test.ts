import { describe, expect, it } from 'vitest'
import { collectAvailableTags, filterFeedItems } from './FeedPage'
import type { FeedItem } from '../types'

const items: FeedItem[] = [
  makeItem('w1', false, ['Labor Economics', 'Must Read']),
  makeItem('w2', true, ['Macroeconomics']),
]

describe('FeedPage tag filtering', () => {
  it('searches tag names and filters by an exact selected tag', () => {
    expect(filterFeedItems(items, 'all', 'labor', '')).toEqual([items[0]])
    expect(filterFeedItems(items, 'all', '', 'Macroeconomics')).toEqual([items[1]])
    expect(filterFeedItems(items, 'unread', '', 'Macroeconomics')).toEqual([])
  })

  it('collects unique sorted tag options', () => {
    expect(collectAvailableTags(items)).toEqual([
      'Labor Economics',
      'Macroeconomics',
      'Must Read',
    ])
  })
})

function makeItem(paperId: string, isRead: boolean, tags: string[]): FeedItem {
  return {
    paper_id: paperId,
    title: `Paper ${paperId}`,
    authors: ['Author'],
    abstract: 'Abstract',
    url: `https://www.nber.org/papers/${paperId}`,
    source_url: `https://www.nber.org/papers/${paperId}#rss`,
    guid: paperId,
    first_seen_at: '2026-07-19T00:00:00Z',
    last_seen_at: '2026-07-19T00:00:00Z',
    is_read: isRead,
    tags: tags.map((name) => ({ name, source: 'user' })),
  }
}
