import type {
  ChatRequest,
  ChatResponse,
  HealthResponse,
  MetadataResponse,
  ModelDiagnosticResponse,
  SessionClearResponse,
  SpeciesMovesResponse,
  SpeciesProfileResponse,
  SpeciesSearchResponse,
} from "./types";

export class ProductApiClient {
  health(): Promise<HealthResponse> {
    return window.rocoDesktop.request<HealthResponse>({ path: "/health" });
  }

  metadata(): Promise<MetadataResponse> {
    return window.rocoDesktop.request<MetadataResponse>({ path: "/metadata" });
  }

  chat(request: ChatRequest, headers: Record<string, string>): Promise<ChatResponse> {
    return window.rocoDesktop.request<ChatResponse>({
      path: "/chat",
      method: "POST",
      headers,
      body: request,
    });
  }

  clearSession(reason = "desktop_clear_current_chat"): Promise<SessionClearResponse> {
    return window.rocoDesktop.request<SessionClearResponse>({
      path: "/session/clear",
      method: "POST",
      body: { reason },
    });
  }

  modelDiagnostic(headers: Record<string, string>): Promise<ModelDiagnosticResponse> {
    return window.rocoDesktop.request<ModelDiagnosticResponse>({
      path: "/runtime/model-diagnostic",
      method: "POST",
      headers,
      body: { prompt: "用一句中文回答：RoCoach 模型服务连接是否成功？" },
    });
  }

  searchSpecies(
    query: string,
    limit = 8,
    usage: "default" | "team_builder" = "default",
  ): Promise<SpeciesSearchResponse> {
    const params = new URLSearchParams({ q: query, limit: String(limit), usage });
    return window.rocoDesktop.request<SpeciesSearchResponse>({
      path: `/species/search?${params.toString()}`,
    });
  }

  speciesProfile(speciesId: string): Promise<SpeciesProfileResponse> {
    return window.rocoDesktop.request<SpeciesProfileResponse>({
      path: `/species/${encodeURIComponent(speciesId)}`,
    });
  }

  speciesMoves(speciesId: string, limit = 200): Promise<SpeciesMovesResponse> {
    const params = new URLSearchParams({ limit: String(limit) });
    return window.rocoDesktop.request<SpeciesMovesResponse>({
      path: `/species/${encodeURIComponent(speciesId)}/moves?${params.toString()}`,
    });
  }
}
