.PHONY: dev backend frontend install test lint

# 開発サーバー起動（バックエンド + フロントエンド）
dev: backend frontend

backend:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

# 依存関係インストール
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# テスト実行
test:
	cd backend && python -m pytest tests/ -v

# テスト（pip依存含む）
test-ci:
	pip install pytest pytest-asyncio httpx
	cd backend && python -m pytest tests/ -v
