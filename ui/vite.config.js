import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          whitespace: "preserve",
        },
      },
    }),
  ],
  root: "temboardui/static/src",
  base: "/static/",
  server: {
    origin: "http://localhost:5173",
    port: 5173,
  },
  build: {
    manifest: true,
    outDir: "..",
    emptyOutDir: false,
    assetsDir: ".",
    rollupOptions: {
      output: {
        manualChunks: {
          "highlight.js": ["highlight.js"],
          datatables: ["datatables.net-bs4", "datatables.net-buttons-bs4"],
          "bootstrap-vue-next": ["bootstrap-vue-next"],
          vue: ["vue"],
        },
      },
      input: {
        home: "/home.js",
        temboard: "/temboard.js",
      },
    },
  },
  resolve: {
    alias: {
      vue: "vue/dist/vue.esm-bundler.js",
      moment: "moment/moment.js",
    },
  },
});
