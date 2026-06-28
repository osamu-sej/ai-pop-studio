import { useRef, useState } from 'react'
import { api } from '../api'
import { Modal } from './Modal'
import { IconDoc, IconLink, IconText } from './Icons'

type Tab = 'file' | 'url' | 'text'

export function AddSourceDialog({
  notebookId,
  onClose,
  onAdded,
}: {
  notebookId: string
  onClose: () => void
  onAdded: () => void
}) {
  const [tab, setTab] = useState<Tab>('file')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [text, setText] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const [files, setFiles] = useState<File[]>([])

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setError('')
    try {
      await fn()
      onAdded()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  const submit = () => {
    if (tab === 'url') {
      if (!url.trim()) return
      run(() => api.addUrl(notebookId, url.trim()))
    } else if (tab === 'text') {
      if (!text.trim()) return
      run(() => api.addText(notebookId, title.trim() || 'Pasted text', text))
    } else {
      if (files.length === 0) return
      run(async () => {
        for (const f of files) await api.addFile(notebookId, f)
      })
    }
  }

  return (
    <Modal title="Add source" onClose={onClose} width={560}>
      <div className="tabs">
        <button className={`tab ${tab === 'file' ? 'active' : ''}`} onClick={() => setTab('file')}>
          <IconDoc width={15} height={15} /> Upload
        </button>
        <button className={`tab ${tab === 'url' ? 'active' : ''}`} onClick={() => setTab('url')}>
          <IconLink width={15} height={15} /> Link
        </button>
        <button className={`tab ${tab === 'text' ? 'active' : ''}`} onClick={() => setTab('text')}>
          <IconText width={15} height={15} /> Paste
        </button>
      </div>

      {tab === 'file' && (
        <div
          className="dropzone"
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault()
            setFiles(Array.from(e.dataTransfer.files))
          }}
        >
          <input
            ref={fileRef}
            type="file"
            multiple
            hidden
            accept=".pdf,.docx,.txt,.md,.csv,.json,.mp3,.wav,.m4a,.mp4,.webm"
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          />
          {files.length === 0 ? (
            <>
              <IconDoc width={28} height={28} />
              <p>Drop files here or click to browse</p>
              <p className="muted small">PDF · DOCX · TXT · Markdown · CSV · audio</p>
            </>
          ) : (
            <ul className="file-list">
              {files.map((f, i) => (
                <li key={i}>{f.name}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {tab === 'url' && (
        <>
          <label className="field-label">Web page or YouTube URL</label>
          <input
            className="input"
            autoFocus
            placeholder="https://example.com/article  ·  https://youtu.be/…"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
          />
          <p className="muted small">YouTube links import the video transcript automatically.</p>
        </>
      )}

      {tab === 'text' && (
        <>
          <label className="field-label">Title</label>
          <input
            className="input"
            placeholder="Optional title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <label className="field-label">Text</label>
          <textarea
            className="input"
            rows={8}
            placeholder="Paste any text here…"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </>
      )}

      {error && <p className="error-text">{error}</p>}

      <div className="modal-actions">
        <button className="btn" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          {busy ? 'Importing…' : 'Add source'}
        </button>
      </div>
    </Modal>
  )
}
