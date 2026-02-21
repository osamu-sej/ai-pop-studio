# POP Generator 設計書
## 1. システム概要
### 1.1 目的
セブンイレブンの新商品POP作成作業を自動化する。
商品案内PDFから情報を抽出し、Excelテンプレートに自動挿入してPOPを生成する。
### 1.2 ユーザー
- OP情報チームのメンバー（複数人が使用可能）
- ITリテラシー：一般的なオフィスワーカーレベル
### 1.3 ワークフロー
```
[ユーザー]
  ↓ PDFアップロード
[PDF解析エンジン]
  ↓ 商品情報JSON（名前・売価・写真・説明文）
[ユーザー]
  ↓ 商品選択 + テンプレート選択 + 税率確認
[POP生成エンジン]
  ↓ Excelファイル
[ユーザー]
  ↓ ダウンロード・印刷
```
---
## 2. PDF解析
### 2.1 入力PDFの特性（検証結果）
- **形式**: 画像ベースPDF（各ページが1枚のJPEG画像として埋め込み）
- **テキスト埋め込み**: なし（OCRまたはAI Visionが必須）
- **レイアウト**: PDFの種類によって異なる
  - 写真案内PDF: 1ページ4商品（2×2グリッド）
  - 他のPDF: 1ページの商品数がバラバラ
- **含まれる情報**:
  - 商品名
  - 商品コード
  - カテゴリ（おにぎり、弁当等）
  - 売価（税抜）
  - 原価
  - 商品写真
  - 説明文（○で始まる箇条書き）
  - 納品開始日・発注開始日
  - 発注グループ
