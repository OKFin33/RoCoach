/// <reference types="vite/client" />

type RocoBackendStatus =
  | {
      status: "running";
      baseUrl: string;
      managedByDesktop: boolean;
      message: string;
    }
  | {
      status: "starting";
      baseUrl: string;
      managedByDesktop: boolean;
      message: string;
    }
  | {
      status: "failed";
      baseUrl: string;
      managedByDesktop: boolean;
      message: string;
    };

interface Window {
  rocoDesktop: {
    ensureBackendStarted(): Promise<RocoBackendStatus>;
    backendStatus(): Promise<RocoBackendStatus>;
    request<T = unknown>(request: {
      path: string;
      method?: string;
      headers?: Record<string, string>;
      body?: unknown;
    }): Promise<T>;
    encryptSecret(plainText: string): Promise<string>;
    decryptSecret(encryptedBase64: string): Promise<string>;
  };
}
