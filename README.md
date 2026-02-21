# AI POP Studio

セブンイレブン向けPOP（Point of Purchase）自動生成アプリ

## 概要

PDFカタログから商品情報を自動抽出し、ExcelのPOPテンプレートに挿入するWebアプリケーション。

## 主要機能

1. **PDF商品情報抽出** - Claude Vision APIを使用してPDFカタログから商品名・価格・画像等を抽出
2. **POP自動生成** - 抽出した情報をExcelテンプレートに自動挿入
3. **テンプレート管理** - 複数のPOPテンプレートを管理・選択

## 技術スタック

- **バックエンド**: FastAPI (Python)
- **フロントエンド**: React / Vite
- **AI**: Claude Vision API (Anthropic)
- **開発環境**: GitHub Codespaces

## セットアップ

### バックエンド

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

### 環境変数

`.env` ファイルをプロジェクトルートに作成:

```
ANTHROPIC_API_KEY=your_api_key_here
```

## ディレクトリ構成

```
ai-pop-studio/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPIエントリーポイント
│   │   ├── routers/         # APIルーター
│   │   ├── services/        # ビジネスロジック
│   │   │   ├── pdf_extractor.py   # PDF情報抽出
│   │   │   └── excel_writer.py    # Excel POP生成
│   │   └── models/          # データモデル
│   ├── templates/           # Excelテンプレート
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Reactコンポーネント
│   │   ├── pages/           # ページコンポーネント
│   │   └── services/        # API通信
│   └── package.json
├── .devcontainer/
│   └── devcontainer.json
├── DESIGN.md
└── README.md
```

## 技術的な注意事項

### PDF処理
- 対象PDFは画像ベース（埋め込みテキストなし）
- Claude Vision APIによる処理が必須（OCRでは精度不十分）

### Excel処理
- テンプレートはDrawingML（XML）で描画要素を管理
- PythonのElementTreeはXML名前空間プレフィックスを破損するため使用禁止
- 正規表現による文字列操作でXMLを直接編集する