### 2.2 抽出方式
**採用方式: Claude Vision API**
| 方式 | 精度 | コスト | 柔軟性 |
|------|------|--------|--------|
| ~~Tesseract OCR~~ | △ 70-80% | 無料 | ✗ 固定レイアウトのみ |
| **Claude Vision API** | **◎ 95%以上** | **API利用料** | **◎ レイアウト自動対応** |
**選定理由**:
- PDFが画像ベースのためOCRが必須
- Tesseract OCRは日本語精度が不十分（商品名・説明文の誤認識多い）
- Claude Vision APIはレイアウトを理解して構造化データを返せる
- PDFの種類によってレイアウトが異なるため、固定位置クロップでは対応不可
### 2.3 テキスト抽出フロー
```
PDF → ページ単位でレンダリング（300DPI）
    → Claude Vision APIに送信
    → プロンプト: 「各商品の商品名・売価・説明文を抽出しJSON形式で返してください」
    → 構造化JSON取得
```
### 2.4 商品写真抽出フロー
```
PDF → ページ単位でレンダリング（300DPI）
    → Claude Vision APIに送信
    → プロンプト: 「各商品写真の位置座標（バウンディングボックス）を返してください」
    → 座標取得 → 画像クロップ
```
**注意**: PDFのレイアウトがバラバラなので、固定座標でのクロップではなく
Claude Vision APIに座標を返させる動的な方式を採用する。
### 2.5 抽出データ構造
```json
{
  "products": [
    {
      "product_name": "おおきなおむすび しゃけわかめ",
      "product_code": "041744",
      "category": "おにぎり",
      "selling_price": 220,
      "description": "定番商品の約1.5倍量の御飯を使用したおむすび。...",
      "delivery_start": "2026/02/10",
      "order_start": "2026/02/09",
      "photo_bbox": {"x": 500, "y": 60, "w": 300, "h": 210},
      "page_number": 1
    }
  ]
}
```
---
## 3. Excelテンプレート操作
### 3.1 テンプレート構造（検証結果）
ExcelのPOPはセルベースではなく、**DrawingML（XML）** で構成されている。
```
.xlsx (ZIP)
├── xl/
│   ├── worksheets/
│   │   └── sheet1.xml          ← セル値（売価・税率・数式）
│   ├── drawings/
│   │   ├── drawing1.xml        ← Drawing定義（テキスト・画像配置）
│   │   └── _rels/
│   │       └── drawing1.xml.rels  ← 画像ファイルへの参照
│   └── media/
│       ├── image1.jpeg         ← 背景デザイン（固定）
│       ├── image2.jpeg         ← 背景デザイン（固定）
│       ├── image6.jpeg         ← 商品写真TOP（差し替え対象）
│       └── image7.png          ← 商品写真BOTTOM（差し替え対象）
```
### 3.2 差し替え対象の一覧（Sheet ① の例）
| 要素 | 場所 | 識別方法 | 差し替え内容 |
|------|------|----------|-------------|
| TOP商品名 | Anchor 0 / Shape '正方形/長方形 8' | Shape名で検索 | 商品名テキスト |
| TOP税抜売価 | Anchor 0 / Shape '正方形/長方形 9' | Shape名で検索 | 「{価格}円*」 |
| TOP税込価格 | Anchor 0 / Shape '正方形/長方形 10' | Shape名で検索 | 「(税込:{税込価格}円)」|
| TOPおすすめ | Anchor 1 | Anchor番号 | おすすめ文言 |
| BOTTOM商品名 | Anchor 2 / Shape '正方形/長方形 54' | Shape名で検索 | 商品名テキスト |
| BOTTOM税抜売価 | Anchor 2 / Shape '正方形/長方形 50' | Shape名で検索 | 「{価格}円*」 |
| BOTTOMおすすめ1 | Anchor 3 | Anchor番号 | おすすめ文言 |
| BOTTOMおすすめ2 | Anchor 4 | Anchor番号 | おすすめ文言（2行目）|
| BOTTOM税込価格 | Anchor 7 | Anchor番号 | 「(税込:{税込価格}円)」|
| TOP商品写真 | Anchor 5 / rId7 → image6.jpeg | rId / media | 商品写真画像 |
| BOTTOM商品写真 | Anchor 6 / rId8 → image7.png | rId / media | 商品写真画像 |
| TOP売価セル | Sheet1 / S36 | セル参照 | 税抜売価（数値） |
| TOP税率セル | Sheet1 / T36 | セル参照 | 税率（1.08 or 1.10）|
| BOTTOM売価セル | Sheet1 / S58 | セル参照 | 税抜売価（数値） |
| BOTTOM税率セル | Sheet1 / T58 | セル参照 | 税率（1.08 or 1.10）|
### 3.3 Excel操作方式
**採用方式: XML文字列直接操作**
| 方式 | 結果 |
|------|------|
| ~~openpyxl標準API~~ | ✗ DrawingMLのShape/テキストボックス操作に非対応 |
| ~~ElementTree XML操作~~ | ✗ 名前空間プレフィックスが変更されExcelが読めなくなる |
| **正規表現による文字列操作** | **◎ 名前空間完全保持、差し替え成功** |
**重要な知見（検証で発見）:**
- Python `xml.etree.ElementTree` は書き出し時に `xdr:` → `ns0:`、`a:` → `ns1:` に
  名前空間プレフィックスを勝手に変更する
- Excelはこの変更されたプレフィックスを認識できず、描画が全て消える
- **対策**: XMLをテキスト（文字列）として扱い、正規表現で差し替える
- この方式なら名前空間が完全に保持される（出現回数一致を検証済み）
### 3.4 差し替え処理フロー
```
1. XLSXファイルをZIP展開
2. drawing*.xml をテキストとして読み込み
3. Shape名でテキスト要素を特定し、正規表現で差し替え
4. Anchor番号でおすすめ文言を差し替え
5. xl/media/ 内の商品写真ファイルを上書き
6. sheet*.xml 内のセル値（売価・税率）を正規表現で差し替え
7. ZIP再パッケージ → XLSX完成
```
### 3.5 画像差し替え時の注意事項（検証で発見した課題）
**課題1: アスペクト比の維持**
- 差し替え画像のサイズがテンプレートの画像枠と異なるとき、画像が潰れる
- **対策**: テンプレートの画像枠サイズ（EMU単位）を取得し、
  そのアスペクト比に合わせてリサイズ・フィット（letterbox）してから差し替え
