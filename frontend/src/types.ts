export interface Notebook {
  id: string
  name: string
  description: string
  emoji: string
  created_at: string
  updated_at: string
  source_count: number
  note_count: number
}

export interface Source {
  id: string
  notebook_id: string
  title: string
  source_type: string
  origin: string
  summary: string
  status: string
  token_count: number
  metadata: Record<string, unknown>
  created_at: string
}

export interface SourceDetail extends Source {
  content: string
}

export interface Note {
  id: string
  notebook_id: string
  title: string
  content: string
  note_type: string
  kind: string
  created_at: string
  updated_at: string
}

export interface Citation {
  source_id: string
  source_title: string
  chunk_idx: number
  snippet: string
  score: number
}

export interface ChatMessage {
  id: string
  notebook_id: string
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
  created_at: string
}

export interface Podcast {
  id: string
  notebook_id: string
  title: string
  transcript: string
  audio_path: string
  audio_url: string | null
  status: string
  created_at: string
}

export interface TransformResult {
  kind: string
  title: string
  content: string
  note_id: string | null
}

export interface ProviderStatus {
  llm_provider: string
  llm_model: string
  llm_available: boolean
  llm_mode: 'model' | 'heuristic'
  embedding_provider: string
  embedding_available: boolean
  tts_provider: string
  tts_available: boolean
  notes: string[]
}

export interface SettingsView {
  llm_provider: string
  llm_base_url: string
  llm_model: string
  llm_api_key_set: boolean
  embedding_provider: string
  embedding_model: string
  tts_provider: string
}

export interface SettingsUpdate {
  llm_provider?: string
  llm_base_url?: string
  llm_model?: string
  llm_api_key?: string
  embedding_provider?: string
  embedding_model?: string
  tts_provider?: string
}

export type TransformKind =
  | 'summary'
  | 'study_guide'
  | 'faq'
  | 'timeline'
  | 'key_topics'
  | 'briefing'
  | 'mindmap'
