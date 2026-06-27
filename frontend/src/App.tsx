import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import type { ProviderStatus } from './types'
import { Home } from './components/Home'
import { NotebookView } from './components/NotebookView'

export function App() {
  const [activeId, setActiveId] = useState<string | null>(null)
  const [status, setStatus] = useState<ProviderStatus | null>(null)

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
          onBack={() => {
            setActiveId(null)
            refreshStatus()
          }}
        />
      ) : (
        <Home status={status} onOpen={setActiveId} />
      )}
    </div>
  )
}
