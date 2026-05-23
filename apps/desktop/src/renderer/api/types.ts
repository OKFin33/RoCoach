export type AgentResponseStatus = "ok" | "degraded" | "refused" | "failed";
export type AgentRuntimePath =
  | "native_llm_terminal"
  | "deterministic_degraded_fallback"
  | "static_control_response";
export type AnalysisType =
  | "chat_response"
  | "team_analysis"
  | "species_analysis"
  | "session_command"
  | "unsupported"
  | "runtime_failure"
  | "unknown";

export type PersonaSelector =
  | {
      kind: "built_in";
      persona_id: "lattice_support_coach";
    }
  | {
      kind: "managed";
      persona_id: string;
      version: string;
      revision: number;
    };

export type PersonaEnvelope = {
  persona_id?: string | null;
  display_name?: string | null;
  display_style?: string | null;
  rendered_answer?: string | null;
  facts_locked: boolean;
  fact_policy: string;
  public_safe: boolean;
  sanitized: boolean;
  render_contract?: string | null;
};

export type PresentationResult = {
  reply: string;
};

export type AgentResponse = {
  schema_version: "agent_response.v1";
  status: AgentResponseStatus;
  backend: string;
  runtime_path: AgentRuntimePath;
  continuity_persisted: boolean;
  analysis_type: AnalysisType;
  answer: string;
  presentation?: PresentationResult | null;
  persona?: PersonaEnvelope | null;
};

export type ChatRequest = {
  message: string;
  session_id?: string | null;
  persona_selector?: PersonaSelector | null;
  context_attachments?: TeamContextAttachment[];
};

export type ChatResponse = {
  session_id: string;
  response: AgentResponse;
  session_event?: SessionEvent | null;
};

export type SessionClearResponse = {
  session_id: string;
  session_event: SessionEvent;
};

export type SessionEvent = {
  type: "started" | "continued" | "reconciled" | "cleared" | "rolled_over";
  reason: string;
  message: string;
  user_action?: string | null;
  diagnostic: {
    agent_context?: string;
    visible_messages?: "unchanged" | "mark_stale" | "clear" | string;
    archive?: string;
    support_code?: string;
    [key: string]: unknown;
  };
};

export type HealthResponse = {
  status: string;
  service_name: string;
  release_stage: string;
  api_version: string;
  response_schema_version: string;
};

export type MetadataResponse = {
  service_name: string;
  release_stage: string;
  default_backend: string;
  battle_dex_available: boolean;
};

export type ModelDiagnosticResponse = {
  status: "ok" | "failed";
  diagnostic_code: string;
  message: string;
  provider_family_hint: string;
};

export type TeamStatKey = "hp" | "atk" | "defense" | "spa" | "spd" | "spe";

export type TeamMoveSelection = {
  move_id: string;
  move_name: string;
  access_channel?: string | null;
  move_type?: string | null;
  category_raw?: string | null;
};

export type TeamContextSlot = {
  slot_index: number;
  species_id: string;
  display_name: string;
  primary_type: string;
  secondary_type?: string | null;
  fixed_ability?: {
    ability_name: string;
    effect_text?: string | null;
  } | null;
  selected_moves: TeamMoveSelection[];
  nature: {
    label?: string | null;
    plus_stat?: TeamStatKey | null;
    minus_stat?: TeamStatKey | null;
  };
  individual_value_bonuses: {
    stat: TeamStatKey;
    value: number;
  }[];
  notes?: string | null;
};

export type TeamContextAttachment = {
  kind: "team_context";
  schema_version: "team_context.v1";
  source: "team_builder";
  team_id: string;
  active: true;
  slots: TeamContextSlot[];
};

export type SpeciesSearchItem = {
  species_id: string;
  display_name: string;
  initial_species_name?: string | null;
  form_name?: string | null;
  regional_form_name?: string | null;
  primary_type: string;
  secondary_type?: string | null;
};

export type SpeciesSearchResponse = {
  query: string;
  results: SpeciesSearchItem[];
};

export type SpeciesProfileResponse = {
  profile: Record<string, unknown>;
};

export type SpeciesMoveRecord = {
  species_id: string;
  move_id?: string | null;
  move_name: string;
  move_type?: string | null;
  category_raw?: string | null;
  access_channel: string;
  unlock_level?: number | null;
  power?: number | null;
  effect_text?: string | null;
};

export type SpeciesMovesResponse = {
  species_id: string;
  moves: SpeciesMoveRecord[];
};
