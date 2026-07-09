import { apiClient, unwrap } from './client'
import type { Paper } from '../types'

export function fetchPaper(paperId: string) {
  return unwrap<Paper>(apiClient.get(`/papers/${paperId}`))
}

export function setPaperReadStatus(paperId: string, isRead: boolean) {
  return unwrap<{ paper_id: string; is_read: boolean }>(
    apiClient.post(`/papers/${paperId}/mark-read`, { is_read: isRead }),
  )
}
