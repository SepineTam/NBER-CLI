import { apiClient, unwrap } from './client'
import type { FeedList, FeedRefreshResult } from '../types'

interface FetchFeedInput {
  limit?: number
  offset?: number
}

export function fetchFeed(input: FetchFeedInput = {}) {
  const { limit = 100, offset = 0 } = input
  return unwrap<FeedList>(apiClient.get('/feed', { params: { limit, offset } }))
}

export function refreshFeed() {
  return unwrap<FeedRefreshResult>(apiClient.post('/feed/refresh'))
}
