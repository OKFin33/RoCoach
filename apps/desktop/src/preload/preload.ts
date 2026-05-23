import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("rocoDesktop", {
  ensureBackendStarted: () => ipcRenderer.invoke("backend:ensureStarted"),
  backendStatus: () => ipcRenderer.invoke("backend:status"),
  request: (request: {
    path: string;
    method?: string;
    headers?: Record<string, string>;
    body?: unknown;
  }) => ipcRenderer.invoke("api:request", request),
  encryptSecret: (plainText: string) => ipcRenderer.invoke("secret:encrypt", plainText),
  decryptSecret: (encryptedBase64: string) => ipcRenderer.invoke("secret:decrypt", encryptedBase64),
});
