import { useCallback, useEffect } from 'react'
import type { CSSProperties } from 'react'
import './App.css'
import { Sidebar } from './components/Sidebar'
import { FeedPage } from './pages/FeedPage'
import { SettingsPage } from './pages/SettingsPage'
import { useAppStore } from './stores/appStore'
import { autoRefreshIntervalMs, canAutoRefresh } from './autoRefresh'
import { useNativeMenu } from './nativeMenu'
import {
  PAPER_SEARCH_INPUT_ID,
  useOpenFeedShortcut,
  usePaperSearchShortcuts,
  useRefreshShortcut,
} from './keyboardShortcuts'

function App() {
  const { activeView, setActiveView, boot, error, notice, refresh, settings, localReady } = useAppStore()
  const openFeed = useCallback(() => setActiveView('feed'), [setActiveView])
  const openSettings = useCallback(() => setActiveView('settings'), [setActiveView])
  const openSearch = useCallback(() => {
    setActiveView('feed')
    window.requestAnimationFrame(() => {
      document.getElementById(PAPER_SEARCH_INPUT_ID)?.focus()
    })
  }, [setActiveView])
  const refreshFeed = useCallback(() => {
    void refresh()
  }, [refresh])

  useNativeMenu({ openFeed, openSearch, openSettings, refreshFeed })
  useOpenFeedShortcut(openFeed)
  usePaperSearchShortcuts(openSearch)
  useRefreshShortcut(refreshFeed)

  useEffect(() => {
    void boot()
  }, [boot])

  useEffect(() => {
    const intervalMs = autoRefreshIntervalMs(settings?.feed_refresh_interval_minutes)
    if (!localReady || intervalMs === null) {
      return undefined
    }

    const timer = window.setInterval(() => {
      const state = useAppStore.getState()
      if (state.refreshing || !canAutoRefresh(document.visibilityState, state.localReady)) {
        return
      }
      void state.refresh()
    }, intervalMs)

    return () => window.clearInterval(timer)
  }, [settings?.feed_refresh_interval_minutes, localReady])

  return (
    <div
      className={`app-shell ${activeView === 'settings' ? 'settings-view' : ''}`}
      style={{ '--detail-font-size': `${settings?.detail_font_size ?? 16}px` } as CSSProperties}
    >
      <Sidebar
        activeView={activeView}
        onChange={setActiveView}
        localReady={localReady}
      />
      <div className="main-shell">
        <div className="app-notifications" aria-live="polite">
          {error ? <div className="banner error-banner" role="alert">{error}</div> : null}
          {notice ? <div className="banner notice-banner">{notice}</div> : null}
        </div>

        {activeView === 'feed' ? <FeedPage /> : <SettingsPage />}
      </div>
    </div>
  )
}

export default App
