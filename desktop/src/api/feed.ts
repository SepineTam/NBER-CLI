import { invoke } from '@tauri-apps/api/core'
import type { FeedList, FeedRefreshResult } from '../types'

interface FetchFeedInput {
  limit?: number
  offset?: number
}

export function fetchFeed(input: FetchFeedInput = {}) {
  const { limit = 100, offset = 0 } = input
  return invoke<FeedList>('get_feed', { limit, offset })
}

export function refreshFeed() {
  return invoke<FeedRefreshResult>('refresh_feed')
}