**課題2: Z-order（前面/背面）**
- 差し替えた画像が背景画像の後ろに隠れることがある
- **対策**: 差し替え要素は常に前面に配置する
  - DrawingML内のAnchorの順序を調整
  - または画像ファイルの直接上書き（同一rIdを使用）で対応
---
## 4. 税込価格計算
### 4.1 仕様
- 税率: 8%（1.08）と 10%（1.10）の2種類
- 計算式: `税込価格 = 税抜売価 × 税率`
- 表示: 小数第2位まで表示（例: 237.60円）
- 税率変更: 将来の税率変更に対応できるよう、設定値として管理
### 4.2 税率の自動判定
- 食品（おにぎり、弁当、飲料等）→ 軽減税率 8%
- 酒類、日用品 → 標準税率 10%
- UI上で手動変更も可能
---
## 5. テンプレート管理
### 5.1 テンプレート登録
各テンプレートには以下のメタデータを定義する:
```json
{
  "template_id": "new_pop_np",
  "name": "新規POP",
  "file": "260223週_新規POP_NP__.xlsx",
  "sheets": [
    {
      "sheet_name": "①",
      "products_per_sheet": 2,
      "drawing_file": "drawing1.xml",
      "replacements": {
        "top": {
          "product_name_shape": "正方形/長方形 8",
          "price_excl_shape": "正方形/長方形 9",
          "price_incl_shape": "正方形/長方形 10",
          "recommendation_anchor": 1,
          "photo_rid": "rId7",
          "photo_media": "image6.jpeg",
          "price_cell": "S36",
          "tax_rate_cell": "T36"
        },
        "bottom": {
          "product_name_shape": "正方形/長方形 54",
          "price_excl_shape": "正方形/長方形 50",
          "price_incl_anchor": 7,
          "recommendation_anchors": [3, 4],
          "photo_rid": "rId8",
          "photo_media": "image7.png",
          "price_cell": "S58",
          "tax_rate_cell": "T58"
        }
      }
    }
  ]
}
```
### 5.2 テンプレート拡張
- 初期: 2-3テンプレート
- 将来: 最大10テンプレート
- 新テンプレート追加手順:
  1. ExcelファイルをZIP展開して構造解析
  2. Drawing XML内のShape名・Anchor番号を特定
  3. メタデータJSON を作成
  4. テンプレートフォルダに配置
