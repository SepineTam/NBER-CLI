import { invoke } from '@tauri-apps/api/core'
import type { Paper, PaperTag, PaperTagSource } from '../types'

export async function fetchPaper(paperId: string): Promise<Paper> {
  const paper = await invoke<Paper>('get_paper', { paperId })
  return {
    ...paper,
    authors: Array.isArray(paper?.authors) ? paper.authors : [],
    tags: Array.isArray(paper?.tags) ? paper.tags : [],
  }
}

export function setPaperReadStatus(paperId: string, isRead: boolean) {
  return invoke<{ paper_id: string; is_read: boolean }>('set_paper_read_status', {
    paperId,
    isRead,
  })
}

export function addPaperTag(paperId: string, tag: string) {
  return invoke<PaperTag[]>('add_paper_tag', { paperId, tag })
}

export function renamePaperTag(
  paperId: string,
  oldTag: string,
  newTag: string,
  source: PaperTagSource,
) {
  return invoke<PaperTag[]>('rename_paper_tag', {
    paperId,
    oldTag,
    newTag,
    source,
  })
}

export function removePaperTag(paperId: string, tag: string, source: PaperTagSource) {
  return invoke<PaperTag[]>('remove_paper_tag', { paperId, tag, source })
}
