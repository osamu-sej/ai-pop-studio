# Aurora Notebook — Frontend

React 19 + Vite + TypeScript. A 3-pane (Sources · Chat · Studio) SPA for
[Aurora Notebook](../README.md).

```bash
npm install
npm run dev      # http://localhost:5173 (proxies /api → backend :8000)
npm run build    # outputs to dist/ (served by the FastAPI backend in production)
npm run lint
```

Structure:

- `src/App.tsx` — top-level view switch (home ↔ notebook)
- `src/components/` — `Home`, `NotebookView`, `SourcesPanel`, `ChatPanel`, `StudioPanel`, …
- `src/lib/markdown.tsx` — dependency-free markdown renderer
- `src/api.ts` / `src/types.ts` — typed API client and shared types

No backend URL is hard-coded: calls are same-origin and proxied to FastAPI in dev.
