# Aurora Notebook — 設計書 / Design Document

NotebookLM を超える自由度を持つ、**ローカルファースト / API 不要**のリサーチノートブック。
本書は、最優先要件である「**API を使わずに実現できるか**」への結論と、その実現方式をまとめる。

---

## 0. 結論（最優先論点への回答）

> **「API を使わない設計で実現可能か？ それが最優先。」**

### ✅ 結論：**完全に API 不要で実現可能。本リポジトリはその設計で実装済み。**

NotebookLM の中核機能（取り込み・要約・引用付きチャット・スタディガイド・音声概要）は、
すべて**ローカルで動作する無料技術**に置き換え可能で、実際に置き換えた。

| 機能 | NotebookLM（クラウドAPI） | Aurora（API不要・ローカル） | 追加コスト |
|------|--------------------------|------------------------------|-----------|
| LLM（チャット/要約/生成） | Google Gemini | **Ollama**（Llama 3.1 / Qwen2.5 / Gemma2 等） | **0円** |
| 埋め込み（意味検索） | クラウド埋め込み | **nomic-embed-text** / sentence-transformers / 内蔵ハッシュ埋め込み | **0円** |
| PDF/文書解析 | クラウド | **PyMuPDF / python-docx**（ローカル） | **0円** |
| Web取り込み | クラウド | **httpx + BeautifulSoup**（ローカル） | **0円** |
| YouTube取り込み | クラウド | **youtube-transcript-api**（公開字幕） | **0円** |
| 音声→文字（STT） | クラウド | **faster-whisper**（ローカル, 任意） | **0円** |
| 音声概要（TTS） | クラウド | **piper / pyttsx3**（ローカル, 任意） | **0円** |
| データ保存 | クラウド | **SQLite**（単一ファイル） | **0円** |

さらに **何のモデルも入れていない状態でもアプリは完全に動作する**よう、
古典的 NLP による**ヒューリスティック・エンジン**（抽出型要約・キーワード接地応答・
台本生成）を内蔵した。これにより「インストール直後・オフライン・APIキー無し」でも
全機能が使え、Ollama を入れた瞬間に**自動でフル品質へ昇格**する。

### 品質に関する正直な評価

ユーザー指摘の通り「無料 API はほぼ劣化」になりがちなので、**無料 API には依存しない**方針を採った。

- **推奨（ローカル Ollama）**：8B クラスのモデルでも、要約・引用付きQA・台本生成は実用品質。
  量子化モデルなら一般的なノートPC（16GB RAM）で動作。GPU があれば 14B〜32B でさらに高品質。
  **クォータ無し・完全プライベート・オフライン**。これが NotebookLM に対する明確な優位点。
- **ヒューリスティック（モデル無し）**：抽象的要約や推論はできないが、抽出型で「動く」。
  デモ・低スペック環境・プライバシー最優先用途のフォールバック。
- **任意のクラウド API**：速度が欲しい上級者向けの“アクセラレータ”として**選択可能**だが、
  既定では使わない。`AURORA_LLM_PROVIDER=openai` で任意の OpenAI 互換エンドポイント
  （LM Studio / Groq 無料枠 / OpenRouter / OpenAI）に差し替え可能。

→ **設計の肝**：「AI プロバイダ」を抽象化し、`ローカル ↔ クラウド ↔ ヒューリスティック`を
環境変数だけで切替可能にした。コードのどこにも**有料 API への依存を埋め込んでいない**。

---

## 1. システム概要

Aurora は 3 ペイン構成（NotebookLM 流）の SPA と、FastAPI バックエンドからなる。

```
[Sources]            [Chat]                    [Studio]
 取り込み/選択   →   引用付きRAGチャット   →   要約/学習ガイド/FAQ/
 PDF·Web·YT·音声      意味+語彙ハイブリッド検索   タイムライン/ブリーフィング/
                                                  マインドマップ/ポッドキャスト
```

