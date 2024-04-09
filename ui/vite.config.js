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
        "alerting.check": "/alerting.check.js",
        "alerting.checks": "/alerting.checks.js",
        "maintenance.database": "/maintenance.database.js",
        "maintenance.schema": "/maintenance.schema.js",
        "maintenance.table": "/maintenance.table.js",
        "settings.about": "/settings.about.js",
        "settings.group": "/settings.group.js",
        "settings.instance": "/settings.instance.js",
        activity: "/activity.js",
        dashboard: "/dashboard.js",
        home: "/home.js",
        maintenance: "/maintenance.js",
        monitoring: "/monitoring.js",
        statements: "/statements.js",
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
