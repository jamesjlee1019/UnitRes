import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The website runs at http://localhost:3000.
// Anything the website fetches from /api/... is forwarded to the FastAPI backend,
// so fetch('/api/apartments') reaches GET /apartments on the API.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: process.env.API_URL ?? 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
    // Docker doesn't always notice when you save a file, so check on a timer instead
    watch: { usePolling: process.env.WATCH_POLLING === 'true' },
  },
})
