import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { openPath } from '@tauri-apps/plugin-opener'
import { useAppStore } from '../stores/appStore'

export function SettingsPage() {
  const { settings, savingSettings, loadSettings, updateSettings } = useAppStore()
  const [port, setPort] = useState('31527')
  const [interval, setIntervalValue] = useState('60')

  useEffect(() => {
    if (!settings) {
      void loadSettings()
      return
    }
    setPort(String(settings.server_port))
    setIntervalValue(String(settings.feed_refresh_interval_minutes))
  }, [loadSettings, settings])

  function submit(event: FormEvent) {
    event.preventDefault()
    void updateSettings({
      server_port: Number(port),
      feed_refresh_interval_minutes: Number(interval),
    })
  }

  return (
    <main className="settings-page">
      <header className="page-header">
        <div>
          <h1>设置</h1>
          <p>端口修改需要重启应用后生效。</p>
        </div>
      </header>

      <form className="settings-form" onSubmit={submit}>
        <label>
          <span>服务端口号</span>
          <input
            min={1024}
            max={65535}
            type="number"
            value={port}
            onChange={(event) => setPort(event.target.value)}
          />
        </label>
        <label>
          <span>Feed 刷新间隔（分钟）</span>
          <input
            min={1}
            type="number"
            value={interval}
            onChange={(event) => setIntervalValue(event.target.value)}
          />
        </label>
        <button className="primary-button" type="submit" disabled={savingSettings}>
          {savingSettings ? '保存中' : '保存设置'}
        </button>
      </form>

      {settings ? (
        <div className="settings-paths">
          <div>
            <strong>数据库</strong>
            <span>{settings.db_path}</span>
          </div>
          <div>
            <strong>配置文件</strong>
            <span>{settings.config_path}</span>
          </div>
          <button className="secondary-button" type="button" onClick={() => openPath(settings.log_dir)}>
            打开日志目录
          </button>
        </div>
      ) : null}
    </main>
  )
}
