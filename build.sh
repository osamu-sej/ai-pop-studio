#!/usr/bin/env bash
set -e

# フロントエンドのビルド
cd frontend
npm install
npm run build
cd ..

# バックエンドの依存関係インストール
cd backend
pip install -r requirements.txt
