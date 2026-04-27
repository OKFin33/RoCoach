import * as SecureStore from "expo-secure-store";

export const ROCO_RUNTIME_HEADERS = {
  providerKey: "X-Roco-Provider-Key",
  providerBaseUrl: "X-Roco-Provider-Base-Url",
  model: "X-Roco-Model",
  runtimeMode: "X-Roco-Runtime-Mode",
} as const;

const NON_SECRET_SETTINGS_KEY = "roco.runtime.non_secret.v1";
const PROVIDER_KEY_SECRET_KEY = "roco.runtime.provider_key.v1";

export type RuntimeExecutionMode = "deterministic" | "native";
export type RuntimeTransportMode = "local" | "cloud";

export type RuntimeSettings = {
  apiBaseUrl: string;
  providerBaseUrl: string;
  model: string;
  runtimeMode: RuntimeExecutionMode;
  transportMode: RuntimeTransportMode;
  allowUnsafeLanHttp: boolean;
  providerKey: string;
};

export type RuntimeSettingsLoadResult = {
  settings: RuntimeSettings;
  secureStoreAvailable: boolean;
  warning: string | null;
};

export type NativeHeaderBuildResult =
  | { ok: true; headers: Record<string, string> }
  | { ok: false; error: string };

export type NativeHeaderBuildOptions = {
  secureStoreAvailable?: boolean;
};

type NonSecretRuntimeSettings = Omit<RuntimeSettings, "providerKey">;

export const DEFAULT_RUNTIME_SETTINGS: RuntimeSettings = {
  apiBaseUrl: "http://127.0.0.1:8000",
  providerBaseUrl: "",
  model: "",
  runtimeMode: "deterministic",
  transportMode: "local",
  allowUnsafeLanHttp: false,
  providerKey: "",
};

export async function loadRuntimeSettings(): Promise<RuntimeSettingsLoadResult> {
  const secureStoreAvailable = await SecureStore.isAvailableAsync();
  if (!secureStoreAvailable) {
    return {
      settings: { ...DEFAULT_RUNTIME_SETTINGS },
      secureStoreAvailable,
      warning: "Secure storage is unavailable. Native runtime keys are treated as not configured.",
    };
  }

  const nonSecretJson = await SecureStore.getItemAsync(NON_SECRET_SETTINGS_KEY);
  const providerKey = (await SecureStore.getItemAsync(PROVIDER_KEY_SECRET_KEY)) ?? "";
  return {
    settings: {
      ...DEFAULT_RUNTIME_SETTINGS,
      ...parseNonSecretSettings(nonSecretJson),
      providerKey,
    },
    secureStoreAvailable,
    warning: null,
  };
}

export async function saveRuntimeSettings(settings: RuntimeSettings): Promise<void> {
  const secureStoreAvailable = await SecureStore.isAvailableAsync();
  if (!secureStoreAvailable) {
    throw new Error("Secure storage is unavailable; provider key was not saved.");
  }

  const { providerKey, ...nonSecretSettings } = normalizeRuntimeSettings(settings);
  await SecureStore.setItemAsync(NON_SECRET_SETTINGS_KEY, JSON.stringify(nonSecretSettings));
  if (providerKey) {
    await SecureStore.setItemAsync(PROVIDER_KEY_SECRET_KEY, providerKey);
  } else {
    await SecureStore.deleteItemAsync(PROVIDER_KEY_SECRET_KEY);
  }
}

export async function clearProviderKey(): Promise<void> {
  if (await SecureStore.isAvailableAsync()) {
    await SecureStore.deleteItemAsync(PROVIDER_KEY_SECRET_KEY);
  }
}

