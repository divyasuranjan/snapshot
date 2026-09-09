import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

const root = process.cwd();

export default defineConfig({
  plugins: [react()],
  test: {
    root,
    environment: "jsdom",
    setupFiles: [path.join(root, "vitest.setup.ts")],
    exclude: ["node_modules", ".next"],
  },
  resolve: {
    alias: {
      "@": root,
    },
  },
});
