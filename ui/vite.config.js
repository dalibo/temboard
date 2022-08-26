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
    rollupOptions: {
      input: {
        'temboard': '/temboard.js'
      }
    }
  }
})
