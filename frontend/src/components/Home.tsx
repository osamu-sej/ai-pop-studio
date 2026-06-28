import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Notebook, ProviderStatus } from '../types'
import { IconBook, IconPlus, IconSettings, IconTrash } from './Icons'
import { Modal } from './Modal'
import { StatusPill } from './StatusPill'
import { GlobalSearch } from './GlobalSearch'

const EMOJIS = ['📓', '🌍', '🔬', '📚', '💡', '🧠', '⚖️', '🚀', '🎬', '🧪', '📈', '🩺']

export function Home({
  status,
  onOpen,
  onOpenSettings,
}: {
  status: ProviderStatus | null
  onOpen: (id: string) => void
  onOpenSettings: () => void
}) {
  const [notebooks, setNotebooks] = useState<Notebook[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)

  const load = () => {
    api
      .listNotebooks()
      .then(setNotebooks)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    let active = true
    api
      .listNotebooks()
      .then((nbs) => active && setNotebooks(nbs))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  const remove = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!confirm('Delete this notebook and all its sources?')) return
    await api.deleteNotebook(id)
    load()
  }

  return (
    <div className="home">
      <header className="home-head">
        <div className="brand">
          <span className="brand-mark">◑</span>
          <div>
            <h1>Aurora</h1>
            <p className="brand-sub">Your local-first research notebook</p>
          </div>
        </div>
        <StatusPill status={status} />
        <button className="icon-btn" onClick={onOpenSettings} title="AI settings">
          <IconSettings />
        </button>
      </header>

      <div className="home-body">
        {!loading && notebooks.length > 0 && <GlobalSearch onOpen={onOpen} />}

        <div className="home-title-row">
          <h2>Notebooks</h2>
          <button className="btn btn-primary" onClick={() => setCreating(true)}>
            <IconPlus width={16} height={16} /> New notebook
          </button>
        </div>

        {loading ? (
          <p className="muted">Loading…</p>
        ) : notebooks.length === 0 ? (
          <div className="empty-state">
            <IconBook width={42} height={42} />
            <h3>Create your first notebook</h3>
            <p>Add PDFs, web pages, YouTube videos or pasted text, then chat with your sources,
              generate study guides, and produce audio overviews — all running on your machine.</p>
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <IconPlus width={16} height={16} /> New notebook
            </button>
          </div>
        ) : (
          <div className="nb-grid">
            {notebooks.map((nb) => (
              <button key={nb.id} className="nb-card" onClick={() => onOpen(nb.id)}>
                <div className="nb-emoji">{nb.emoji}</div>
                <div className="nb-card-body">
                  <h3>{nb.name}</h3>
                  {nb.description && <p className="nb-desc">{nb.description}</p>}
                  <div className="nb-meta">
                    <span>{nb.source_count} sources</span>
                    <span>·</span>
                    <span>{nb.note_count} notes</span>
                  </div>
                </div>
                <span className="nb-del" onClick={(e) => remove(e, nb.id)} title="Delete">
                  <IconTrash width={15} height={15} />
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {creating && (
        <CreateModal
          onClose={() => setCreating(false)}
          onCreated={(id) => {
            setCreating(false)
            onOpen(id)
          }}
        />
      )}
    </div>
  )
}

function CreateModal({ onClose, onCreated }: { onClose: () => void; onCreated: (id: string) => void }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [emoji, setEmoji] = useState(EMOJIS[0])
  const [busy, setBusy] = useState(false)

  const submit = async () => {
    if (!name.trim()) return
    setBusy(true)
    try {
      const nb = await api.createNotebook(name.trim(), emoji, description.trim())
      onCreated(nb.id)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="New notebook" onClose={onClose}>
      <label className="field-label">Icon</label>
      <div className="emoji-row">
        {EMOJIS.map((e) => (
          <button
            key={e}
            className={`emoji-pick ${e === emoji ? 'active' : ''}`}
            onClick={() => setEmoji(e)}
          >
            {e}
          </button>
        ))}
      </div>
      <label className="field-label">Name</label>
      <input
        className="input"
        autoFocus
        value={name}
        placeholder="e.g. Climate Policy Research"
        onChange={(e) => setName(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && submit()}
      />
      <label className="field-label">Description (optional)</label>
      <textarea
        className="input"
        rows={2}
        value={description}
        placeholder="What is this notebook about?"
        onChange={(e) => setDescription(e.target.value)}
      />
      <div className="modal-actions">
        <button className="btn" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={submit} disabled={!name.trim() || busy}>
          {busy ? 'Creating…' : 'Create notebook'}
        </button>
      </div>
    </Modal>
  )
}
