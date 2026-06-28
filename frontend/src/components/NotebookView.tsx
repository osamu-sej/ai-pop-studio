import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { Notebook, ProviderStatus, Source } from '../types'
import { IconBack, IconDownload, IconSettings } from './Icons'
import { SourcesPanel } from './SourcesPanel'
import { ChatPanel } from './ChatPanel'
import { StudioPanel } from './StudioPanel'
import { StatusPill } from './StatusPill'

export function NotebookView({
  notebookId,
  status,
  onBack,
  onOpenSettings,
}: {
  notebookId: string
  status: ProviderStatus | null
  onBack: () => void
  onOpenSettings: () => void
}) {
  const [notebook, setNotebook] = useState<Notebook | null>(null)
  const [sources, setSources] = useState<Source[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [notesVersion, setNotesVersion] = useState(0)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [editingName, setEditingName] = useState(false)
  const [nameDraft, setNameDraft] = useState('')
  const firstLoad = useRef(true)
  const dragDepth = useRef(0)

  const loadSources = useCallback(async () => {
    const list = await api.listSources(notebookId)
    const ids = new Set(list.map((s) => s.id))
    setSources(list)
    // Keep selection in sync: drop deleted sources, auto-select brand-new ones.
    setSelected((prev) => {
      if (firstLoad.current) {
        firstLoad.current = false
        return new Set(ids)
      }
      const next = new Set<string>()
      for (const id of prev) if (ids.has(id)) next.add(id)
      for (const s of list) if (!prev.has(s.id)) next.add(s.id)
      return next
    })
  }, [notebookId])

  useEffect(() => {
    let active = true
    api.getNotebook(notebookId).then((nb) => active && setNotebook(nb))
    api.listSources(notebookId).then((list) => {
      if (!active) return
      setSources(list)
      setSelected(new Set(list.map((s) => s.id)))
      firstLoad.current = false
    })
    return () => {
      active = false
    }
  }, [notebookId])

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const setAll = (on: boolean) => {
    setSelected(on ? new Set(sources.map((s) => s.id)) : new Set())
  }

  const selectedIds = sources.length === selected.size ? undefined : Array.from(selected)

  const saveName = async () => {
    const name = nameDraft.trim()
    setEditingName(false)
    if (notebook && name && name !== notebook.name) {
      const updated = await api.updateNotebook(notebookId, { name })
      setNotebook(updated)
    }
  }

  const hasFiles = (e: React.DragEvent) => e.dataTransfer?.types?.includes('Files')

  const onDragEnter = (e: React.DragEvent) => {
    if (!hasFiles(e)) return
    e.preventDefault()
    dragDepth.current += 1
    setDragging(true)
  }
  const onDragOver = (e: React.DragEvent) => {
    if (hasFiles(e)) e.preventDefault()
  }
  const onDragLeave = (e: React.DragEvent) => {
    if (!hasFiles(e)) return
    dragDepth.current = Math.max(0, dragDepth.current - 1)
    if (dragDepth.current === 0) setDragging(false)
  }
  const onDrop = async (e: React.DragEvent) => {
    if (!hasFiles(e)) return
    e.preventDefault()
    dragDepth.current = 0
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length === 0) return
    setUploading(true)
    try {
      for (const f of files) {
        try {
          await api.addFile(notebookId, f)
        } catch {
          /* skip files that fail; others still import */
        }
      }
      await loadSources()
    } finally {
      setUploading(false)
    }
  }

  return (
    <div
      className="nbview"
      onDragEnter={onDragEnter}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <header className="nbview-head">
        <button className="icon-btn" onClick={onBack} title="Back to notebooks">
          <IconBack />
        </button>
        <span className="nbview-emoji">{notebook?.emoji ?? '📓'}</span>
        {editingName ? (
          <input
            className="nbview-title-input"
            autoFocus
            value={nameDraft}
            onChange={(e) => setNameDraft(e.target.value)}
            onBlur={saveName}
            onKeyDown={(e) => {
              if (e.key === 'Enter') saveName()
              if (e.key === 'Escape') setEditingName(false)
            }}
          />
        ) : (
          <h2
            className="nbview-title editable"
            title="Click to rename"
            onClick={() => {
              setNameDraft(notebook?.name ?? '')
              setEditingName(true)
            }}
          >
            {notebook?.name ?? 'Notebook'}
          </h2>
        )}
        <div className="spacer" />
        <a
          className="btn btn-sm"
          href={`/api/notebooks/${notebookId}/export`}
          title="Export this notebook to Markdown"
        >
          <IconDownload width={15} height={15} /> Export
        </a>
        <StatusPill status={status} />
        <button className="icon-btn" onClick={onOpenSettings} title="AI settings">
          <IconSettings />
        </button>
      </header>

      <div className="panes">
        <SourcesPanel
          notebookId={notebookId}
          sources={sources}
          selected={selected}
          onToggle={toggle}
          onSetAll={setAll}
          onChanged={loadSources}
        />
        <ChatPanel
          notebookId={notebookId}
          sources={sources}
          selectedIds={selectedIds}
          onNotesChanged={() => setNotesVersion((v) => v + 1)}
        />
        <StudioPanel
          notebookId={notebookId}
          hasSources={sources.length > 0}
          selectedIds={selectedIds}
          refreshKey={notesVersion}
        />
      </div>

      {(dragging || uploading) && (
        <div className="drop-overlay">
          <div className="drop-card">
            <span className="drop-icon">⬇</span>
            {uploading ? 'Importing files…' : 'Drop files to add them as sources'}
          </div>
        </div>
      )}
    </div>
  )
}
