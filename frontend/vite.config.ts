import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// Local dev: frontend :5173, backend :8000 (manual 4.4)
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    // CI/sandbox safety: never let vite rmSync the outDir (the local safe-delete
    // hook blocks recycle-bin operations). Clean `dist` before building instead.
    emptyOutDir: false,
  },
})
