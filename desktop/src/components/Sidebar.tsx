import brandLogo from '../../src-tauri/icons/128x128.png'
import { PapersIcon, SettingsIcon } from './Icons'

interface SidebarProps {
  activeView: 'feed' | 'settings'
  onChange: (view: 'feed' | 'settings') => void
  sidecarReady: boolean
}

export function Sidebar({ activeView, onChange, sidecarReady }: SidebarProps) {
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

      <div className={`local-state ${sidecarReady ? 'ready' : ''}`} title={sidecarReady ? 'Python Server 正在本机运行' : '正在连接本地服务'}>
        <i />
        <span>Local</span>
      </div>
    </aside>
  )
}
