# 🍱 幕の内弁当コンポーザー

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/osamu-sej/ai-pop-studio?quickstart=1)

AI画像生成で作った料理画像を保管し、幕の内弁当の仕切りへドラッグ&ドロップで盛り付けて、
オリジナルのお弁当を組み立てる Web アプリです。

## 概要

```
[料理画像を生成] → [ライブラリに保管] → [仕切りへドラッグ&ドロップ] → [献立を保存]
```

1. 入れたい料理を言葉で入力して画像を生成
2. 生成画像はライブラリ（保管庫）に貯まる
3. ライブラリの画像を右の弁当の仕切りへドラッグ&ドロップ
4. 仕切り間の入れ替えや、不要な画像の削除も可能
5. 「献立を保存」で配置をサーバーに永続化

> **画像生成について**: 現在はモック実装です。プロンプトから配色を決めた
> プレースホルダー画像を生成します。OpenAI や Stability AI などの実APIへは
> `backend/services/image_generator.py` の `generate_image()` を差し替えるだけで対応できます。

## 主な機能

- **画像生成**: プロンプト＋スタイル指定から料理画像を生成（モック）
- **ライブラリ（保管庫）**: 生成画像をサーバーに保存・一覧・削除
- **弁当コンポーザー**: 6つの仕切り（ご飯／主菜／副菜×3／香の物）へ D&D で盛り付け
- **仕切り間の移動**: 仕切りから別の仕切りへドラッグして入れ替え
- **配置の永続化**: 弁当レイアウトをサーバーに保存・復元

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| フロントエンド | React 19 + Vite + TypeScript（D&Dはネイティブ HTML5 Drag&Drop） |
| バックエンド | Python + FastAPI |
| 画像生成 | Pillow によるモック生成（実APIへ差し替え可能） |
| ストレージ | ファイルベース（`backend/storage/`） |
| デプロイ | Render / GitHub Codespaces |

## プロジェクト構成

```
ai-pop-studio/
├── README.md
├── DESIGN.md                 # 設計書
├── frontend/                 # React フロントエンド
│   └── src/
│       ├── App.tsx           # 画面全体・状態管理・D&Dロジック
│       ├── bento.ts          # 仕切り定義
│       ├── dnd.ts            # ドラッグ&ドロップ用MIME
│       ├── api/client.ts     # API クライアント
│       └── components/
│           ├── ImageGenerator.tsx  # ①画像生成
│           ├── ImageLibrary.tsx    # ②画像ライブラリ（保管庫）
│           └── BentoBox.tsx        # ③弁当（仕切り＝ドロップ先）
└── backend/                  # FastAPI バックエンド
    ├── main.py
    ├── requirements.txt
    ├── routers/
    │   ├── images.py         # 画像 生成/一覧/削除 API
    │   └── bento.py          # 弁当レイアウト 取得/保存 API
    ├── services/
    │   ├── image_generator.py  # 画像生成（モック）
    │   └── storage.py          # ファイル永続化
    └── tests/
        └── test_images.py
```

## セットアップ

### GitHub Codespaces（推奨）

上部の **「Open in GitHub Codespaces」** ボタンをクリックすると、開発環境が自動構築され、
フロントエンド（5173）とバックエンド（8000）が起動します。

### 手動セットアップ

```bash
# バックエンド
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# フロントエンド（別ターミナル）
cd frontend
npm install
npm run dev
```

ブラウザで http://localhost:5173 を開きます（`/api` はバックエンドへプロキシされます）。

または `make dev` で両方同時に起動できます。

> 日本語テキストをモック画像に描画するため、ローカルでは日本語フォント
> （例: `fonts-ipafont-gothic`）があるときれいに表示されます。無い場合は英数字に
> フォールバックします。

## API

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/images/generate` | プロンプトから画像を生成・保管 |
| GET | `/api/images` | 保管画像の一覧（新しい順） |
| DELETE | `/api/images/{id}` | 画像を削除（弁当配置からも除去） |
| GET | `/api/bento` | 現在の弁当レイアウトを取得 |
| PUT | `/api/bento` | 弁当レイアウトを保存 |
| GET | `/media/images/{id}.png` | 生成画像の配信 |

## テスト

```bash
cd backend
python -m pytest tests/ -v
```

## ライセンス

Private
