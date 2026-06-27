import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { ChatMessage, NotebookGuide, Source } from '../types'
import { Markdown } from '../lib/markdown'
import { IconSend, IconSparkles, IconTrash } from './Icons'
import { SourceViewer } from './SourceViewer'

const FALLBACK_SUGGESTIONS = [
  'Give me a 5-bullet summary of these sources.',
  'What are the key arguments and who makes them?',
  'What questions do these sources leave unanswered?',
  'Compare and contrast the main viewpoints.',
]

export function ChatPanel({
  notebookId,
  sources,
  selectedIds,
  onNotesChanged,
}: {
  notebookId: string
  sources: Source[]
  selectedIds: string[] | undefined
  onNotesChanged?: () => void
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [guide, setGuide] = useState<NotebookGuide | null>(null)
  const [guideLoading, setGuideLoading] = useState(false)
  const [viewer, setViewer] = useState<{ sourceId: string; snippet: string } | null>(null)
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.getChat(notebookId).then(setMessages)
  }, [notebookId])

  const loadGuide = (force = false) => {
    if (sources.length === 0) {
      setGuide(null)
      return
    }
    if (guide && !force) return
    setGuideLoading(true)
    api
      .getGuide(notebookId)
      .then(setGuide)
      .catch(() => setGuide(null))
      .finally(() => setGuideLoading(false))
  }

  useEffect(() => {
    let active = true
    if (sources.length === 0) {
      setGuide(null)
      return
    }
    setGuideLoading(true)
    api
      .getGuide(notebookId)
      .then((g) => active && setGuide(g))
      .catch(() => active && setGuide(null))
      .finally(() => active && setGuideLoading(false))
    return () => {
      active = false
    }
    // reload when the set of sources changes
  }, [notebookId, sources.length])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, busy])

  const send = async (textArg?: string) => {
    const text = (textArg ?? input).trim()
    if (!text || busy) return
    setInput('')
    setBusy(true)
    const now = Date.now()
    const streamId = `stream-${now}`
    // optimistic user bubble + an empty assistant bubble that fills in live
    setMessages((m) => [
      ...m,
      { id: `tmp-${now}`, notebook_id: notebookId, role: 'user', content: text, citations: [], created_at: new Date().toISOString() },
      { id: streamId, notebook_id: notebookId, role: 'assistant', content: '', citations: [], created_at: new Date().toISOString() },
    ])

    const patchStream = (fn: (msg: ChatMessage) => ChatMessage) =>
      setMessages((m) => m.map((x) => (x.id === streamId ? fn(x) : x)))

    try {
      await api.sendChatStream(notebookId, text, selectedIds, {
        onToken: (t) => patchStream((x) => ({ ...x, content: x.content + t })),
        onDone: (final) => patchStream(() => final),
        onError: (e) => patchStream((x) => ({ ...x, content: `⚠️ ${e}` })),
      })
    } catch (e) {
      patchStream((x) => ({ ...x, content: `⚠️ ${e instanceof Error ? e.message : 'Request failed'}` }))
    } finally {
      setBusy(false)
    }
  }

  const clear = async () => {
    await api.clearChat(notebookId)
    setMessages([])
  }

  const scrollToCite = (messageId: string, n: number) => {
    const el = document.getElementById(`cite-${messageId}-${n}`)
    if (!el) return
    if (el instanceof HTMLDetailsElement) el.open = true
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    el.classList.add('cite-flash')
    setTimeout(() => el.classList.remove('cite-flash'), 1200)
  }

  const saveAnswer = async (m: ChatMessage) => {
    if (savedIds.has(m.id)) return
    const idx = messages.findIndex((x) => x.id === m.id)
    const question = idx > 0 ? messages[idx - 1].content : ''
    const title = question ? question.slice(0, 80) : 'Saved answer'
    await api.createNote(notebookId, title, m.content)
    setSavedIds((prev) => new Set(prev).add(m.id))
    onNotesChanged?.()
  }

  const activeCount = selectedIds ? selectedIds.length : sources.length

  return (
    <section className="panel panel-chat">
      <div className="panel-head">
        <h3>Chat</h3>
        <div className="chat-head-right">
          <span className="muted small">{activeCount} of {sources.length} sources in context</span>
          {messages.length > 0 && (
            <button className="icon-btn ghost" onClick={clear} title="Clear conversation">
              <IconTrash width={15} height={15} />
            </button>
          )}
        </div>
      </div>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="chat-welcome">
            <div className="chat-welcome-badge"><IconSparkles width={22} height={22} /></div>
            <h3>Ask anything about your sources</h3>
            <p className="muted">
              {sources.length === 0
                ? 'Add a source on the left to get grounded, cited answers.'
                : 'Answers are grounded in your selected sources, with citations you can verify.'}
            </p>
            {sources.length > 0 && (
              <>
                {guideLoading && !guide && <p className="muted small">Building your notebook guide…</p>}
                {guide && guide.overview && (
                  <div className="guide-card">
                    <div className="guide-head">
                      <span>📋 Notebook guide</span>
                      <button className="link-btn" onClick={() => loadGuide(true)} disabled={guideLoading}>
                        {guideLoading ? 'Refreshing…' : 'Refresh'}
                      </button>
                    </div>
                    <div className="guide-overview">
                      <Markdown text={guide.overview} />
                    </div>
                    {guide.topics.length > 0 && (
                      <div className="topic-chips">
                        {guide.topics.map((t) => (
                          <button key={t} className="topic-chip" onClick={() => send(`Tell me about ${t}.`)}>
                            {t}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                <div className="suggestions">
                  {(guide?.suggestions.length ? guide.suggestions : FALLBACK_SUGGESTIONS).map((s) => (
                    <button key={s} className="suggestion" onClick={() => send(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        ) : (
          messages.map((m) => (
            <div key={m.id} className={`msg msg-${m.role}`}>
              <div className="msg-bubble">
                {m.role === 'assistant' ? (
                  m.content ? (
                    <Markdown text={m.content} onCite={(n) => scrollToCite(m.id, n)} />
                  ) : (
                    <span className="typing"><span></span><span></span><span></span></span>
                  )
                ) : (
                  <p>{m.content}</p>
                )}
              </div>
              {m.role === 'assistant' && m.content && !m.id.startsWith('stream-') && (
                <div className="msg-actions">
                  <button className="msg-action" onClick={() => saveAnswer(m)}>
                    {savedIds.has(m.id) ? '✓ Saved to notes' : '＋ Save to notes'}
                  </button>
                </div>
              )}
              {m.citations.length > 0 && (
                <div className="citations">
                  {m.citations.map((c, i) => (
                    <details key={i} id={`cite-${m.id}-${i + 1}`} className="citation">
                      <summary>
                        <span className="cite-num">{i + 1}</span>
                        {c.source_title}
                        <span className="cite-score">{Math.round(c.score * 100)}%</span>
                      </summary>
                      <p>{c.snippet}</p>
                      <button
                        className="cite-open"
                        onClick={() => setViewer({ sourceId: c.source_id, snippet: c.snippet })}
                      >
                        Open source ↗
                      </button>
                    </details>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div className="chat-input">
        <textarea
          value={input}
          placeholder={sources.length === 0 ? 'Add a source to start chatting…' : 'Ask a question…'}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              send()
            }
          }}
          rows={1}
        />
        <button className="btn btn-primary send-btn" onClick={() => send()} disabled={busy || !input.trim()}>
          <IconSend width={16} height={16} />
        </button>
      </div>

      {viewer && (
        <SourceViewer
          notebookId={notebookId}
          sourceId={viewer.sourceId}
          snippet={viewer.snippet}
          onClose={() => setViewer(null)}
        />
      )}
    </section>
  )
}
