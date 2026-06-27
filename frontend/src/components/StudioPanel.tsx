import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Note, Podcast, TransformKind } from '../types'
import { Markdown } from '../lib/markdown'
import { IconMic, IconNote, IconPlus, IconSparkles, IconTrash } from './Icons'
import { Modal } from './Modal'

const TRANSFORMS: { kind: TransformKind; label: string; icon: string }[] = [
  { kind: 'summary', label: 'Summary', icon: '📝' },
  { kind: 'study_guide', label: 'Study Guide', icon: '🎓' },
  { kind: 'faq', label: 'FAQ', icon: '❓' },
  { kind: 'timeline', label: 'Timeline', icon: '📅' },
  { kind: 'key_topics', label: 'Key Topics', icon: '🏷️' },
  { kind: 'briefing', label: 'Briefing Doc', icon: '📋' },
  { kind: 'mindmap', label: 'Mind Map', icon: '🧠' },
]

export function StudioPanel({
  notebookId,
  hasSources,
  selectedIds,
  refreshKey,
}: {
  notebookId: string
  hasSources: boolean
  selectedIds: string[] | undefined
  refreshKey?: number
}) {
  const [notes, setNotes] = useState<Note[]>([])
  const [podcasts, setPodcasts] = useState<Podcast[]>([])
  const [running, setRunning] = useState<string | null>(null)
  const [openNote, setOpenNote] = useState<Note | null>(null)
  const [openPodcast, setOpenPodcast] = useState<Podcast | null>(null)
  const [showPodcastSetup, setShowPodcastSetup] = useState(false)

  const reload = () => {
    api.listNotes(notebookId).then(setNotes)
    api.listPodcasts(notebookId).then(setPodcasts)
  }
  useEffect(reload, [notebookId, refreshKey])

  const runTransform = async (kind: TransformKind) => {
    if (!hasSources) return
    setRunning(kind)
    try {
      const res = await api.transform(notebookId, kind, selectedIds)
      const list = await api.listNotes(notebookId)
      setNotes(list)
      const created = list.find((n) => n.id === res.note_id)
      if (created) setOpenNote(created)
    } finally {
      setRunning(null)
    }
  }

  const addBlankNote = async () => {
    const n = await api.createNote(notebookId, 'New note', '')
    setNotes((prev) => [n, ...prev])
    setOpenNote(n)
  }

  const deleteNote = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    await api.deleteNote(notebookId, id)
    setNotes((prev) => prev.filter((n) => n.id !== id))
  }

  const deletePodcast = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    await api.deletePodcast(notebookId, id)
    setPodcasts((prev) => prev.filter((p) => p.id !== id))
  }

  return (
    <section className="panel panel-studio">
      <div className="panel-head">
        <h3>Studio</h3>
      </div>

      <div className="panel-scroll">
        <div className="studio-section">
          <div className="studio-section-head">
            <IconSparkles width={15} height={15} />
            <span>Generate</span>
          </div>
          <div className="transform-grid">
            {TRANSFORMS.map((t) => (
              <button
                key={t.kind}
                className="transform-btn"
                disabled={!hasSources || running !== null}
                onClick={() => runTransform(t.kind)}
              >
                <span className="t-icon">{t.icon}</span>
                <span>{running === t.kind ? 'Working…' : t.label}</span>
              </button>
            ))}
          </div>
          <button
            className="audio-btn"
            disabled={!hasSources || running !== null}
            onClick={() => setShowPodcastSetup(true)}
          >
            <IconMic width={18} height={18} />
            <div>
              <strong>Audio Overview</strong>
              <span className="muted small">Generate a two-host podcast from your sources</span>
            </div>
          </button>
        </div>

        {podcasts.length > 0 && (
          <div className="studio-section">
            <div className="studio-section-head">
              <IconMic width={15} height={15} />
              <span>Audio overviews</span>
            </div>
            {podcasts.map((p) => (
              <div key={p.id} className="studio-item" onClick={() => setOpenPodcast(p)}>
                <span className="studio-item-icon">🎙️</span>
                <div className="studio-item-main">
                  <div className="studio-item-title">{p.title}</div>
                  <div className="muted small">
                    {p.audio_url ? 'audio + transcript' : 'transcript'} · {p.status}
                  </div>
                </div>
                <button className="icon-btn ghost" onClick={(e) => deletePodcast(e, p.id)}>
                  <IconTrash width={14} height={14} />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="studio-section">
          <div className="studio-section-head">
            <IconNote width={15} height={15} />
            <span>Notes</span>
            <button className="icon-btn ghost mini" onClick={addBlankNote} title="New note">
              <IconPlus width={14} height={14} />
            </button>
          </div>
          {notes.length === 0 ? (
            <p className="muted small pad">Generated outputs and your own notes are saved here.</p>
          ) : (
            notes.map((n) => (
              <div key={n.id} className="studio-item" onClick={() => setOpenNote(n)}>
                <span className="studio-item-icon">{n.note_type === 'generated' ? '✨' : '🗒️'}</span>
                <div className="studio-item-main">
                  <div className="studio-item-title">{n.title}</div>
                  <div className="muted small">{n.note_type === 'generated' ? n.kind.replace('_', ' ') : 'note'}</div>
                </div>
                <button className="icon-btn ghost" onClick={(e) => deleteNote(e, n.id)}>
                  <IconTrash width={14} height={14} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {openNote && (
        <NoteEditor
          notebookId={notebookId}
          note={openNote}
          onClose={() => setOpenNote(null)}
          onSaved={(n) => {
            setNotes((prev) => prev.map((x) => (x.id === n.id ? n : x)))
            setOpenNote(null)
          }}
        />
      )}

      {openPodcast && (
        <Modal title={openPodcast.title} onClose={() => setOpenPodcast(null)} width={720}>
          {openPodcast.audio_url && (
            <audio controls src={openPodcast.audio_url} style={{ width: '100%', marginBottom: 16 }} />
          )}
          <Markdown text={openPodcast.transcript} />
        </Modal>
      )}

      {showPodcastSetup && (
        <PodcastSetup
          notebookId={notebookId}
          selectedIds={selectedIds}
          onClose={() => setShowPodcastSetup(false)}
          onDone={(p) => {
            setShowPodcastSetup(false)
            setPodcasts((prev) => [p, ...prev])
            setOpenPodcast(p)
          }}
        />
      )}
    </section>
  )
}

function NoteEditor({
  notebookId,
  note,
  onClose,
  onSaved,
}: {
  notebookId: string
  note: Note
  onClose: () => void
  onSaved: (n: Note) => void
}) {
  const [title, setTitle] = useState(note.title)
  const [content, setContent] = useState(note.content)
  const [editing, setEditing] = useState(note.note_type !== 'generated')
  const [busy, setBusy] = useState(false)

  const save = async () => {
    setBusy(true)
    try {
      const updated = await api.updateNote(notebookId, note.id, { title, content })
      onSaved(updated)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title={editing ? 'Edit note' : note.title} onClose={onClose} width={720}>
      {editing ? (
        <>
          <label className="field-label">Title</label>
          <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} />
          <label className="field-label">Content (markdown)</label>
          <textarea
            className="input mono"
            rows={16}
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <div className="modal-actions">
            <button className="btn" onClick={onClose}>Cancel</button>
            <button className="btn btn-primary" onClick={save} disabled={busy}>
              {busy ? 'Saving…' : 'Save'}
            </button>
          </div>
        </>
      ) : (
        <>
          <Markdown text={content} />
          <div className="modal-actions">
            <button className="btn" onClick={() => setEditing(true)}>Edit</button>
            <button className="btn btn-primary" onClick={onClose}>Done</button>
          </div>
        </>
      )}
    </Modal>
  )
}

function PodcastSetup({
  notebookId,
  selectedIds,
  onClose,
  onDone,
}: {
  notebookId: string
  selectedIds: string[] | undefined
  onClose: () => void
  onDone: (p: Podcast) => void
}) {
  const [style, setStyle] = useState('conversational')
  const [length, setLength] = useState('medium')
  const [busy, setBusy] = useState(false)

  const generate = async () => {
    setBusy(true)
    try {
      const p = await api.createPodcast(notebookId, { style, length, source_ids: selectedIds })
      onDone(p)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="Audio Overview" onClose={onClose} width={520}>
      <p className="muted small">
        Two AI hosts discuss your selected sources. The script is generated locally; audio is
        synthesized if a local TTS engine is installed (otherwise you get the transcript).
      </p>
      <label className="field-label">Style</label>
      <div className="choice-row">
        {[
          ['conversational', 'Conversational'],
          ['deep_dive', 'Deep dive'],
          ['debate', 'Debate'],
          ['solo', 'Solo host'],
        ].map(([v, l]) => (
          <button key={v} className={`choice ${style === v ? 'active' : ''}`} onClick={() => setStyle(v)}>
            {l}
          </button>
        ))}
      </div>
      <label className="field-label">Length</label>
      <div className="choice-row">
        {[
          ['short', 'Short'],
          ['medium', 'Medium'],
          ['long', 'Long'],
        ].map(([v, l]) => (
          <button key={v} className={`choice ${length === v ? 'active' : ''}`} onClick={() => setLength(v)}>
            {l}
          </button>
        ))}
      </div>
      <div className="modal-actions">
        <button className="btn" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={generate} disabled={busy}>
          {busy ? 'Generating…' : 'Generate'}
        </button>
      </div>
    </Modal>
  )
}
