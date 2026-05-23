import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import type { InlineConfig, ViteDevServer } from "vite";

const dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ command }) => ({
  root: dirname,
  base: "./",
  plugins: [react(), electronDevPlugin(command === "serve")],
  build: {
    outDir: "dist/renderer",
    emptyOutDir: true,
  },
  server: {
    host: "127.0.0.1",
    port: 5179,
    strictPort: true,
  },
}));

function electronDevPlugin(enabled: boolean) {
  return {
    name: "roco-electron-dev",
    async configureServer(server: ViteDevServer) {
      if (!enabled) {
        return;
      }
      const { build } = await import("vite");
      const { spawn } = await import("node:child_process");
      const mainConfig: InlineConfig = {
        configFile: false,
        publicDir: false,
        build: {
          outDir: "dist/main",
          emptyOutDir: false,
          lib: {
            entry: path.resolve(dirname, "src/main/main.ts"),
            formats: ["es"] as const,
            fileName: () => "main.js",
          },
          rollupOptions: {
            external: ["electron", "node:path", "node:url", "node:child_process", "node:fs", "node:os", "node:net"],
          },
        },
      };
      const preloadConfig: InlineConfig = {
        configFile: false,
        publicDir: false,
        build: {
          outDir: "dist/preload",
          emptyOutDir: false,
          lib: {
            entry: path.resolve(dirname, "src/preload/preload.ts"),
            formats: ["cjs"] as const,
            fileName: () => "preload.cjs",
          },
          rollupOptions: {
            external: ["electron"],
          },
        },
      };

      await build(mainConfig);
      await build(preloadConfig);

      server.httpServer?.once("listening", () => {
        const electron = spawn(
          process.platform === "win32"
            ? path.resolve(dirname, "node_modules/electron/dist/electron.exe")
            : path.resolve(dirname, "node_modules/electron/dist/Electron.app/Contents/MacOS/Electron"),
          [path.resolve(dirname, "dist/main/main.js")],
          {
            cwd: dirname,
            env: {
              ...process.env,
              ROCO_DESKTOP_DEV_SERVER_URL: "http://127.0.0.1:5179",
            },
            stdio: "inherit",
          },
        );
        server.httpServer?.once("close", () => {
          electron.kill();
        });
      });
    },
  };
}