---
## 6. API設計
### 6.1 PDF解析
```
POST /api/pdf/parse
Content-Type: multipart/form-data
Body: file=<PDF>
Response:
{
  "products": [
    {
      "product_name": "おおきなおむすび しゃけわかめ",
      "selling_price": 220,
      "description": "...",
      "photo_base64": "data:image/png;base64,...",
      "page_number": 1
    }
  ],
  "total_pages": 41,
  "total_products": 80
}
```
### 6.2 POP生成
```
POST /api/pop/generate
Content-Type: application/json
Body:
{
  "template_id": "new_pop_np",
  "products": [
    {
      "product_name": "おおきなおむすび しゃけわかめ",
      "selling_price": 220,
      "tax_rate": 1.08,
      "recommendation": "定番商品の約1.5倍量の御飯を使用したおむすび",
      "photo_base64": "data:image/png;base64,..."
    }
  ]
}
Response: Excel file (application/octet-stream)
```
### 6.3 テンプレート一覧
```
GET /api/templates
Response:
{
  "templates": [
    {
      "template_id": "new_pop_np",
      "name": "新規POP",
      "products_per_sheet": 2,
      "total_sheets": 6
    }
  ]
}
```
---
## 7. フロントエンド画面設計
### 7.1 メイン画面（1画面構成）
```
┌──────────────────────────────────────────┐
│  🏪 POP Generator                        │
├──────────────────────────────────────────┤
│                                          │
│  ① PDFアップロード                       │
│  ┌─────────────────────────────┐        │
│  │  📄 ドラッグ&ドロップ        │        │
│  │     または ファイル選択       │        │
│  └─────────────────────────────┘        │
│                                          │
│  ② 商品一覧（抽出結果）                  │
│  ┌──────┬──────┬──────┬──────┐        │
│  │☑ 写真│商品名 │売価  │税率  │        │
│  ├──────┼──────┼──────┼──────┤        │
│  │☑ 🖼 │しゃけ │ 220 │ 8%  │        │
│  │☑ 🖼 │カレー │ 178 │ 8%  │        │
│  │☐ 🖼 │焼鳥重 │ 648 │ 8%  │        │
│  └──────┴──────┴──────┴──────┘        │
│                                          │
│  ③ テンプレート選択                      │
│  ┌─────────────────────────────┐        │
│  │ 📋 新規POP  ○ プライチPOP   │        │
│  └─────────────────────────────┘        │
│                                          │
│  ④ POP生成                              │
│  ┌─────────────────────────────┐        │
│  │     [ POP生成・ダウンロード ]  │        │
│  └─────────────────────────────┘        │
│                                          │
└──────────────────────────────────────────┘
```
### 7.2 操作フロー
1. PDFをドラッグ&ドロップ → 自動で解析開始
2. 商品一覧表示 → チェックボックスで選択
3. 各商品の売価・税率・おすすめ文言は編集可能
4. テンプレート選択
5. 「POP生成・ダウンロード」→ Excelダウンロード
---
## 8. 開発環境
### 8.1 GitHub Codespaces設定
```json
// .devcontainer/devcontainer.json
{
  "name": "POP Generator",
  "image": "mcr.microsoft.com/devcontainers/python:3.12",
  "features": {
    "ghcr.io/devcontainers/features/node:1": {"version": "20"}
  },
  "forwardPorts": [3000, 8000],
  "postCreateCommand": "cd backend && pip install -r requirements.txt && cd ../frontend && npm install",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "dbaeumer.vscode-eslint"
      ]
    }
  }
}
```
### 8.2 環境変数
```
ANTHROPIC_API_KEY=sk-...     # Claude Vision API用
```
---
## 9. 開発ロードマップ
### Phase 3: バックエンドAPI開発
- [ ] FastAPIプロジェクト初期化
- [ ] PDF解析エンドポイント（Claude Vision API連携）
- [ ] Excel差し替えエンジン（文字列操作方式）
- [ ] POP生成エンドポイント
- [ ] テンプレート管理API
### Phase 4: フロントエンドUI開発
- [ ] React/Viteプロジェクト初期化
- [ ] PDFアップロードコンポーネント
- [ ] 商品一覧・編集コンポーネント
- [ ] テンプレート選択コンポーネント
- [ ] POP生成・ダウンロード機能
### Phase 5: テンプレート拡張・税率管理
- [ ] 複数テンプレート対応
- [ ] テンプレートメタデータ管理UI
- [ ] 税率設定の永続化
### Phase 6: テスト・改善
- [ ] 複数PDFでの抽出精度テスト
- [ ] 複数テンプレートでの差し替えテスト
- [ ] エラーハンドリング強化
- [ ] パフォーマンス最適化
---
## 10. 既知の課題と対策
| # | 課題 | 対策 | 優先度 |
|---|------|------|--------|
| 1 | PDF解析にAPI費用がかかる | バッチ処理で最小限のAPI呼び出しに最適化 | 中 |
| 2 | 商品写真のアスペクト比崩れ | テンプレート枠サイズに合わせてリサイズ・フィット | 高 |
| 3 | 差し替え画像のZ-order問題 | 差し替え要素を常に前面配置するロジック実装 | 高 |
| 4 | テンプレート追加に構造解析が必要 | テンプレート登録用の解析ツールを用意 | 中 |
| 5 | PDFレイアウトの多様性 | Claude Vision APIの柔軟性で対応 | 低（API対応済み）|
