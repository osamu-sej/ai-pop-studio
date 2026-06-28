import { useState } from 'react'
import { api } from '../api'
import type { Source, SourceDetail } from '../types'
import { IconDoc, IconLink, IconPlus, IconText, IconTrash, IconYoutube } from './Icons'
import { AddSourceDialog } from './AddSourceDialog'
import { Modal } from './Modal'
import { Markdown } from '../lib/markdown'

function typeIcon(t: string) {
  if (t === 'pdf' || t === 'docx') return <IconDoc width={16} height={16} />
  if (t === 'web') return <IconLink width={16} height={16} />
  if (t === 'youtube') return <IconYoutube width={16} height={16} />
  return <IconText width={16} height={16} />
}

export function SourcesPanel({
  notebookId,
  sources,
  selected,
  onToggle,
  onSetAll,
  onChanged,
}: {
  notebookId: string
  sources: Source[]
  selected: Set<string>
  onToggle: (id: string) => void
  onSetAll: (on: boolean) => void
  onChanged: () => void
}) {
  const [adding, setAdding] = useState(false)
  const [detail, setDetail] = useState<SourceDetail | null>(null)
  const [reindexing, setReindexing] = useState(false)

  const allOn = sources.length > 0 && selected.size === sources.length

  const remove = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    await api.deleteSource(notebookId, id)
    onChanged()
  }

  const openDetail = async (id: string) => {
    const d = await api.getSource(notebookId, id)
    setDetail(d)
  }

  const reindex = async () => {
    if (!detail) return
    setReindexing(true)
    try {
      await api.reindexSource(notebookId, detail.id)
      onChanged()
      setDetail(null)
    } finally {
      setReindexing(false)
    }
  }

  return (
    <aside className="panel panel-sources">
      <div className="panel-head">
        <h3>Sources</h3>
        <button className="btn btn-sm btn-primary" onClick={() => setAdding(true)}>
          <IconPlus width={14} height={14} /> Add
        </button>
      </div>

      {sources.length > 0 && (
        <label className="select-all">
          <input type="checkbox" checked={allOn} onChange={(e) => onSetAll(e.target.checked)} />
          <span>Select all sources</span>
          <span className="count">{selected.size}/{sources.length}</span>
        </label>
      )}

      <div className="panel-scroll">
        {sources.length === 0 ? (
          <div className="panel-empty">
            <p>No sources yet.</p>
            <p className="muted">Add a PDF, web link, YouTube video, or paste text to ground
              your chat and studio outputs.</p>
          </div>
        ) : (
          sources.map((s) => (
            <div
              key={s.id}
              className={`source-card ${selected.has(s.id) ? 'sel' : ''}`}
              onClick={() => openDetail(s.id)}
            >
              <input
                type="checkbox"
                checked={selected.has(s.id)}
                onClick={(e) => e.stopPropagation()}
                onChange={() => onToggle(s.id)}
              />
              <span className="source-icon">{typeIcon(s.source_type)}</span>
              <div className="source-main">
                <div className="source-title">{s.title}</div>
                <div className="source-sub">
                  <span className="badge">{s.source_type}</span>
                  {s.status === 'needs_stt' && <span className="badge badge-warn">no transcript</span>}
                  <span className="muted">{s.token_count} tok</span>
                </div>
              </div>
              <button className="icon-btn ghost" onClick={(e) => remove(e, s.id)} title="Remove">
                <IconTrash width={14} height={14} />
              </button>
            </div>
          ))
        )}
      </div>

      {adding && (
        <AddSourceDialog
          notebookId={notebookId}
          onClose={() => setAdding(false)}
          onAdded={() => {
            setAdding(false)
            onChanged()
          }}
        />
      )}

      {detail && (
        <Modal title={detail.title} onClose={() => setDetail(null)} width={720}>
          {detail.summary && (
            <div className="detail-summary">
              <h4>Summary</h4>
              <Markdown text={detail.summary} />
            </div>
          )}
          {detail.origin && (
            <p className="muted small">Origin: {detail.origin}</p>
          )}
          {detail.status === 'needs_stt' && (
            <p className="error-text">
              This audio wasn't transcribed. Install the optional `faster-whisper` package and
              re-upload the file to transcribe it.
            </p>
          )}
          <h4>Content</h4>
          <div className="detail-content">{detail.content || '(empty)'}</div>
          <div className="modal-actions">
            <button className="btn" onClick={reindex} disabled={reindexing} title="Re-chunk, re-embed and re-summarise">
              {reindexing ? 'Re-indexing…' : 'Re-index'}
            </button>
          </div>
        </Modal>
      )}
    </aside>
  )
}
