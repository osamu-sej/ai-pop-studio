import { useEffect, useState } from 'react'
import { api } from '../api'
import type { ProviderStatus, SettingsView } from '../types'
import { Modal } from './Modal'

const PROVIDERS: { value: string; label: string; hint: string }[] = [
  { value: 'ollama', label: 'Ollama (local, free)', hint: 'Recommended. Runs models on your machine.' },
  { value: 'openai', label: 'OpenAI-compatible', hint: 'LM Studio, llama.cpp, Groq, OpenRouter, OpenAI…' },
  { value: 'heuristic', label: 'Heuristic (no model)', hint: 'Built-in extractive engine. Always works.' },
]

export function SettingsModal({
  onClose,
  onSaved,
}: {
  onClose: () => void
  onSaved: (status: ProviderStatus) => void
}) {
  const [s, setS] = useState<SettingsView | null>(null)
  const [apiKey, setApiKey] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedNote, setSavedNote] = useState('')

  useEffect(() => {
    let active = true
    api.getSettings().then((v) => active && setS(v))
    return () => {
      active = false
    }
  }, [])

  if (!s) {
    return (
      <Modal title="AI settings" onClose={onClose} width={560}>
        <p className="muted">Loading…</p>
      </Modal>
    )
  }

  const set = (patch: Partial<SettingsView>) => setS({ ...s, ...patch })
  const isOpenAI = s.llm_provider === 'openai'
  const isOllama = s.llm_provider === 'ollama'

  const save = async () => {
    setBusy(true)
    setSavedNote('')
    try {
      const status = await api.updateSettings({
        llm_provider: s.llm_provider,
        llm_base_url: s.llm_base_url,
        llm_model: s.llm_model,
        embedding_provider: s.embedding_provider,
        embedding_model: s.embedding_model,
        tts_provider: s.tts_provider,
        ...(apiKey ? { llm_api_key: apiKey } : {}),
      })
      onSaved(status)
      setSavedNote(
        status.llm_mode === 'model'
          ? `✅ Connected: ${status.llm_provider} · ${status.llm_model}`
          : '⚠️ Saved, but no model reachable yet — still in heuristic mode. Check the URL/model.',
      )
    } catch (e) {
      setSavedNote(`⚠️ ${e instanceof Error ? e.message : 'Could not save'}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="AI settings" onClose={onClose} width={560}>
      <p className="muted small">
        Switch the AI engine without editing files or restarting. Everything stays local
        unless you point it at a hosted endpoint.
      </p>

      <label className="field-label">LLM provider</label>
      <div className="choice-row">
        {PROVIDERS.map((p) => (
          <button
            key={p.value}
            className={`choice ${s.llm_provider === p.value ? 'active' : ''}`}
            onClick={() => set({ llm_provider: p.value })}
          >
            {p.label}
          </button>
        ))}
      </div>
      <p className="muted small">{PROVIDERS.find((p) => p.value === s.llm_provider)?.hint}</p>

      {(isOllama || isOpenAI) && (
        <>
          <label className="field-label">{isOllama ? 'Ollama URL' : 'Base URL'}</label>
          <input
            className="input"
            value={s.llm_base_url}
            placeholder={isOllama ? 'http://localhost:11434' : 'http://localhost:1234/v1'}
            onChange={(e) => set({ llm_base_url: e.target.value })}
          />
          <label className="field-label">Model</label>
          <input
            className="input"
            value={s.llm_model}
            placeholder={isOllama ? 'llama3.1:8b' : 'llama-3.3-70b-versatile'}
            onChange={(e) => set({ llm_model: e.target.value })}
          />
        </>
      )}

      {isOpenAI && (
        <>
          <label className="field-label">
            API key {s.llm_api_key_set && <span className="muted small">(already set — leave blank to keep)</span>}
          </label>
          <input
            className="input"
            type="password"
            value={apiKey}
            placeholder={s.llm_api_key_set ? '•••••••• (unchanged)' : 'only for hosted endpoints'}
            onChange={(e) => setApiKey(e.target.value)}
          />
        </>
      )}

      <details className="adv">
        <summary>Advanced: embeddings & podcast voice</summary>
        <label className="field-label">Embedding provider</label>
        <div className="choice-row">
          {['auto', 'ollama', 'sentence-transformers', 'hashing'].map((v) => (
            <button
              key={v}
              className={`choice ${s.embedding_provider === v ? 'active' : ''}`}
              onClick={() => set({ embedding_provider: v })}
            >
              {v}
            </button>
          ))}
        </div>
        <label className="field-label">Embedding model (Ollama)</label>
        <input
          className="input"
          value={s.embedding_model}
          onChange={(e) => set({ embedding_model: e.target.value })}
        />
        <label className="field-label">Podcast TTS</label>
        <div className="choice-row">
          {['auto', 'piper', 'pyttsx3', 'none'].map((v) => (
            <button
              key={v}
              className={`choice ${s.tts_provider === v ? 'active' : ''}`}
              onClick={() => set({ tts_provider: v })}
            >
              {v}
            </button>
          ))}
        </div>
      </details>

      {savedNote && <p className="settings-note">{savedNote}</p>}

      <div className="modal-actions">
        <button className="btn" onClick={onClose}>Close</button>
        <button className="btn btn-primary" onClick={save} disabled={busy}>
          {busy ? 'Saving & testing…' : 'Save & test'}
        </button>
      </div>
    </Modal>
  )
}
