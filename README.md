# POP Generator - セブンイレブン POP自動生成アプリ

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/osamu-sej/ai-pop-studio)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/osamu-sej/ai-pop-studio?quickstart=1)

商品案内PDFから商品情報を自動抽出し、Excelテンプレートに挿入してPOPを生成するWebアプリケーション。

## クイックスタート

### 方法1: Render にデプロイ（推奨）

上の **「Deploy to Render」** ボタンをクリックすると、無料でクラウド上にアプリがデプロイされます。

1. ボタンをクリック → Render のセットアップ画面が開きます
2. GitHub アカウントで認証
3. 自動的にビルド・デプロイされます
4. 発行されたURLからアプリにアクセスできます

### 方法2: GitHub Codespaces

**「Open in GitHub Codespaces」** ボタンをクリックすると、ブラウザ上で開発環境が自動構築されます。

1. ボタンをクリック → Codespace が作成されます
2. 依存関係が自動インストールされます
3. フロントエンド（React）とバックエンド（FastAPI）が自動起動します
4. ブラウザが自動で開き、アプリが使えます

## 概要
セブンイレブンの新商品POPを作成する作業を自動化します。
**従来のワークフロー（手作業）:**
```
商品案内PDF → 手動で商品名・売価・写真をコピー → Excelテンプレートに貼り付け → 税込価格を計算
```
**このアプリのワークフロー（自動化）:**
```
商品案内PDFをアップロード → 商品情報を自動抽出 → テンプレート選択 → POP自動生成・ダウンロード
```
## 主な機能
- **PDF解析**: 商品案内PDFから商品名・売価・写真・説明文を自動抽出
- **税込価格計算**: 税抜売価から税込価格を自動計算（8%/10%対応、税率変更可能）
- **テンプレート管理**: 複数のExcel POPテンプレートに対応（初期2-3個、最大10個）
- **POP生成**: 背景デザインを保持したまま商品情報を差し替え
- **マルチユーザー**: 複数ユーザーが使用可能なWeb UI
## 技術スタック
| レイヤー | 技術 |
|---------|------|
| フロントエンド | React + Vite + TypeScript |
| バックエンド | Python + FastAPI |
| PDF解析 | PyMuPDF + Claude Vision API |
| Excel操作 | openpyxl + XML直接操作 |
| デプロイ | Render / GitHub Codespaces |
## プロジェクト構成
```
pop-generator/
├── README.md
├── docs/
│   └── DESIGN.md          # 設計書
├── frontend/              # React フロントエンド
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── PdfUploader.tsx
│       │   ├── ProductList.tsx
│       │   ├── TemplateSelector.tsx
│       │   └── PopPreview.tsx
│       └── api/
│           └── client.ts
├── backend/               # FastAPI バックエンド
│   ├── requirements.txt
│   ├── main.py
│   ├── routers/
│   │   ├── pdf.py         # PDF解析API
│   │   ├── pop.py         # POP生成API
│   │   └── templates.py   # テンプレート管理API
│   ├── services/
│   │   ├── pdf_parser.py  # PDF情報抽出
│   │   ├── image_extractor.py  # 商品写真抽出
│   │   ├── excel_writer.py     # Excel差し替え
│   │   └── tax_calculator.py   # 税込計算
│   └── templates/         # Excelテンプレート格納
│       └── .gitkeep
├── .devcontainer/         # Codespaces設定
│   └── devcontainer.json
└── .env.example           # 環境変数サンプル
```
## セットアップ
### GitHub Codespaces（推奨）
1. 上部の [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/osamu-sej/ai-pop-studio?quickstart=1) ボタンをクリック
2. 自動的に開発環境がセットアップされ、アプリが起動します
3. ポート 5173 でフロントエンドが自動的にブラウザで開きます
### 手動セットアップ
```bash
# バックエンド
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# フロントエンド
cd frontend
npm install
npm run dev
```
### 環境変数
```bash
cp .env.example .env
# .env を編集して Claude API キーを設定
ANTHROPIC_API_KEY=your-api-key-here
```
## 使い方
1. ブラウザでアプリにアクセス
2. 商品案内PDFをアップロード
3. 抽出された商品一覧から、POPにしたい商品を選択
4. テンプレートを選択
5. 税率を確認（8% or 10%）
6. 「POP生成」ボタンをクリック
7. 完成したExcelをダウンロード
## 開発フェーズ
| Phase | 内容 | 状態 |
|-------|------|------|
| Phase 1 | PDF情報抽出の検証 | 完了 |
| Phase 2 | Excelテンプレート差し替え検証 | 完了 |
| Phase 3 | バックエンドAPI開発 | 未着手 |
| Phase 4 | フロントエンドUI開発 | 未着手 |
| Phase 5 | テンプレート管理・税率管理 | 未着手 |
| Phase 6 | テスト・デプロイ | 未着手 |
## ライセンス
Private - 社内利用専用
