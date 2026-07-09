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
    <div className="app-shell">
      <Sidebar activeView={activeView} onChange={setActiveView} />
      <div className="main-shell">
        <div className="status-strip">
          <span className={sidecar?.ready ? 'status-dot ready' : 'status-dot'} />
          <span>{sidecar?.ready ? '本地服务已连接' : '正在连接本地服务'}</span>
        </div>

        {error ? <div className="banner error-banner">{error}</div> : null}
        {notice ? <div className="banner notice-banner">{notice}</div> : null}

        {activeView === 'feed' ? <FeedPage /> : <SettingsPage />}
      </div>
    </div>
  )
}

export default App