### 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | React 19 + Vite + TypeScript |
| バックエンド | Python 3.12 + FastAPI |
| データベース | SQLite（埋め込み・サーバー不要） |
| ベクトル検索 | numpy（コサイン類似度, インライン格納） |
| LLM | Ollama（既定） / OpenAI 互換 / ヒューリスティック |
| 埋め込み | nomic-embed-text / sentence-transformers / ハッシュ埋め込み |
| 文書解析 | PyMuPDF, python-docx, BeautifulSoup, youtube-transcript-api |
| STT/TTS | faster-whisper / piper・pyttsx3（いずれも任意・ローカル） |

---

## 2. AI レイヤー設計（差し替え可能な“頭脳”）

`backend/app/ai/` に全認知機能を小さなインターフェースで隔離する。

```
ai/llm.py         BaseLLM ← OllamaLLM / OpenAICompatibleLLM
ai/embeddings.py  BaseEmbedder ← Ollama / SentenceTransformer / Hashing
ai/tts.py         BaseTTS ← Piper / Pyttsx3 / None
ai/heuristics.py  モデル不要の抽出型 NLP（要約/QA/台本/各種変換）
ai/engine.py      高水準関数。モデル可否を見て model ↔ heuristic を透過切替
ai/prompts.py     実モデル用プロンプト群
```

**設計原則**：アプリ本体（services / routers）は `engine.answer_question()` や
`engine.transform()` だけを呼ぶ。どのエンジンが使われたかを意識しない。
`engine` 内で `get_llm().available()` を見て、利用可能なら実モデル、
不可ならヒューリスティックに自動フォールバックする（例外時も安全に降格）。

### 埋め込みの 3 段フォールバック

`auto` 設定時は **Ollama → sentence-transformers → 内蔵ハッシュ埋め込み**の順で
利用可能なものを採用。ハッシュ埋め込みは依存ゼロ（numpy のみ）で、
単語/2-gram/文字3-gram の符号付きハッシュにより**語彙・形態の重なり**を捉える。
モデルが一切無くてもベクトル検索が機能する。

---

## 3. 取り込みパイプライン

```
extract（PDF/DOCX/Web/YouTube/Text/Audio）
  → source 保存（SQLite）
  → chunking（段落優先・境界考慮・オーバーラップ）
  → embeddings（書き込み時に生成しインライン格納）
  → chunks 保存
  → 要約生成（engine.summarize_source）
```

検索・チャットを高速化するため、埋め込みと要約は**取り込み時**に確定させる。
音声ファイルは faster-whisper 未導入時、クラッシュせず「文字起こし待ち」状態で保存し、
導入後に再インデックス可能（`reindex_source`）。

---

## 4. 検索（ハイブリッド）

引用の頑健性は、**意味（ベクトル）**と**語彙（キーワード）**の併用で担保する。

- ベクトル：取り込み時に L2 正規化済み → 内積＝コサイン類似度を numpy で一括計算。
- 語彙：候補チャンク集合に対する軽量 **BM25** スコア。固有名詞・数値・略語に強い。
- 統合：`score = α·semantic + (1−α)·lexical`（既定 α=0.6）。正規化後に加重合成。

個人/研究スケール（数千チャンク）ではインメモリ計算で十分高速。将来的に大規模化する
場合は同一インターフェースのまま `sqlite-vec` 等へ差し替え可能。

---

## 5. チャット（引用付き RAG）

```
ユーザー発話を保存
  → hybrid_search で関連チャンク取得（選択ソースに限定可）
  → engine.answer_question(question, context_blocks)
       実モデル: RAG プロンプト（[n] で引用指示）
       ヒューリスティック: 質問語と重なる文を抽出
  → 取得チャンクを出典として citations 化（ソース別に上位を重複排除）
  → アシスタント応答＋引用を保存
```

UI では各引用を折りたたみ表示し、**出典タイトル・該当スニペット・関連度%**を提示。
回答の検証可能性（grounding）を最優先にした。

---

## 6. スタディオ（変換 + 音声概要）

### 変換（各々ノートとして保存・編集可能）
Summary / Study Guide / FAQ / Timeline / Key Topics / Briefing / Mind Map。
実モデル時はプロンプトで Markdown 生成、モデル無し時は抽出型アルゴリズムで生成。

