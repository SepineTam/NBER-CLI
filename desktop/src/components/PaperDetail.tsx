import { openUrl } from '@tauri-apps/plugin-opener'
import type { Paper } from '../types'

interface PaperDetailProps {
  paperId: string | null
  paper: Paper | null
  error: string | null
  loading: boolean
  onClose: () => void
  onRetry: (paperId: string) => void
  onToggleRead: (paperId: string, isRead: boolean) => void
}

export function PaperDetail({
  paperId,
  paper,
  error,
  loading,
  onClose,
  onRetry,
  onToggleRead,
}: PaperDetailProps) {
  const isOpen = Boolean(paper || loading || error || paperId)

  return (
    <aside className={`detail-drawer ${isOpen ? 'open' : ''}`} aria-live="polite">
      <div className="drawer-header">
        <span>Paper Detail</span>
        <button className="icon-button" type="button" onClick={onClose} aria-label="关闭详情">
          ×
        </button>
      </div>

      {loading ? (
        <div className="drawer-skeleton">
          <div />
          <div />
          <div />
        </div>
      ) : null}

      {!loading && !paper && error ? (
        <div className="drawer-error">
          <strong>无法获取详情</strong>
          <span>{error}</span>
          <button
            className="secondary-button"
            type="button"
            disabled={!paperId}
            onClick={() => paperId && onRetry(paperId)}
          >
            重试
          </button>
        </div>
      ) : null}

      {!loading && paper ? (
        <div className="drawer-content">
          <div className="paper-kicker">
            <span>{paper.paper_id}</span>
            <span>{paper.date || 'No date'}</span>
          </div>
          <h2>{paper.title}</h2>
          <p className="authors">{paper.authors.join(', ') || 'Unknown authors'}</p>
          <p className="abstract">{paper.abstract || 'No abstract is available for this paper.'}</p>

          {paper.published_version ? (
            <div className="metadata-line">
              <strong>Published version</strong>
              <span>{paper.published_version}</span>
            </div>
          ) : null}

          <div className="drawer-actions">
            <button
              type="button"
              className="secondary-button"
              disabled={!paper.url}
              onClick={() => paper.url && openUrl(paper.url)}
            >
              NBER 页面
            </button>
            <button
              type="button"
              className="secondary-button"
              disabled={!paper.pdf_url}
              onClick={() => paper.pdf_url && openUrl(paper.pdf_url)}
            >
              下载 PDF
            </button>
            <button
              type="button"
              className="secondary-button"
              onClick={() => onToggleRead(paper.paper_id, !paper.is_read)}
            >
              {paper.is_read ? '标记未读' : '标记已读'}
            </button>
          </div>
        </div>
      ) : null}
    </aside>
  )
}
