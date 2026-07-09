import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { FeedList } from './FeedList'
import type { FeedItem } from '../types'

const items: FeedItem[] = [
  makeFeedItem('w12345', 'First Paper'),
  makeFeedItem('w12346', 'Second Paper'),
]

describe('FeedList', () => {
  it('renders a load more button when more feed items are available', async () => {
    const onLoadMore = vi.fn()
    render(
      <FeedList
        items={items}
        totalCount={3}
        loading={false}
        loadingMore={false}
        selectedPaperId={null}
        onOpenPaper={vi.fn()}
        onLoadMore={onLoadMore}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: '加载更多（2/3）' }))

    expect(onLoadMore).toHaveBeenCalledOnce()
  })

  it('hides the load more button when all feed items are loaded', () => {
    render(
      <FeedList
        items={items}
        totalCount={2}
        loading={false}
        loadingMore={false}
        selectedPaperId={null}
        onOpenPaper={vi.fn()}
        onLoadMore={vi.fn()}
      />,
    )

    expect(screen.queryByRole('button', { name: /加载更多/ })).not.toBeInTheDocument()
  })
})

function makeFeedItem(paperId: string, title: string): FeedItem {
  return {
    paper_id: paperId,
    title,
    authors: ['Ada Lovelace'],
    abstract: 'Abstract',
    url: `https://www.nber.org/papers/${paperId}`,
    source_url: `https://www.nber.org/papers/${paperId}#rss`,
    guid: `https://www.nber.org/papers/${paperId}`,
    first_seen_at: '2026-07-08T00:00:00+00:00',
    last_seen_at: '2026-07-08T00:00:00+00:00',
    is_read: false,
  }
}
