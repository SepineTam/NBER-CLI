import { beforeEach, describe, expect, it, vi } from 'vitest'

const { invokeMock } = vi.hoisted(() => ({ invokeMock: vi.fn() }))

vi.mock('@tauri-apps/api/core', () => ({ invoke: invokeMock }))

import { fetchFeed, refreshFeed } from './feed'
import {
  addPaperTag,
  fetchPaper,
  removePaperTag,
  renamePaperTag,
  setPaperReadStatus,
} from './papers'
import { fetchSettings, saveSettings } from './settings'

describe('native desktop commands', () => {
  beforeEach(() => {
    invokeMock.mockReset()
  })

  it('loads and refreshes the feed through Rust', async () => {
    invokeMock.mockResolvedValue({ items: [] })

    await fetchFeed({ limit: 50, offset: 100 })
    await refreshFeed()

    expect(invokeMock).toHaveBeenNthCalledWith(1, 'get_feed', { limit: 50, offset: 100 })
    expect(invokeMock).toHaveBeenNthCalledWith(2, 'refresh_feed')
  })

  it('normalizes legacy feed records with missing arrays', async () => {
    invokeMock.mockResolvedValue({
      items: [{ paper_id: 'w12345', title: 'Legacy paper' }],
    })

    const feed = await fetchFeed()

    expect(feed.items[0]).toMatchObject({
      paper_id: 'w12345',
      authors: [],
      tags: [],
    })
    expect(feed.total_count).toBe(1)
  })

  it('loads paper details and writes read status through Rust', async () => {
    invokeMock.mockResolvedValue({ paper_id: 'w12345' })

    await fetchPaper('w12345')
    await setPaperReadStatus('w12345', false)

    expect(invokeMock).toHaveBeenNthCalledWith(1, 'get_paper', { paperId: 'w12345' })
    expect(invokeMock).toHaveBeenNthCalledWith(2, 'set_paper_read_status', {
      paperId: 'w12345',
      isRead: false,
    })
  })

  it('normalizes legacy paper details with missing arrays', async () => {
    invokeMock.mockResolvedValue({ paper_id: 'w12345', title: 'Legacy paper' })

    const paper = await fetchPaper('w12345')

    expect(paper).toMatchObject({
      paper_id: 'w12345',
      authors: [],
      tags: [],
    })
  })

  it('creates, renames, and removes paper tags through Rust', async () => {
    invokeMock.mockResolvedValue([])

    await addPaperTag('w12345', 'Must Read')
    await renamePaperTag('w12345', 'Must Read', 'Priority', 'user')
    await removePaperTag('w12345', 'Labor Economics', 'topic')

    expect(invokeMock).toHaveBeenNthCalledWith(1, 'add_paper_tag', {
      paperId: 'w12345',
      tag: 'Must Read',
    })
    expect(invokeMock).toHaveBeenNthCalledWith(2, 'rename_paper_tag', {
      paperId: 'w12345',
      oldTag: 'Must Read',
      newTag: 'Priority',
      source: 'user',
    })
    expect(invokeMock).toHaveBeenNthCalledWith(3, 'remove_paper_tag', {
      paperId: 'w12345',
      tag: 'Labor Economics',
      source: 'topic',
    })
  })

  it('loads and saves native settings without a service port', async () => {
    invokeMock.mockResolvedValue({ feed_refresh_interval_minutes: 45, detail_font_size: 18 })

    await fetchSettings()
    await saveSettings({ feed_refresh_interval_minutes: 45, detail_font_size: 18 })

    expect(invokeMock).toHaveBeenNthCalledWith(1, 'get_settings')
    expect(invokeMock).toHaveBeenNthCalledWith(2, 'save_settings', {
      input: { feedRefreshIntervalMinutes: 45, detailFontSize: 18 },
    })
  })
})
