import { useEffect, useState } from 'react'
import type { PaperTag, PaperTagSource } from '../types'

interface TagEditorProps {
  paperId: string
  tags: PaperTag[]
  onAdd: (paperId: string, tag: string) => Promise<void>
  onRename: (
    paperId: string,
    oldTag: string,
    newTag: string,
    source: PaperTagSource,
  ) => Promise<void>
  onRemove: (paperId: string, tag: string, source: PaperTagSource) => Promise<void>
}

export function TagEditor({ paperId, tags, onAdd, onRename, onRemove }: TagEditorProps) {
  const [newTag, setNewTag] = useState('')
  const [editing, setEditing] = useState<PaperTag | null>(null)
  const [editedTag, setEditedTag] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setNewTag('')
    setEditing(null)
    setEditedTag('')
  }, [paperId])

  async function addTag() {
    if (!newTag.trim() || busy) return
    setBusy(true)
    try {
      await onAdd(paperId, newTag)
      setNewTag('')
    } catch {
      return
    } finally {
      setBusy(false)
    }
  }

  async function saveRename() {
    if (!editing || !editedTag.trim() || busy) return
    setBusy(true)
    try {
      await onRename(paperId, editing.name, editedTag, editing.source)
      setEditing(null)
      setEditedTag('')
    } catch {
      return
    } finally {
      setBusy(false)
    }
  }

  async function removeTag(tag: PaperTag) {
    if (busy) return
    setBusy(true)
    try {
      await onRemove(paperId, tag.name, tag.source)
    } catch {
      return
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="tag-editor" aria-label="论文标签">
      <div className="tag-editor-heading">
        <strong>标签</strong>
        <span>官方标签来自 NBER，改动只保存在本机</span>
      </div>

      <div className="tag-list">
        {tags.length === 0 ? <span className="tag-empty">暂无标签</span> : null}
        {tags.map((tag) => (
          <span className={`tag-chip tag-${tag.source}`} key={`${tag.source}-${tag.name}`}>
            <span>{tag.name}</span>
            <button
              type="button"
              disabled={busy}
              aria-label={`修改标签 ${tag.name}`}
              title="修改"
              onClick={() => {
                setEditing(tag)
                setEditedTag(tag.name)
              }}
            >
              编辑
            </button>
            <button
              type="button"
              disabled={busy}
              aria-label={`删除标签 ${tag.name}`}
              title={tag.source === 'user' ? '删除' : '在本机隐藏'}
              onClick={() => void removeTag(tag)}
            >
              ×
            </button>
          </span>
        ))}
      </div>

      {editing ? (
        <form
          className="tag-form"
          onSubmit={(event) => {
            event.preventDefault()
            void saveRename()
          }}
        >
          <input
            aria-label="新的标签名称"
            autoFocus
            maxLength={60}
            value={editedTag}
            onChange={(event) => setEditedTag(event.target.value)}
          />
          <button type="submit" disabled={busy || !editedTag.trim()}>保存</button>
          <button type="button" onClick={() => setEditing(null)}>取消</button>
        </form>
      ) : (
        <form
          className="tag-form"
          onSubmit={(event) => {
            event.preventDefault()
            void addTag()
          }}
        >
          <input
            aria-label="添加标签"
            maxLength={60}
            placeholder="添加自己的标签"
            value={newTag}
            onChange={(event) => setNewTag(event.target.value)}
          />
          <button type="submit" disabled={busy || !newTag.trim()}>添加</button>
        </form>
      )}
    </section>
  )
}
