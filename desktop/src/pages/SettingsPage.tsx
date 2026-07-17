import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { openPath, openUrl } from '@tauri-apps/plugin-opener'
import { DatabaseIcon, FolderIcon } from '../components/Icons'
import { useAppStore } from '../stores/appStore'
import { checkForDesktopUpdate } from '../updateCheck'
import type { UpdateCheckResult } from '../updateCheck'

export function SettingsPage() {
  const { settings, savingSettings, loadSettings, updateSettings } = useAppStore()
  const [interval, setIntervalValue] = useState('60')
  const [checkingUpdate, setCheckingUpdate] = useState(false)
  const [updateResult, setUpdateResult] = useState<UpdateCheckResult | null>(null)
  const [updateError, setUpdateError] = useState<string | null>(null)

  useEffect(() => {
    if (!settings) {
      void loadSettings()
      return
    }
    setIntervalValue(String(settings.feed_refresh_interval_minutes))
  }, [loadSettings, settings])

  function submit(event: FormEvent) {
    event.preventDefault()
    void updateSettings({
      feed_refresh_interval_minutes: Number(interval),
    })
  }

  async function checkUpdate() {
    setCheckingUpdate(true)
    setUpdateError(null)
    try {
      setUpdateResult(await checkForDesktopUpdate())
    } catch (error) {
      setUpdateResult(null)
      setUpdateError(error instanceof Error ? error.message : 'Failed to check for updates')
    } finally {
      setCheckingUpdate(false)
    }
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
                  <p>控制桌面端自动同步最新论文的频率。</p>
            </div>
          </div>

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

        <section className="settings-card settings-update">
          <div className="settings-card-heading">
            <span>03</span>
            <div>
              <strong>桌面端更新</strong>
              <p>不会自动弹出提示；点击检查后才会访问 GitHub。</p>
            </div>
          </div>

          <div className="update-status">
            <strong>当前版本</strong>
            <span>v{__APP_VERSION__}</span>
          </div>

          {updateResult ? (
            <div className={`update-message ${updateResult.available ? 'available' : 'current'}`}>
              {updateResult.available ? (
                <>
                  <strong>发现新版本 v{updateResult.latestVersion}</strong>
                  <p>打开 GitHub Releases 下载与你系统匹配的安装包并覆盖安装。</p>
                </>
              ) : (
                <>
                  <strong>已经是最新版本</strong>
                  <p>当前版本 v{updateResult.currentVersion} 与 GitHub 最新版本一致。</p>
                </>
              )}
            </div>
          ) : null}

          {updateError ? <p className="update-error">{updateError}</p> : null}

          <div className="update-actions">
            <button className="settings-save" type="button" onClick={checkUpdate} disabled={checkingUpdate}>
              {checkingUpdate ? '正在检查' : '检查更新'}
            </button>
            {updateResult?.available ? (
              <button className="open-path-button" type="button" onClick={() => openUrl(updateResult.releaseUrl)}>
                打开下载页面
              </button>
            ) : null}
          </div>
        </section>
      </div>
    </main>
  )
}
