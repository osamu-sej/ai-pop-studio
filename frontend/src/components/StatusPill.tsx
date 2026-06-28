import { useState } from 'react'
import type { ProviderStatus } from '../types'
import { IconChip } from './Icons'

export function StatusPill({ status }: { status: ProviderStatus | null }) {
  const [open, setOpen] = useState(false)
  if (!status) {
    return <span className="pill pill-muted">connecting…</span>
  }
  const live = status.llm_mode === 'model'
  return (
    <div className="status-wrap">
      <button
        className={`pill ${live ? 'pill-live' : 'pill-warn'}`}
        onClick={() => setOpen((v) => !v)}
        title="AI engine status"
      >
        <IconChip width={14} height={14} />
        {live ? `${status.llm_provider} · ${status.llm_model}` : 'Offline mode (heuristic)'}
      </button>
      {open && (
        <div className="status-pop" onMouseLeave={() => setOpen(false)}>
          <Row label="LLM" value={status.llm_available ? `${status.llm_provider} · ${status.llm_model}` : 'none'} ok={status.llm_available} />
          <Row label="Embeddings" value={status.embedding_provider} ok={status.embedding_provider !== 'hashing'} />
          <Row label="Podcast TTS" value={status.tts_available ? status.tts_provider : 'transcript only'} ok={status.tts_available} />
          {status.notes.length > 0 && (
            <div className="status-notes">
              {status.notes.map((n, i) => (
                <p key={i}>• {n}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Row({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="status-row">
      <span className={`dot ${ok ? 'dot-ok' : 'dot-warn'}`} />
      <span className="status-label">{label}</span>
      <span className="status-value">{value}</span>
    </div>
  )
}
