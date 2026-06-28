import { useState } from 'react'
import { api } from '../api'
import type { GlobalSearchHit } from '../types'
import { IconSearch, IconClose } from './Icons'

export function GlobalSearch({ onOpen }: { onOpen: (id: string) => void }) {
  const [q, setQ] = useState('')
  const [hits, setHits] = useState<GlobalSearchHit[] | null>(null)
  const [busy, setBusy] = useState(false)

  const run = async () => {
    const query = q.trim()
    if (!query) {
      setHits(null)
      return
    }
    setBusy(true)
    try {
      setHits(await api.globalSearch(query))
    } catch {
      setHits([])
    } finally {
      setBusy(false)
    }
  }

  const reset = () => {
    setQ('')
    setHits(null)
  }

  return (
    <div className="global-search">
      <div className="gs-bar">
        <IconSearch width={16} height={16} />
        <input
          className="gs-input"
          value={q}
          placeholder="Search across all notebooks…"
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') run()
            if (e.key === 'Escape') reset()
          }}
        />
        {q && (
          <button className="icon-btn ghost" onClick={reset} title="Clear">
            <IconClose width={15} height={15} />
          </button>
        )}
      </div>

      {busy && <p className="muted small gs-status">Searching…</p>}

      {hits && !busy && (
        <div className="gs-results">
          {hits.length === 0 ? (
            <p className="muted small gs-status">No matches found.</p>
          ) : (
            hits.map((h, i) => (
              <button key={i} className="gs-hit" onClick={() => onOpen(h.notebook_id)}>
                <div className="gs-hit-head">
                  <span className="gs-hit-nb">{h.notebook_emoji} {h.notebook_name}</span>
                  <span className="muted small">{h.source_title}</span>
                </div>
                <div className="gs-hit-text">{h.text.slice(0, 180)}…</div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
