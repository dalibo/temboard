import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
  root: 'temboardui/static/src',
  base: '/static/',
  build: {
    manifest: true,
    outDir: '..',
    emptyOutDir: false,
    assetsDir: '.',
    // Increase warning limit until highlighjs is extracted from base module.
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      input: {
        'temboard': '/temboard.js'
      }
    }
  }
})
