import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  root: "renderer",
  // Required for Electron packaged builds (file://) so assets resolve relatively.
  base: "./",
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    hmr: false
  },
  test: {
    environment: "node",
    globals: true,
    include: ["../tests/renderer/**/*.test.js"]
  }
});
