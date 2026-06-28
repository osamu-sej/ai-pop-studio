import type {
  ChatMessage,
  GlobalSearchHit,
  Note,
  Notebook,
  NotebookGuide,
  Podcast,
  ProviderStatus,
  SettingsUpdate,
  SettingsView,
  Source,
  SourceDetail,
  TransformKind,
  TransformResult,
} from './types'

async function http<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  // system
  status: () => http<ProviderStatus>('/api/status'),
  globalSearch: (query: string, topK = 20) =>
    http<GlobalSearchHit[]>('/api/search', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    }),
  getSettings: () => http<SettingsView>('/api/settings'),
  updateSettings: (patch: SettingsUpdate) =>
    http<ProviderStatus>('/api/settings', { method: 'PUT', body: JSON.stringify(patch) }),

  // notebooks
  listNotebooks: () => http<Notebook[]>('/api/notebooks'),
  getNotebook: (id: string) => http<Notebook>(`/api/notebooks/${id}`),
  createNotebook: (name: string, emoji: string, description = '') =>
    http<Notebook>('/api/notebooks', {
      method: 'POST',
      body: JSON.stringify({ name, emoji, description }),
    }),
  updateNotebook: (id: string, patch: Partial<Pick<Notebook, 'name' | 'description' | 'emoji'>>) =>
    http<Notebook>(`/api/notebooks/${id}`, { method: 'PATCH', body: JSON.stringify(patch) }),
  deleteNotebook: (id: string) => http<void>(`/api/notebooks/${id}`, { method: 'DELETE' }),

  // sources
  listSources: (nb: string) => http<Source[]>(`/api/notebooks/${nb}/sources`),
  getSource: (nb: string, id: string) => http<SourceDetail>(`/api/notebooks/${nb}/sources/${id}`),
  addText: (nb: string, title: string, content: string) =>
    http<Source>(`/api/notebooks/${nb}/sources/text`, {
      method: 'POST',
      body: JSON.stringify({ title, content }),
    }),
  addUrl: (nb: string, url: string) =>
    http<Source>(`/api/notebooks/${nb}/sources/url`, {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),
  addFile: async (nb: string, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    const res = await fetch(`/api/notebooks/${nb}/sources/file`, { method: 'POST', body: fd })
    if (!res.ok) {
      let detail = res.statusText
      try {
        detail = (await res.json()).detail ?? detail
      } catch {
        /* ignore */
      }
      throw new Error(detail)
    }
    return (await res.json()) as Source
  },
  deleteSource: (nb: string, id: string) =>
    http<void>(`/api/notebooks/${nb}/sources/${id}`, { method: 'DELETE' }),
  reindexSource: (nb: string, id: string) =>
    http<Source>(`/api/notebooks/${nb}/sources/${id}/reindex`, { method: 'POST' }),

  // notes
  listNotes: (nb: string) => http<Note[]>(`/api/notebooks/${nb}/notes`),
  createNote: (nb: string, title: string, content = '') =>
    http<Note>(`/api/notebooks/${nb}/notes`, {
      method: 'POST',
      body: JSON.stringify({ title, content }),
    }),
  updateNote: (nb: string, id: string, patch: Partial<Pick<Note, 'title' | 'content'>>) =>
    http<Note>(`/api/notebooks/${nb}/notes/${id}`, { method: 'PATCH', body: JSON.stringify(patch) }),
  deleteNote: (nb: string, id: string) =>
    http<void>(`/api/notebooks/${nb}/notes/${id}`, { method: 'DELETE' }),

  // chat
  getChat: (nb: string) => http<ChatMessage[]>(`/api/notebooks/${nb}/chat`),
  sendChat: (nb: string, message: string, sourceIds?: string[]) =>
    http<ChatMessage>(`/api/notebooks/${nb}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message, source_ids: sourceIds ?? null }),
    }),
  clearChat: (nb: string) => http<void>(`/api/notebooks/${nb}/chat`, { method: 'DELETE' }),
  getSuggestions: (nb: string) => http<string[]>(`/api/notebooks/${nb}/chat/suggestions`),
  getGuide: (nb: string, force = false) =>
    http<NotebookGuide>(`/api/notebooks/${nb}/studio/guide${force ? '?force=true' : ''}`),
  sendChatStream: async (
    nb: string,
    message: string,
    sourceIds: string[] | undefined,
    handlers: {
      onToken: (t: string) => void
      onDone: (m: ChatMessage) => void
      onError: (e: string) => void
    },
  ) => {
    const res = await fetch(`/api/notebooks/${nb}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, source_ids: sourceIds ?? null }),
    })
    if (!res.ok || !res.body) {
      handlers.onError(res.statusText || 'Stream failed')
      return
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const blocks = buffer.split('\n\n')
      buffer = blocks.pop() ?? ''
      for (const block of blocks) {
        const line = block.split('\n').find((l) => l.startsWith('data:'))
        if (!line) continue
        try {
          const evt = JSON.parse(line.slice(5).trim())
          if (evt.type === 'token') handlers.onToken(evt.text)
          else if (evt.type === 'done') handlers.onDone(evt.message)
        } catch {
          /* ignore malformed chunk */
        }
      }
    }
  },

  // studio
  transform: (nb: string, kind: TransformKind, sourceIds?: string[]) =>
    http<TransformResult>(`/api/notebooks/${nb}/studio/transform`, {
      method: 'POST',
      body: JSON.stringify({ kind, source_ids: sourceIds ?? null, save_as_note: true }),
    }),
  listPodcasts: (nb: string) => http<Podcast[]>(`/api/notebooks/${nb}/studio/podcasts`),
  createPodcast: (
    nb: string,
    opts: { style: string; length: string; title?: string; source_ids?: string[] },
  ) =>
    http<Podcast>(`/api/notebooks/${nb}/studio/podcasts`, {
      method: 'POST',
      body: JSON.stringify({
        style: opts.style,
        length: opts.length,
        title: opts.title ?? null,
        source_ids: opts.source_ids ?? null,
      }),
    }),
  deletePodcast: (nb: string, id: string) =>
    http<void>(`/api/notebooks/${nb}/studio/podcasts/${id}`, { method: 'DELETE' }),
}
