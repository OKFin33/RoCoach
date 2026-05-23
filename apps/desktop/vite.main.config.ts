import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  publicDir: false,
  build: {
    outDir: "dist/main",
    emptyOutDir: true,
    lib: {
      entry: path.resolve(dirname, "src/main/main.ts"),
      formats: ["es"],
      fileName: () => "main.js",
    },
    rollupOptions: {
      external: ["electron", "node:path", "node:url", "node:child_process", "node:fs", "node:os", "node:net"],
    },
  },
});
