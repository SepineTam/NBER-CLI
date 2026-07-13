import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { openPath } from '@tauri-apps/plugin-opener'
import { DatabaseIcon, FolderIcon } from '../components/Icons'
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
      <header className="settings-header">
        <p className="eyebrow">Local control · 本地控制</p>
        <div className="title-row">
          <h1>设置</h1>
          <p>配置只保存在这台设备上</p>
        </div>
      </header>

      <div className="settings-grid">
        <form className="settings-card settings-form" onSubmit={submit}>
          <div className="settings-card-heading">
            <span>01</span>
            <div>
              <strong>运行参数</strong>
              <p>端口修改需要重启应用后生效。</p>
            </div>
          </div>

          <label>
            <span>本地服务端口</span>
            <input
              min={1024}
              max={65535}
              type="number"
              value={port}
              onChange={(event) => setPort(event.target.value)}
            />
          </label>
          <label>
            <span>论文同步间隔</span>
            <div className="input-with-unit">
              <input
                min={1}
                type="number"
                value={interval}
                onChange={(event) => setIntervalValue(event.target.value)}
              />
              <em>分钟</em>
            </div>
          </label>
          <button className="settings-save" type="submit" disabled={savingSettings}>
            {savingSettings ? '正在保存' : '保存设置'}
          </button>
        </form>

        {settings ? (
          <section className="settings-card settings-paths">
            <div className="settings-card-heading">
              <span>02</span>
              <div>
                <strong>本地数据</strong>
                <p>数据库、配置和日志都由你掌控。</p>
              </div>
            </div>

            <div className="path-row">
              <DatabaseIcon />
              <div>
                <strong>数据库</strong>
                <span>{settings.db_path}</span>
              </div>
            </div>
            <div className="path-row">
              <FolderIcon />
              <div>
                <strong>配置文件</strong>
                <span>{settings.config_path}</span>
              </div>
            </div>
            <button className="open-path-button" type="button" onClick={() => openPath(settings.log_dir)}>
              <FolderIcon />
              打开日志目录
            </button>
          </section>
        ) : null}
      </div>
    </main>
  )
}
