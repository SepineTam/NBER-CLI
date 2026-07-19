import { useEffect, useRef, useState } from 'react'
import { openUrl } from '@tauri-apps/plugin-opener'
import { CITATION_STYLES, copyText, formatCitation } from '../citation'
import type { CitationStyle } from '../citation'
import type { Paper, PaperTagSource } from '../types'
import { ChevronDownIcon, CloseIcon, CopyIcon, EyeIcon, GlobeIcon } from './Icons'
import { TagEditor } from './TagEditor'

interface PaperDetailProps {
  paperId: string | null
  paper: Paper | null
  error: string | null
  loading: boolean
  onClose: () => void
  onRetry: (paperId: string) => void
  onToggleRead: (paperId: string, isRead: boolean) => void
  onAddTag?: (paperId: string, tag: string) => Promise<void>
  onRenameTag?: (paperId: string, oldTag: string, newTag: string, source: PaperTagSource) => Promise<void>
  onRemoveTag?: (paperId: string, tag: string, source: PaperTagSource) => Promise<void>
}

export function PaperDetail({
  paperId,
  paper,
  error,
  loading,
  onClose,
  onRetry,
  onToggleRead,
  onAddTag = async () => {},
  onRenameTag = async () => {},
  onRemoveTag = async () => {},
}: PaperDetailProps) {
  const [citationStyle, setCitationStyle] = useState<CitationStyle>('bibtex')
  const [citationMenuOpen, setCitationMenuOpen] = useState(false)
  const [copyNotice, setCopyNotice] = useState<string | null>(null)
  const citationControlRef = useRef<HTMLDivElement>(null)
  const citationDefinition = CITATION_STYLES.find((style) => style.id === citationStyle) ?? CITATION_STYLES[0]

  useEffect(() => {
    setCitationMenuOpen(false)
    setCopyNotice(null)
  }, [paperId])

  useEffect(() => {
    function closeMenus(event: MouseEvent) {
      if (!citationControlRef.current?.contains(event.target as Node)) {
        setCitationMenuOpen(false)
      }
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setCitationMenuOpen(false)
      }
    }

    document.addEventListener('click', closeMenus)
    document.addEventListener('keydown', closeOnEscape)
    return () => {
      document.removeEventListener('click', closeMenus)
      document.removeEventListener('keydown', closeOnEscape)
    }
  }, [])

  async function copyCurrentCitation() {
    if (!paper) {
      return
    }
    try {
      await copyText(formatCitation(citationStyle, paper))
      setCopyNotice(`已复制 ${citationDefinition.label} 引用`)
    } catch {
      setCopyNotice('复制失败，请重试')
    }
  }

  return (
    <aside className="detail-panel" aria-live="polite">
      <header className="detail-header">
        <div className="detail-header-label">
          <i className={paper?.from_cache ? 'ready' : ''} />
          <span>{paper?.from_cache ? '本地资料库已连接' : '论文详情'}</span>
        </div>
        <div className="detail-actions">
          {paper ? (
            <button
              className="detail-icon-button"
              type="button"
              onClick={() => onToggleRead(paper.paper_id, !paper.is_read)}
              aria-label={paper.is_read ? '标记未读' : '标记已读'}
              title={paper.is_read ? '标记未读' : '标记已读'}
            >
              <EyeIcon />
            </button>
          ) : null}
          {paperId ? (
            <button className="detail-icon-button" type="button" onClick={onClose} aria-label="关闭详情" title="关闭详情">
              <CloseIcon />
            </button>
          ) : null}
        </div>
      </header>

      {loading ? (
        <div className="detail-skeleton" aria-label="正在获取论文详情">
          <div />
          <div />
          <div />
          <div />
        </div>
      ) : null}

      {!loading && !paper && error ? (
        <div className="detail-error">
          <strong>无法获取详情</strong>
          <span>{error}</span>
          <button className="secondary-button" type="button" disabled={!paperId} onClick={() => paperId && onRetry(paperId)}>
            重试
          </button>
        </div>
      ) : null}

      {!loading && !paper && !error ? (
        <div className="detail-empty">
          <span className="detail-empty-mark">N</span>
          <strong>选择一篇论文开始阅读</strong>
          <p>摘要、作者信息和引用格式会显示在这里。</p>
        </div>
      ) : null}

      {!loading && paper ? (
        <div className="detail-scroll">
          <span className="paper-number">NBER · {paper.paper_id.toUpperCase()}</span>
          <h2>{paper.title}</h2>
          <p className="detail-authors">{paper.authors.join(' · ') || 'Unknown authors'}</p>

          <TagEditor
            paperId={paper.paper_id}
            tags={paper.tags}
            onAdd={onAddTag}
            onRename={onRenameTag}
            onRemove={onRemoveTag}
          />

          <div className="detail-rule">Abstract</div>
          <p className="abstract">{paper.abstract || 'No abstract is available for this paper.'}</p>

          <div className="meta-grid">
            <div>
              <span>发布日期</span>
              <strong>{formatPaperDate(paper.date)}</strong>
            </div>
            <div>
              <span>分类</span>
              <strong>{paper.programs || paper.topic || 'Working Paper'}</strong>
            </div>
            <div>
              <span>资料来源</span>
              <strong>NBER</strong>
            </div>
            <div>
              <span>保存位置</span>
              <strong>{paper.from_cache ? '本机数据库' : '在线获取'}</strong>
            </div>
          </div>

          {paper.published_version ? (
            <div className="published-version">
              <span>Published version</span>
              <strong>{paper.published_version}</strong>
            </div>
          ) : null}

          <div className="citation-control" ref={citationControlRef}>
            <div className="citation-split">
              <button className="citation-copy" type="button" onClick={() => void copyCurrentCitation()} aria-label={`复制 ${citationDefinition.label}`}>
                <CopyIcon />
                <span>复制 {citationDefinition.label}</span>
              </button>
              <button
                className="citation-toggle"
                type="button"
                aria-label="选择引用格式"
                aria-expanded={citationMenuOpen}
                aria-controls="citation-menu"
                onClick={() => setCitationMenuOpen((open) => !open)}
              >
                <ChevronDownIcon />
              </button>
            </div>

            <div id="citation-menu" className={`citation-menu ${citationMenuOpen ? 'open' : ''}`} role="menu" aria-hidden={!citationMenuOpen}>
              <div className="citation-menu-label">选择引用格式</div>
              {CITATION_STYLES.map((style) => (
                <button
                  className={`citation-option ${style.id === citationStyle ? 'active' : ''}`}
                  data-citation-style={style.id}
                  key={style.id}
                  role="menuitem"
                  type="button"
                  onClick={() => {
                    setCitationStyle(style.id)
                    setCitationMenuOpen(false)
                    setCopyNotice(`已切换为 ${style.label}`)
                  }}
                >
                  <span className="citation-check">✓</span>
                  <span className="citation-option-name">{style.label}</span>
                  <span className="citation-option-note">{style.note}</span>
                </button>
              ))}
            </div>
          </div>

          {copyNotice ? <div className="copy-notice" role="status">{copyNotice}</div> : null}

          <button className="web-action" type="button" disabled={!paper.url} onClick={() => paper.url && openUrl(paper.url)}>
            <GlobeIcon />
            NBER 页面
          </button>
        </div>
      ) : null}
    </aside>
  )
}

function formatPaperDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value || 'No date'
  }
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date)
}
