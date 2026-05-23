export const ROCO_RUNTIME_HEADERS = {
  providerKey: "X-Roco-Provider-Key",
  providerBaseUrl: "X-Roco-Provider-Base-Url",
  model: "X-Roco-Model",
  runtimeMode: "X-Roco-Runtime-Mode",
  reasoningMode: "X-Roco-Reasoning-Mode",
  reasoningEffort: "X-Roco-Reasoning-Effort",
} as const;

export type RuntimeThinkingMode = "disabled" | "enabled";
export type RuntimeReasoningEffort = "none" | "high" | "max";

export type RuntimeSettings = {
  providerBaseUrl: string;
  model: string;
  thinkingMode: RuntimeThinkingMode;
  reasoningEffort: RuntimeReasoningEffort;
  providerKey: string;
};

const SETTINGS_KEY = "roco.desktop.runtime.settings.v1";
const SECRET_KEY = "roco.desktop.runtime.provider_key.encrypted.v1";

export const DEFAULT_RUNTIME_SETTINGS: RuntimeSettings = {
  providerBaseUrl: "",
  model: "",
  thinkingMode: "enabled",
  reasoningEffort: "high",
  providerKey: "",
};

export async function loadRuntimeSettings(): Promise<RuntimeSettings> {
  const stored = safeJsonParse(localStorage.getItem(SETTINGS_KEY));
  const encryptedKey = localStorage.getItem(SECRET_KEY) ?? "";
  let providerKey = "";
  if (encryptedKey) {
    try {
      providerKey = await window.rocoDesktop.decryptSecret(encryptedKey);
    } catch {
      providerKey = "";
    }
  }
  return normalizeRuntimeSettings({
    ...DEFAULT_RUNTIME_SETTINGS,
    ...stored,
    providerKey,
  });
}

export async function saveRuntimeSettings(settings: RuntimeSettings): Promise<void> {
  const normalized = normalizeRuntimeSettings(settings);
  const { providerKey, ...nonSecret } = normalized;
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(nonSecret));
  if (providerKey) {
    localStorage.setItem(SECRET_KEY, await window.rocoDesktop.encryptSecret(providerKey));
  } else {
    localStorage.removeItem(SECRET_KEY);
  }
}

export async function clearProviderKey(): Promise<void> {
  localStorage.removeItem(SECRET_KEY);
}

export function buildNativeRuntimeHeaders(settings: RuntimeSettings): Record<string, string> {
  const normalized = normalizeRuntimeSettings(settings);
  if (!hasCompleteProviderConfig(normalized)) {
    return {};
  }
  const providerBaseUrlError = validateProviderBaseUrl(normalized.providerBaseUrl);
  if (providerBaseUrlError) {
    throw new Error(providerBaseUrlError);
  }
  return {
    [ROCO_RUNTIME_HEADERS.providerKey]: normalized.providerKey,
    [ROCO_RUNTIME_HEADERS.providerBaseUrl]: normalized.providerBaseUrl,
    [ROCO_RUNTIME_HEADERS.model]: normalized.model,
    [ROCO_RUNTIME_HEADERS.runtimeMode]: "native",
    [ROCO_RUNTIME_HEADERS.reasoningMode]: normalized.thinkingMode,
    ...(normalized.thinkingMode === "enabled" && normalized.reasoningEffort !== "none"
      ? { [ROCO_RUNTIME_HEADERS.reasoningEffort]: normalized.reasoningEffort }
      : {}),
  };
}

export function hasCompleteProviderConfig(settings: RuntimeSettings): boolean {
  return Boolean(settings.providerKey.trim() && settings.providerBaseUrl.trim() && settings.model.trim());
}

export function normalizeRuntimeSettings(settings: RuntimeSettings): RuntimeSettings {
  const thinkingMode: RuntimeThinkingMode = settings.thinkingMode === "enabled" ? "enabled" : "disabled";
  return {
    providerBaseUrl: settings.providerBaseUrl.trim(),
    model: settings.model.trim(),
    thinkingMode,
    reasoningEffort: thinkingMode === "enabled" ? parseReasoningEffort(settings.reasoningEffort) : "none",
    providerKey: settings.providerKey.trim(),
  };
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
  } catch {
    return "Provider base URL is invalid.";
  }
  return "Provider base URL must use HTTPS unless it targets loopback HTTP.";
}

function parseReasoningEffort(value: unknown): RuntimeReasoningEffort {
  return value === "max" || value === "high" ? value : "none";
}

function isLoopbackHostname(hostname: string): boolean {
  const normalized = hostname.toLowerCase();
  return normalized === "localhost" || normalized === "127.0.0.1" || normalized === "::1" || normalized === "[::1]";
}

function safeJsonParse(value: string | null): Partial<RuntimeSettings> {
  if (!value) {
    return {};
  }
  try {
    const parsed = JSON.parse(value) as Partial<RuntimeSettings>;
    return typeof parsed === "object" && parsed !== null ? parsed : {};
  } catch {
    return {};
  }
}
