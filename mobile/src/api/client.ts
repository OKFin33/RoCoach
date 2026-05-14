import type {
  ChatRequest,
  ChatResponse,
  HealthResponse,
  MetadataResponse,
  ModelDiagnosticRequest,
  ModelDiagnosticResponse,
  SpeciesProfileResponse,
  SpeciesMovesResponse,
  SpeciesSearchResponse,
  TeamAnalyzeRequest,
  AgentResponse,
} from "./types";

export class ProductApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, message: string, detail: unknown) {
    super(message);
    this.name = "ProductApiError";
    this.status = status;
    this.detail = detail;
  }
}

export class ProductApiClient {
  readonly baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = normalizeBaseUrl(baseUrl);
  }

  health(): Promise<HealthResponse> {
    return this.request<HealthResponse>("/health");
  }

  metadata(): Promise<MetadataResponse> {
    return this.request<MetadataResponse>("/metadata");
  }

  chat(request: ChatRequest, headers: Record<string, string> = {}): Promise<ChatResponse> {
    return this.request<ChatResponse>("/chat", {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });
  }

  modelDiagnostic(
    request: ModelDiagnosticRequest,
    headers: Record<string, string> = {},
  ): Promise<ModelDiagnosticResponse> {
    return this.request<ModelDiagnosticResponse>("/runtime/model-diagnostic", {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });
  }

  analyzeTeam(request: TeamAnalyzeRequest): Promise<AgentResponse> {
    return this.request<AgentResponse>("/team/analyze", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  searchSpecies(query: string, limit = 10): Promise<SpeciesSearchResponse> {
    const params = new URLSearchParams({ q: query, limit: String(limit) });
    return this.request<SpeciesSearchResponse>(`/species/search?${params.toString()}`);
  }

  speciesProfile(speciesId: string): Promise<SpeciesProfileResponse> {
    return this.request<SpeciesProfileResponse>(`/species/${encodeURIComponent(speciesId)}`);
  }

  speciesMoves(speciesId: string, limit = 200): Promise<SpeciesMovesResponse> {
    const params = new URLSearchParams({ limit: String(limit) });
    return this.request<SpeciesMovesResponse>(
      `/species/${encodeURIComponent(speciesId)}/moves?${params.toString()}`,
    );
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...init.headers,
      },
    });
    const text = await response.text();
    const payload = text.length > 0 ? safeJsonParse(text) : null;
    if (!response.ok) {
      throw new ProductApiError(
        response.status,
        extractErrorMessage(payload) ?? `API request failed with HTTP ${response.status}`,
        payload,
      );
    }
    return payload as T;
  }
}

function normalizeBaseUrl(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return "http://127.0.0.1:8000";
  }
  return trimmed.replace(/\/+$/, "");
}

function safeJsonParse(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function extractErrorMessage(payload: unknown): string | null {
  if (typeof payload !== "object" || payload === null || !("detail" in payload)) {
    return null;
  }
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (typeof detail === "object" && detail !== null && "message" in detail) {
    const message = (detail as { message?: unknown }).message;
    return typeof message === "string" ? message : null;
  }
  return null;
}
