import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue2'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  root: 'temboardui/static/src',
  base: '/static/',
  build: {
    manifest: true,
    outDir: '..',
    emptyOutDir: false,
    assetsDir: '.',
    rollupOptions: {
      input: {
        'temboard': '/temboard.js',
        'temboard.settings.instance': '/temboard.settings.instance.js'
      }
    }
  }
})
