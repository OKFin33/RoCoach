export type AgentResponseStatus = "ok" | "degraded" | "refused" | "failed";

export type AnalysisType =
  | "chat_response"
  | "team_analysis"
  | "species_analysis"
  | "session_command"
  | "unsupported"
  | "runtime_failure"
  | "unknown";

export type ConfidenceTier =
  | "confirmed"
  | "provisional"
  | "low_confidence"
  | "insufficient_evidence";

export type EvidenceItem = {
  id: string;
  source_type: string;
  source_label: string;
  confidence: ConfidenceTier;
  content: string;
  retrieval_reason: string;
};

export type AgentToolResult = {
  tool_name: string;
  status: AgentResponseStatus;
  summary: string;
  evidence_refs: string[];
  payload?: Record<string, unknown> | null;
};

export type ConfidenceNote = {
  claim_scope: string;
  confidence: ConfidenceTier;
  note: string;
};

export type FollowupOption = {
  id: string;
  label: string;
  action?: string | null;
};

export type SynthesisWarningSeverity = "high" | "medium" | "low";

export type SynthesisWarning = {
  code: string;
  severity: SynthesisWarningSeverity;
  message: string;
};

export type SynthesisResult = {
  synthesis_version: string;
  synthesized_judgement: string;
  why_summary: string;
  surfaced_warnings: SynthesisWarning[];
  followup_directions: string[];
  grounding_refs: string[];
  doctrine_refs: string[];
};

export type DetailSectionVisibility = "collapsed" | "expanded";
export type DetailSectionContentKind =
  | "evidence"
  | "confidence"
  | "tool_trace"
  | "analytical_base"
  | "followup"
  | "raw";

export type VisibleWarning = {
  code: string;
  severity: SynthesisWarningSeverity;
  message: string;
};

export type DetailSection = {
  section_id: string;
  label: string;
  default_visibility: DetailSectionVisibility;
  content_kind: DetailSectionContentKind;
  content: string;
};

export type PresentationMetadata = {
  persona_id?: string | null;
  facts_locked: boolean;
  fact_policy: string;
  source_contract: string;
};

export type PresentationResult = {
  presentation_version: string;
  reply: string;
  why: string;
  visible_warnings: VisibleWarning[];
  detail_sections: DetailSection[];
  followup_prompts: string[];
  presentation_metadata: PresentationMetadata;
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

export type PersonaSelectorKind = "built_in" | "managed";

export type BuiltInPersonaSelector = {
  kind: "built_in";
  persona_id: string;
};

export type ManagedPersonaSelector = {
  kind: "managed";
  persona_id: string;
  version: string;
  revision: number;
};

export type PersonaSelector = BuiltInPersonaSelector | ManagedPersonaSelector;

export type AgentResponse = {
  schema_version: "agent_response.v1";
  status: AgentResponseStatus;
  backend: string;
  analysis_type: AnalysisType;
  answer: string;
  tool_results: AgentToolResult[];
  evidence: EvidenceItem[];
  confidence_notes: ConfidenceNote[];
  followup_options: FollowupOption[];
  synthesis?: SynthesisResult | null;
  presentation?: PresentationResult | null;
  persona?: PersonaEnvelope | null;
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
  api_version: string;
  response_schema_version: string;
  default_backend: string;
  battle_dex_available: boolean;
  session_continuity: string;
  provider_key_mode: string;
  rate_limit_mode: string;
  unofficial_notice: string;
  features: string[];
};

export type ModelDiagnosticRequest = {
  prompt?: string;
};

export type ModelDiagnosticResponse = {
  status: "ok" | "failed";
  diagnostic_code: string;
  message: string;
  provider_family_hint: string;
};

export type ChatRequest = {
  message: string;
  session_id?: string | null;
  persona_selector?: PersonaSelector | null;
  persona_id?: string | null;
  context_attachments?: TeamContextAttachment[];
};

export type ChatResponse = {
  session_id: string;
  response: AgentResponse;
  session_event?: SessionEvent | null;
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

export type TeamSlotInput = {
  primary_type: string;
  secondary_type?: string | null;
};

export type TeamAnalyzeRequest = {
  team: TeamSlotInput[];
  persona_selector?: PersonaSelector | null;
  persona_id?: string | null;
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

export type TeamStatKey = "hp" | "atk" | "defense" | "spa" | "spd" | "spe";

export type TeamAbilitySnapshot = {
  ability_name: string;
  effect_text?: string | null;
};

export type TeamMoveSelection = {
  move_id: string;
  move_name: string;
  access_channel?: string | null;
  move_type?: string | null;
  category_raw?: string | null;
};

export type TeamNature = {
  label?: string | null;
  plus_stat?: TeamStatKey | null;
  minus_stat?: TeamStatKey | null;
};

export type TeamIndividualValueBonus = {
  stat: TeamStatKey;
  value: number;
};

export type TeamContextSlot = {
  slot_index: number;
  species_id: string;
  display_name: string;
  primary_type: string;
  secondary_type?: string | null;
  fixed_ability?: TeamAbilitySnapshot | null;
  selected_moves: TeamMoveSelection[];
  nature: TeamNature;
  individual_value_bonuses: TeamIndividualValueBonus[];
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
