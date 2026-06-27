import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// During dev, proxy API calls to the FastAPI backend on :8000.
// In production the backend serves the built SPA, so same-origin works.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
