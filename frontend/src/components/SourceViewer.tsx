import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { SourceDetail } from '../types'
import { Modal } from './Modal'

const normalize = (s: string) => s.replace(/\s+/g, ' ').trim()

export function SourceViewer({
  notebookId,
  sourceId,
  snippet,
  onClose,
}: {
  notebookId: string
  sourceId: string
  snippet: string
  onClose: () => void
}) {
  const [src, setSrc] = useState<SourceDetail | null>(null)
  const hitRef = useRef<HTMLParagraphElement>(null)

  useEffect(() => {
    let active = true
    api.getSource(notebookId, sourceId).then((d) => active && setSrc(d))
    return () => {
      active = false
    }
  }, [notebookId, sourceId])

  useEffect(() => {
    if (src) hitRef.current?.scrollIntoView({ block: 'center' })
  }, [src])

  if (!src) {
    return (
      <Modal title="Source" onClose={onClose} width={760}>
        <p className="muted">Loading…</p>
      </Modal>
    )
  }

  // Locate the cited passage at paragraph granularity (robust to whitespace diffs).
  const key = normalize(snippet.replace(/…/g, '')).slice(0, 60).toLowerCase()
  const paragraphs = src.content.split(/\n\s*\n/).filter((p) => p.trim())
  const hitIndex =
    key.length > 4
      ? paragraphs.findIndex((p) => normalize(p).toLowerCase().includes(key))
      : -1

  return (
    <Modal title={src.title} onClose={onClose} width={760}>
      <div className="source-meta">
        <span className="badge">{src.source_type}</span>
        {src.origin && <span className="muted small">{src.origin}</span>}
      </div>
      <div className="source-reader">
        {paragraphs.length === 0 && <p className="muted">(empty)</p>}
        {paragraphs.map((p, i) => (
          <p
            key={i}
            ref={i === hitIndex ? hitRef : undefined}
            className={i === hitIndex ? 'reader-hit' : undefined}
          >
            {p}
          </p>
        ))}
      </div>
    </Modal>
  )
}
