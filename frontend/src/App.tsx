import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import type { ProviderStatus } from './types'
import { Home } from './components/Home'
import { NotebookView } from './components/NotebookView'
import { SettingsModal } from './components/SettingsModal'

export function App() {
  const [activeId, setActiveId] = useState<string | null>(null)
  const [status, setStatus] = useState<ProviderStatus | null>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)

  const refreshStatus = useCallback(() => {
    api.status().then(setStatus).catch(() => setStatus(null))
  }, [])

  useEffect(() => {
    refreshStatus()
  }, [refreshStatus])

  return (
    <div className="app">
      {activeId ? (
        <NotebookView
          notebookId={activeId}
          status={status}
          onOpenSettings={() => setSettingsOpen(true)}
          onBack={() => {
            setActiveId(null)
            refreshStatus()
          }}
        />
      ) : (
        <Home status={status} onOpen={setActiveId} onOpenSettings={() => setSettingsOpen(true)} />
      )}

      {settingsOpen && (
        <SettingsModal onClose={() => setSettingsOpen(false)} onSaved={setStatus} />
      )}
    </div>
  )
}
