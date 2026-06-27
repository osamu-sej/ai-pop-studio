# ── Stage 1: build the React frontend ──────────────────────────────────────
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python backend that also serves the built SPA ──────────────────
FROM python:3.12-slim
WORKDIR /app

# Backend deps first for better layer caching.
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY --from=frontend /app/frontend/dist /app/frontend/dist

ENV AURORA_DATA_DIR=/app/data \
    PYTHONUNBUFFERED=1
EXPOSE 8000
WORKDIR /app/backend

# One process serves both the API and the SPA on :8000.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