export function buildNativeRuntimeHeaders(
  settings: RuntimeSettings,
  options: NativeHeaderBuildOptions = {},
): NativeHeaderBuildResult {
  if (settings.runtimeMode !== "native") {
    return { ok: true, headers: {} };
  }

  if (options.secureStoreAvailable === false) {
    return {
      ok: false,
      error: "Secure storage is unavailable. Native runtime key is treated as not configured.",
    };
  }

  const providerKey = settings.providerKey.trim();
  const providerBaseUrl = settings.providerBaseUrl.trim();
  const model = settings.model.trim();
  if (!providerKey || !providerBaseUrl || !model) {
    return {
      ok: false,
      error: "Native runtime needs provider key, provider base URL, and model before sending.",
    };
  }

  const providerBaseUrlError = validateProviderBaseUrl(providerBaseUrl);
  if (providerBaseUrlError) {
    return { ok: false, error: providerBaseUrlError };
  }

  const transportError = validateProductApiTransport(settings);
  if (transportError) {
    return { ok: false, error: transportError };
  }

  return {
    ok: true,
    headers: {
      [ROCO_RUNTIME_HEADERS.providerKey]: providerKey,
      [ROCO_RUNTIME_HEADERS.providerBaseUrl]: providerBaseUrl,
      [ROCO_RUNTIME_HEADERS.model]: model,
      [ROCO_RUNTIME_HEADERS.runtimeMode]: "native",
    },
  };
}

export function validateProductApiTransport(settings: RuntimeSettings): string | null {
  let parsed: URL;
  try {
    parsed = new URL(settings.apiBaseUrl);
  } catch {
    return "Product API base URL is invalid.";
  }

  if (parsed.protocol === "https:") {
    return null;
  }
  if (parsed.protocol !== "http:") {
    return "Provider keys can only be sent to HTTPS or loopback HTTP Product API endpoints.";
  }
  if (isLoopbackHostname(parsed.hostname)) {
    return null;
  }
  if (settings.allowUnsafeLanHttp) {
    return null;
  }
  return "Blocked provider key over non-HTTPS LAN HTTP. Enable unsafe dev override only for local testing.";
}

export function validateProviderBaseUrl(providerBaseUrl: string): string | null {
  try {
    const parsed = new URL(providerBaseUrl);
    if (parsed.protocol === "https:") {
      return null;
    }
    if (parsed.protocol === "http:" && isLoopbackHostname(parsed.hostname)) {
      return null;
    }
    if (parsed.protocol === "http:") {
      return "Provider base URL must use HTTPS unless it targets loopback HTTP for local development.";
    }
  } catch {
    return "Provider base URL is invalid.";
  }
  return "Provider base URL must use HTTPS or loopback HTTP.";
}

export function normalizeRuntimeSettings(settings: RuntimeSettings): RuntimeSettings {
  return {
    apiBaseUrl: settings.apiBaseUrl.trim() || DEFAULT_RUNTIME_SETTINGS.apiBaseUrl,
    providerBaseUrl: settings.providerBaseUrl.trim(),
    model: settings.model.trim(),
    runtimeMode: settings.runtimeMode,
    transportMode: settings.transportMode,
    allowUnsafeLanHttp: settings.allowUnsafeLanHttp,
    providerKey: settings.providerKey.trim(),
  };
}

function parseNonSecretSettings(value: string | null): Partial<NonSecretRuntimeSettings> {
  if (!value) {
    return {};
  }
  try {
    const parsed = JSON.parse(value) as Partial<NonSecretRuntimeSettings>;
    return {
      apiBaseUrl: typeof parsed.apiBaseUrl === "string" ? parsed.apiBaseUrl : undefined,
      providerBaseUrl: typeof parsed.providerBaseUrl === "string" ? parsed.providerBaseUrl : undefined,
      model: typeof parsed.model === "string" ? parsed.model : undefined,
      runtimeMode: parsed.runtimeMode === "native" ? "native" : "deterministic",
      transportMode: parsed.transportMode === "cloud" ? "cloud" : "local",
      allowUnsafeLanHttp: parsed.allowUnsafeLanHttp === true,
    };
  } catch {
    return {};
  }
}

function isLoopbackHostname(hostname: string): boolean {
  const normalized = hostname.toLowerCase();
  return normalized === "localhost" || normalized === "127.0.0.1" || normalized === "::1" || normalized === "[::1]";
}
