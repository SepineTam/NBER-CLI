import { invoke } from '@tauri-apps/api/core'
import type { FeedItem, FeedList, FeedRefreshResult } from '../types'

interface FetchFeedInput {
  limit?: number
  offset?: number
}

export async function fetchFeed(input: FetchFeedInput = {}): Promise<FeedList> {
  const { limit = 100, offset = 0 } = input
  const feed = await invoke<Partial<FeedList>>('get_feed', { limit, offset })
  const items = Array.isArray(feed?.items) ? feed.items.map(normalizeFeedItem) : []
  return {
    items,
    total_count: typeof feed?.total_count === 'number' ? feed.total_count : items.length,
    limit: typeof feed?.limit === 'number' ? feed.limit : limit,
    offset: typeof feed?.offset === 'number' ? feed.offset : offset,
    last_successful_fetch_at: feed?.last_successful_fetch_at ?? null,
  }
}

export function refreshFeed() {
  return invoke<FeedRefreshResult>('refresh_feed')
}

function normalizeFeedItem(item: FeedItem): FeedItem {
  return {
    ...item,
    authors: Array.isArray(item?.authors) ? item.authors : [],
    tags: Array.isArray(item?.tags) ? item.tags : [],
  }
}
