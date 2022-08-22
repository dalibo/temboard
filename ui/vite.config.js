import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
  root: 'temboardui/static/src',
  build: {
    manifest: true,
    outDir: '..',
    emptyOutDir: false,
    assetsDir: '.',
    rollupOptions: {
      input: {
        'temboard': '/temboard.js'
      }
    }
  }
})
