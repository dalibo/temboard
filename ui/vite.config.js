import vue from "@vitejs/plugin-vue2";
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
      input: {
        "alerting.checks": "/alerting.checks.js",
        "alerting.check": "/alerting.check.js",
        "instance.about": "/instance.about.js",
        "settings.about": "/settings.about.js",
        "settings.group": "/settings.group.js",
        "settings.instance": "/settings.instance.js",
        "settings.users": "/settings.users.js",
        maintenance: "/maintenance.js",
        "maintenance.database": "/maintenance.database.js",
        "maintenance.schema": "/maintenance.schema.js",
        "maintenance.table": "/maintenance.table.js",
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
      moment: "moment/moment.js",
    },
  },
});
