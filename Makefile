.PHONY: dev backend frontend install build test lint clean ollama-setup

# Run backend + frontend together (Vite proxies /api to the backend).
dev:
	@trap 'kill 0' EXIT; \
	(cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

# Install all dependencies (base, API-free).
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# Optional local-AI extras (better embeddings, local STT/TTS) — still API-free.
install-extras:
	cd backend && pip install -r requirements-extras.txt

# Build the frontend; the backend then serves it as a single app on :8000.
build:
	cd frontend && npm run build

# Run the whole thing as one production process (after `make build`).
serve: build
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	cd backend && python -m pytest tests/ -q

test-ci:
	pip install pytest
	cd backend && python -m pytest tests/ -q

lint:
	cd frontend && npm run lint

# Convenience: pull recommended local models for full-quality, API-free AI.
ollama-setup:
	ollama pull llama3.1:8b
	ollama pull nomic-embed-text

clean:
	rm -rf backend/data frontend/dist backend/.pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
