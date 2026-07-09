interface SidebarProps {
  activeView: 'feed' | 'settings'
  onChange: (view: 'feed' | 'settings') => void
}

export function Sidebar({ activeView, onChange }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">N</div>
        <div>
          <strong>NBER-CLI Desktop</strong>
          <span>Working Papers</span>
        </div>
      </div>

      <nav className="nav">
        <button
          className={activeView === 'feed' ? 'active' : ''}
          type="button"
          onClick={() => onChange('feed')}
        >
          Feed
        </button>
        <button
          className={activeView === 'settings' ? 'active' : ''}
          type="button"
          onClick={() => onChange('settings')}
        >
          设置
        </button>
      </nav>
    </aside>
  )
}
