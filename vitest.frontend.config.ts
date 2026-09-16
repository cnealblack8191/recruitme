import { defineConfig } from "vitest/config";
import path from "node:path";

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve("client/src"),
      "@shared": path.resolve("shared"),
    },
  },
  esbuild: { jsx: "automatic" },
  test: {
    environment: "node",
    include: ["client/src/**/*.test.ts", "client/src/**/*.test.tsx"],
  },
});
