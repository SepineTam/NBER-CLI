import { useEffect } from 'react'
import { invoke } from '@tauri-apps/api/core'
import './App.css'
import { Sidebar } from './components/Sidebar'
import { FeedPage } from './pages/FeedPage'
import { SettingsPage } from './pages/SettingsPage'
import { useAppStore } from './stores/appStore'
import { autoRefreshIntervalMs, canAutoRefresh } from './autoRefresh'

function App() {
  const { activeView, setActiveView, boot, error, notice, settings, sidecar } = useAppStore()

  useEffect(() => {
    void boot()
    return () => {
      void invoke('stop_sidecar').catch(() => undefined)
    }
  }, [boot])

  useEffect(() => {
    const intervalMs = autoRefreshIntervalMs(settings?.feed_refresh_interval_minutes)
    if (!sidecar?.ready || intervalMs === null) {
      return undefined
    }

    const timer = window.setInterval(() => {
      const state = useAppStore.getState()
      if (state.refreshing || !canAutoRefresh(document.visibilityState, Boolean(state.sidecar?.ready))) {
        return
      }
      void state.refresh()
    }, intervalMs)

    return () => window.clearInterval(timer)
  }, [settings?.feed_refresh_interval_minutes, sidecar?.ready])

  return (
    <div className={`app-shell ${activeView === 'settings' ? 'settings-view' : ''}`}>
      <Sidebar
        activeView={activeView}
        onChange={setActiveView}
        sidecarReady={Boolean(sidecar?.ready)}
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
