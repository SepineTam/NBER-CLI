import { create } from 'zustand'
import { invoke } from '@tauri-apps/api/core'
import { fetchFeed, refreshFeed } from '../api/feed'
import { fetchHealth } from '../api/health'
import { fetchPaper, setPaperReadStatus } from '../api/papers'
import { fetchSettings, saveSettings } from '../api/settings'
import { readableError, setApiBaseUrl } from '../api/client'
import type {
  DesktopConfig,
  FeedItem,
  FeedRefreshResult,
  Paper,
  Settings,
  SidecarStatus,
} from '../types'

interface AppState {
  activeView: 'feed' | 'settings'
  config: DesktopConfig | null
  sidecar: SidecarStatus | null
  feedItems: FeedItem[]
  feedTotalCount: number
  selectedPaperId: string | null
  selectedPaper: Paper | null
  paperError: string | null
  settings: Settings | null
  loadingFeed: boolean
  loadingMoreFeed: boolean
  refreshing: boolean
  loadingPaper: boolean
  savingSettings: boolean
  error: string | null
  notice: string | null
  lastUpdatedAt: string | null
  setActiveView: (view: 'feed' | 'settings') => void
  boot: () => Promise<void>
  loadFeed: () => Promise<void>
  loadMoreFeed: () => Promise<void>
  refresh: () => Promise<FeedRefreshResult | null>
  openPaper: (paperId: string) => Promise<void>
  closePaper: () => void
  toggleRead: (paperId: string, isRead: boolean) => Promise<void>
  loadSettings: () => Promise<void>
  updateSettings: (settings: {
    server_port?: number
    feed_refresh_interval_minutes?: number
  }) => Promise<void>
}

export const useAppStore = create<AppState>((set, get) => ({
  activeView: 'feed',
  config: null,
  sidecar: null,
  feedItems: [],
  feedTotalCount: 0,
  selectedPaperId: null,
  selectedPaper: null,
  paperError: null,
  settings: null,
  loadingFeed: false,
  loadingMoreFeed: false,
  refreshing: false,
  loadingPaper: false,
  savingSettings: false,
  error: null,
  notice: null,
  lastUpdatedAt: null,

  setActiveView: (view) => set({ activeView: view, error: null, notice: null }),

  boot: async () => {
    try {
      const config = isTauriRuntime()
        ? await invoke<DesktopConfig>('get_config')
        : fallbackDesktopConfig()
      setApiBaseUrl(config.api_base_url)
      set({ config, error: null })
      const sidecar = isTauriRuntime()
        ? await invoke<SidecarStatus>('start_sidecar')
        : await browserSidecarStatus(config.server_port)
      set({ sidecar })
      await get().loadFeed()
      await get().loadSettings()
      if (get().feedItems.length === 0) {
        await get().refresh()
      }
    } catch (error) {
      set({ error: readableError(error) })
    }
  },

  loadFeed: async () => {
    set({ loadingFeed: true, error: null })
    try {
      const feed = await fetchFeed()
      set({
        feedItems: feed.items,
        feedTotalCount: feed.total_count,
        lastUpdatedAt: feed.last_successful_fetch_at,
        loadingFeed: false,
      })
    } catch (error) {
      set({ error: readableError(error), loadingFeed: false })
    }
  },

  loadMoreFeed: async () => {
    const state = get()
    if (state.loadingFeed || state.loadingMoreFeed || state.feedItems.length >= state.feedTotalCount) {
      return
    }

    set({ loadingMoreFeed: true, error: null })
    try {
      const feed = await fetchFeed({ limit: 50, offset: state.feedItems.length })
      set((current) => {
        const existingIds = new Set(current.feedItems.map((item) => item.paper_id))
        const nextItems = feed.items.filter((item) => !existingIds.has(item.paper_id))
        return {
          feedItems: [...current.feedItems, ...nextItems],
          feedTotalCount: feed.total_count,
          lastUpdatedAt: feed.last_successful_fetch_at,
          loadingMoreFeed: false,
        }
      })
    } catch (error) {
      set({ error: readableError(error), loadingMoreFeed: false })
    }
  },

  refresh: async () => {
    if (get().refreshing) {
      return null
    }
    set({ refreshing: true, error: null, notice: null })
    try {
      const result = await refreshFeed()
      await get().loadFeed()
      set({
        refreshing: false,
        notice: `新增 ${result.new_count} 篇，当前共 ${result.total_count} 篇`,
      })
      return result
    } catch (error) {
      set({ error: readableError(error), refreshing: false })
      return null
    }
  },

  openPaper: async (paperId) => {
    set({
      selectedPaperId: paperId,
      selectedPaper: null,
      paperError: null,
      loadingPaper: true,
      error: null,
    })
    try {
      const paper = await fetchPaper(paperId)
      set((state) => ({
        selectedPaper: paper,
        paperError: null,
        loadingPaper: false,
        feedItems: state.feedItems.map((item) =>
          item.paper_id === paperId ? { ...item, is_read: true } : item,
        ),
      }))
    } catch (error) {
      set({ paperError: readableError(error), loadingPaper: false })
    }
  },

  closePaper: () =>
    set({
      selectedPaperId: null,
      selectedPaper: null,
      paperError: null,
      loadingPaper: false,
    }),

  toggleRead: async (paperId, isRead) => {
    try {
      await setPaperReadStatus(paperId, isRead)
      set((state) => ({
        selectedPaper:
          state.selectedPaper?.paper_id === paperId
            ? { ...state.selectedPaper, is_read: isRead }
            : state.selectedPaper,
        feedItems: state.feedItems.map((item) =>
          item.paper_id === paperId ? { ...item, is_read: isRead } : item,
        ),
      }))
    } catch (error) {
      set({ error: readableError(error) })
    }
  },

  loadSettings: async () => {
    try {
      const settings = await fetchSettings()
      set({ settings })
    } catch (error) {
      set({ error: readableError(error) })
    }
  },

  updateSettings: async (input) => {
    set({ savingSettings: true, error: null, notice: null })
    try {
      const settings = await saveSettings(input)
      set({
        settings,
        savingSettings: false,
        notice: '设置已保存。端口修改将在重启后生效。',
      })
    } catch (error) {
      set({ error: readableError(error), savingSettings: false })
    }
  },
}))

function isTauriRuntime() {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window
}

function fallbackDesktopConfig(): DesktopConfig {
  return {
    server_port: 31527,
    feed_refresh_interval_minutes: 60,
    api_base_url: 'http://127.0.0.1:31527/api/v1',
    config_path: '',
    db_path: '',
    log_dir: '',
  }
}

async function browserSidecarStatus(port: number): Promise<SidecarStatus> {
  try {
    await fetchHealth()
    return {
      ready: true,
      port,
      message: 'local service is ready',
    }
  } catch {
    return {
      ready: false,
      port,
      message: 'local service is not reachable',
    }
  }
}
