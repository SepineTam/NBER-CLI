import { invoke } from '@tauri-apps/api/core'
import type { Paper } from '../types'

export function fetchPaper(paperId: string) {
  return invoke<Paper>('get_paper', { paperId })
}

export function setPaperReadStatus(paperId: string, isRead: boolean) {
  return invoke<{ paper_id: string; is_read: boolean }>('set_paper_read_status', {
    paperId,
    isRead,
  })
}
