import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { FeedItemRow } from './FeedItemRow'
import type { FeedItem } from '../types'

const item: FeedItem = {
  paper_id: 'w12345',
  title: 'A Useful Paper',
  authors: ['Ada Lovelace', 'Grace Hopper', 'Katherine Johnson', 'Mary Jackson'],
  abstract: 'Abstract',
  url: 'https://www.nber.org/papers/w12345',
  source_url: 'https://www.nber.org/papers/w12345#rss',
  guid: 'https://www.nber.org/papers/w12345',
  first_seen_at: '2026-07-08T00:00:00+00:00',
  last_seen_at: '2026-07-08T00:00:00+00:00',
  is_read: false,
}

describe('FeedItemRow', () => {
  it('renders title, truncated authors, and opens the paper', async () => {
    const onOpen = vi.fn()
    render(<FeedItemRow item={item} selected={false} onOpen={onOpen} />)

    expect(screen.getByText('A Useful Paper')).toBeInTheDocument()
    expect(screen.getByText('Ada Lovelace, Grace Hopper, Katherine Johnson et al.')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button'))

    expect(onOpen).toHaveBeenCalledWith('w12345')
  })
})
