import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { ChatMessage, Source } from '../types'
import { Markdown } from '../lib/markdown'
import { IconSend, IconSparkles, IconTrash } from './Icons'

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
}: {
  notebookId: string
  sources: Source[]
  selectedIds: string[] | undefined
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.getChat(notebookId).then(setMessages)
  }, [notebookId])

  useEffect(() => {
    if (sources.length === 0) {
      setSuggestions([])
      return
    }
    let active = true
    api
      .getSuggestions(notebookId)
      .then((s) => active && setSuggestions(s))
      .catch(() => active && setSuggestions([]))
    return () => {
      active = false
    }
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
              <div className="suggestions">
                {(suggestions.length ? suggestions : FALLBACK_SUGGESTIONS).map((s) => (
                  <button key={s} className="suggestion" onClick={() => send(s)}>
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          messages.map((m) => (
            <div key={m.id} className={`msg msg-${m.role}`}>
              <div className="msg-bubble">
                {m.role === 'assistant' ? (
                  m.content ? (
                    <Markdown text={m.content} />
                  ) : (
                    <span className="typing"><span></span><span></span><span></span></span>
                  )
                ) : (
                  <p>{m.content}</p>
                )}
              </div>
              {m.citations.length > 0 && (
                <div className="citations">
                  {m.citations.map((c, i) => (
                    <details key={i} className="citation">
                      <summary>
                        <span className="cite-num">{i + 1}</span>
                        {c.source_title}
                        <span className="cite-score">{Math.round(c.score * 100)}%</span>
                      </summary>
                      <p>{c.snippet}</p>
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
    </section>
  )
}
