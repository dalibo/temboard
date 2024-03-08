import vue from "@vitejs/plugin-vue2";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
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
      input: {
        "alerting.checks": "/alerting.checks.js",
        "alerting.check": "/alerting.check.js",
        "settings.group": "/settings.group.js",
        "settings.instance": "/settings.instance.js",
        maintenance: "/maintenance.js",
        "maintenance.database": "/maintenance.database.js",
        "maintenance.schema": "/maintenance.schema.js",
        activity: "/activity.js",
        dashboard: "/dashboard.js",
        home: "/home.js",
        monitoring: "/monitoring.js",
        statements: "/statements.js",
        temboard: "/temboard.js",
      },
    },
  },
  resolve: {
    alias: {
      vue: "vue/dist/vue.esm.js",
    },
  },
});
