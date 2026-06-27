import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { Notebook, ProviderStatus, Source } from '../types'
import { IconBack } from './Icons'
import { SourcesPanel } from './SourcesPanel'
import { ChatPanel } from './ChatPanel'
import { StudioPanel } from './StudioPanel'
import { StatusPill } from './StatusPill'

export function NotebookView({
  notebookId,
  status,
  onBack,
}: {
  notebookId: string
  status: ProviderStatus | null
  onBack: () => void
}) {
  const [notebook, setNotebook] = useState<Notebook | null>(null)
  const [sources, setSources] = useState<Source[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const firstLoad = useRef(true)

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

  return (
    <div className="nbview">
      <header className="nbview-head">
        <button className="icon-btn" onClick={onBack} title="Back to notebooks">
          <IconBack />
        </button>
        <span className="nbview-emoji">{notebook?.emoji ?? '📓'}</span>
        <h2 className="nbview-title">{notebook?.name ?? 'Notebook'}</h2>
        <div className="spacer" />
        <StatusPill status={status} />
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
        <ChatPanel notebookId={notebookId} sources={sources} selectedIds={selectedIds} />
        <StudioPanel notebookId={notebookId} hasSources={sources.length > 0} selectedIds={selectedIds} />
      </div>
    </div>
  )
}
