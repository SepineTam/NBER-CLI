import { beforeEach, describe, expect, it, vi } from 'vitest'

const { invokeMock } = vi.hoisted(() => ({ invokeMock: vi.fn() }))

vi.mock('@tauri-apps/api/core', () => ({ invoke: invokeMock }))

import { fetchFeed, refreshFeed } from './feed'
import { fetchPaper, setPaperReadStatus } from './papers'
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

  it('loads and saves native settings without a service port', async () => {
    invokeMock.mockResolvedValue({ feed_refresh_interval_minutes: 45 })

    await fetchSettings()
    await saveSettings({ feed_refresh_interval_minutes: 45 })

    expect(invokeMock).toHaveBeenNthCalledWith(1, 'get_settings')
    expect(invokeMock).toHaveBeenNthCalledWith(2, 'save_settings', {
      input: { feedRefreshIntervalMinutes: 45 },
    })
  })
})