### 音声概要（ポッドキャスト）
- スタイル：conversational / deep_dive / debate / solo、長さ：short/medium/long。
- **台本**：実モデルは JSON 形式の二者対話を生成、モデル無し時は要約文から
  ホスト交互の対話を構成。台本は常に得られる。
- **音声**：piper（高品質ニューラル）または pyttsx3（OS音声）が在ればローカル合成して
  WAV を連結。無ければ**台本のみ**（後から任意の TTS に流せる）。

---

## 7. データモデル（SQLite）

```
notebooks(id, name, description, emoji, created_at, updated_at)
sources(id, notebook_id, title, source_type, origin, content, summary, status, metadata, token_count, created_at)
chunks(id, source_id, notebook_id, idx, text, embedding(BLOB float32), dim)
notes(id, notebook_id, title, content, note_type, kind, created_at, updated_at)
chat_messages(id, notebook_id, role, content, citations(JSON), created_at)
podcasts(id, notebook_id, title, transcript, audio_path, status, created_at)
```

埋め込みは float32 を packed bytes で格納し、精度劣化なく省サイズに往復させる。
外部キーは `ON DELETE CASCADE`：ノートブック削除で関連ソース/チャンク/ノート等を一掃。

---

## 8. API 設計（抜粋）

```
GET    /api/status                                   エンジン稼働状況
GET    /api/notebooks                                ノートブック一覧
POST   /api/notebooks                                作成
GET/PATCH/DELETE /api/notebooks/{id}

GET    /api/notebooks/{id}/sources                   ソース一覧
POST   /api/notebooks/{id}/sources/text|url|file     取り込み
GET/DELETE /api/notebooks/{id}/sources/{sid}

POST   /api/notebooks/{id}/search                    ハイブリッド検索
GET/POST/DELETE /api/notebooks/{id}/chat             履歴/送信/クリア

POST   /api/notebooks/{id}/studio/transform          変換生成
GET/POST /api/notebooks/{id}/studio/podcasts         音声概要 一覧/生成
GET    /api/notebooks/{id}/studio/podcasts/{pid}/audio  WAV 取得

CRUD   /api/notebooks/{id}/notes                      ノート
```

---

## 9. 配備

- **開発**：`make dev`（backend:8000 + Vite:5173、`/api` をプロキシ）。
- **本番**：`make serve`（フロントをビルドし、FastAPI が単一プロセスで SPA も配信）。
- 依存はすべて GPU 不要・APIキー不要でインストール可能。ローカル AI 拡張
  （sentence-transformers / faster-whisper / pyttsx3）は `requirements-extras.txt` に分離。

---

## 10. テスト

`backend/tests/` は**完全オフライン**（heuristic + hashing）で 23 ケースを実行：
ノートブック CRUD、ソース取り込み（テキスト/PDF）、検索の関連性、引用付きチャット、
全 7 変換、音声概要、ユニット（チャンキング/ハッシュ埋め込みの類似度/要約）。
`make test` で実行。ネットワーク・モデル・APIキー不要。

---

## 11. 既知の限界と将来拡張

| # | 項目 | 現状 | 拡張案 |
|---|------|------|--------|
| 1 | ベクトル検索のスケール | インメモリ numpy（個人/研究規模に最適） | `sqlite-vec`/FAISS へ差し替え（同一IF） |
| 2 | 応答ストリーミング | 一括返答 | SSE で逐次表示（providerにstream実装） |
| 3 | 多言語要約の精度 | モデル依存 | 多言語モデル（Qwen2.5等）を既定候補に |
| 4 | TTS の声質 | pyttsx3 は素朴 | piper 音声の同梱手順を整備 |
| 5 | 画像/図表の取り込み | テキスト主体 | ローカル Vision モデル（llava 等）連携 |

**まとめ**：最優先要件「API 不要」は満たした上で、NotebookLM の主要機能を網羅し、
さらに自由度（モデル選択・自己ホスト・オフライン・拡張容易性）で上回る設計とした。
