import path from "node:path";
import { fileURLToPath } from "node:url";
import { app, BrowserWindow, Menu, ipcMain, safeStorage } from "electron";
import { BackendManager } from "./backendManager";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(dirname, "../../../..");
const backendManager = new BackendManager(repoRoot, app.getPath("userData"));

app.setName("RoCoach");

let mainWindow: BrowserWindow | null = null;

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 414,
    height: 860,
    minWidth: 390,
    minHeight: 720,
    backgroundColor: "#00000000",
    frame: false,
    hasShadow: true,
    roundedCorners: true,
    transparent: true,
    title: "RoCoach",
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.resolve(dirname, "../preload/preload.cjs"),
    },
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow?.show();
  });

  const devServerUrl = process.env.ROCO_DESKTOP_DEV_SERVER_URL;
  if (devServerUrl) {
    await mainWindow.loadURL(devServerUrl);
  } else {
    await mainWindow.loadFile(path.resolve(dirname, "../renderer/index.html"));
  }

  void backendManager.ensureStarted();
}

app.whenReady().then(async () => {
  Menu.setApplicationMenu(null);
  registerIpc();
  await createWindow();
});

app.on("window-all-closed", () => {
  backendManager.stop();
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  backendManager.stop();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    void createWindow();
  }
});

function registerIpc() {
  ipcMain.handle("backend:ensureStarted", async () => backendManager.ensureStarted());
  ipcMain.handle("backend:status", () => backendManager.status());
  ipcMain.handle(
    "api:request",
    async (_event, request: { path: string; method?: string; headers?: Record<string, string>; body?: unknown }) => {
      const status = await backendManager.ensureStarted();
      if (status.status !== "running") {
        throw new Error(status.message);
      }
      const response = await fetch(`${status.baseUrl}${request.path}`, {
        method: request.method ?? "GET",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          ...(request.headers ?? {}),
        },
        body: request.body === undefined ? undefined : JSON.stringify(request.body),
      });
      const text = await response.text();
      const payload = text ? safeJsonParse(text) : null;
      if (!response.ok) {
        throw new Error(extractErrorMessage(payload) ?? `Product API failed with HTTP ${response.status}`);
      }
      return payload;
    },
  );
  ipcMain.handle("secret:encrypt", (_event, plainText: string) => {
    if (!plainText) {
      return "";
    }
    if (!safeStorage.isEncryptionAvailable()) {
      throw new Error("Desktop secure storage is unavailable.");
    }
    return safeStorage.encryptString(plainText).toString("base64");
  });
  ipcMain.handle("secret:decrypt", (_event, encryptedBase64: string) => {
    if (!encryptedBase64) {
      return "";
    }
    if (!safeStorage.isEncryptionAvailable()) {
      throw new Error("Desktop secure storage is unavailable.");
    }
    return safeStorage.decryptString(Buffer.from(encryptedBase64, "base64"));
  });
}

function safeJsonParse(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function extractErrorMessage(payload: unknown): string | null {
  if (!payload || typeof payload !== "object" || !("detail" in payload)) {
    return null;
  }
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    const message = (detail as { message?: unknown }).message;
    return typeof message === "string" ? message : null;
  }
  return null;
}
