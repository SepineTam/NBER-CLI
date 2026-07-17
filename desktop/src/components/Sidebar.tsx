import brandLogo from '../../src-tauri/icons/128x128.png'
import { PapersIcon, SettingsIcon } from './Icons'

interface SidebarProps {
  activeView: 'feed' | 'settings'
  onChange: (view: 'feed' | 'settings') => void
  localReady: boolean
}

export function Sidebar({ activeView, onChange, localReady }: SidebarProps) {
  return (
    <aside className="sidebar" aria-label="主导航">
      <button className="brand-button" type="button" onClick={() => onChange('feed')} aria-label="NBER Desktop 首页">
        <img src={brandLogo} alt="" />
      </button>

      <nav className="nav">
        <button
          className={`nav-button ${activeView === 'feed' ? 'active' : ''}`}
          type="button"
          onClick={() => onChange('feed')}
          aria-label="论文流"
          title="论文流"
        >
          <PapersIcon />
        </button>
      </nav>

      <div className="sidebar-spacer" />

      <button
        className={`nav-button ${activeView === 'settings' ? 'active' : ''}`}
        type="button"
        onClick={() => onChange('settings')}
        aria-label="设置"
        title="设置"
      >
        <SettingsIcon />
      </button>

      <div className={`local-state ${localReady ? 'ready' : ''}`} title={localReady ? 'Rust 本地数据引擎已就绪' : '正在准备本地数据'}>
        <i />
        <span>Local</span>
      </div>
    </aside>
  )
}
