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
    outDir: "../dist",
    emptyOutDir: true,
    assetsDir: ".",
    rollupOptions: {
      output: {
        manualChunks: {
          "highlight.js": ["highlight.js"],
          "bootstrap-vue-next": ["bootstrap-vue-next"],
          vue: ["vue"],
        },
      },
      input: {
        "alerting.check": "/alerting.check.js",
        "alerting.checks": "/alerting.checks.js",
        "instance.about": "/instance.about.js",
        "maintenance.database": "/maintenance.database.js",
        "maintenance.schema": "/maintenance.schema.js",
        "maintenance.table": "/maintenance.table.js",
        "settings.about": "/settings.about.js",
        "settings.group": "/settings.group.js",
        "settings.instance": "/settings.instance.js",
        "settings.notifications": "/settings.notifications.js",
        "settings.user": "/settings.users.js",
        activity: "/activity.js",
        dashboard: "/dashboard.js",
        home: "/home.js",
        login: "/login.js",
        maintenance: "/maintenance.js",
        monitoring: "/monitoring.js",
        notifications: "/notifications.js",
        statements: "/statements.js",
        configuration: "/pgconf.js",
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
