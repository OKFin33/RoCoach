/**
 * Roco V1 RN UI Contract
 *
 * Purpose:
 * - Defines the first implementation contract for the Expo React Native UI.
 * - Keeps UI-only ids, backend persona ids, message state, and presentation
 *   mapping explicit.
 *
 * Boundary:
 * - This file is a handoff contract, not production source yet.
 * - It must be copied/adapted into mobile/src only by the implementation thread.
 */

export type RocoPersonaUiId = "you_know_who" | "ai_assistant" | "add_persona";

export type BackendBuiltInPersonaId =
  | "obsidian_tactical_coach"
  | "lattice_support_coach";

export type PersonaSelector =
  | {
      kind: "built_in";
      persona_id: BackendBuiltInPersonaId;
    }
  | {
      kind: "managed";
      persona_id: string;
      version: string;
      revision: number;
    };

export type PersonaWheelOption =
  | {
      ui_id: "you_know_who";
      label: "You know who";
      selector: {
        kind: "built_in";
        persona_id: "obsidian_tactical_coach";
      };
      avatar: "agent_you_know_who";
      enabled: true;
    }
  | {
      ui_id: "ai_assistant";
      label: "默认AI助手";
      selector: {
        kind: "built_in";
        persona_id: "lattice_support_coach";
      };
      avatar: "agent_ai_assistant";
      enabled: true;
    }
  | {
      ui_id: "add_persona";
      label: "添加人格";
      selector: null;
      avatar: "persona_add";
      enabled: true;
      reserved_seam: true;
    };

export const PERSONA_UI_TO_BACKEND: Record<
  Exclude<RocoPersonaUiId, "add_persona">,
  PersonaSelector
> = {
  you_know_who: {
    kind: "built_in",
    persona_id: "obsidian_tactical_coach",
  },
  ai_assistant: {
    kind: "built_in",
    persona_id: "lattice_support_coach",
  },
};

export const DEFAULT_PERSONA_UI_ID: RocoPersonaUiId = "you_know_who";

export const DEFAULT_PERSONA_SELECTOR: PersonaSelector =
  PERSONA_UI_TO_BACKEND[DEFAULT_PERSONA_UI_ID];

export type RocoMessageRole = "user" | "agent";

export type RocoMessageStatus = "sent" | "thinking" | "failed";

export type RocoMessageKind = "text" | "analysis";

export type RocoChatMessage = {
  id: string;
  role: RocoMessageRole;
  status: RocoMessageStatus;
  kind: RocoMessageKind;
  text: string;
  created_at?: string;
  persona_ui_id?: RocoPersonaUiId | null;
  analysis_card?: RocoAnalysisCardModel | null;
  error?: RocoMessageError | null;
};

export type RocoMessageError = {
  code: "network_error" | "model_error" | "api_error" | "unknown";
  user_message: string;
  retryable: boolean;
};

export type RocoVisibleWarning = {
  code: string;
  severity: "high" | "medium" | "low";
  message: string;
};

export type RocoAnalysisSection = {
  id: string;
  label: string;
  content: string;
  default_expanded: boolean;
  content_kind:
    | "evidence"
    | "confidence"
    | "tool_trace"
    | "analytical_base"
    | "followup"
    | "raw";
};

export const PUBLIC_ANALYSIS_SECTION_KINDS: ReadonlySet<
  RocoAnalysisSection["content_kind"]
> = new Set(["evidence", "confidence", "analytical_base", "followup"]);

export type RocoAnalysisCardModel = {
  title: string;
  summary?: string;
  warnings: RocoVisibleWarning[];
  sections: RocoAnalysisSection[];
  followup_prompts: string[];
};

export type RocoMessageAction =
  | "copy"
  | "rewrite"
  | "delete"
  | "confirm_delete"
  | "cancel_delete"
  | "regenerate";

export type RocoMessageActionAvailability = {
  message_id: string;
  actions: RocoMessageAction[];
  disabled_actions?: Partial<Record<RocoMessageAction, string>>;
};

export type RocoChatUiState = {
  session_id: string | null;
  messages: RocoChatMessage[];
  active_persona_ui_id: RocoPersonaUiId | null;
  active_persona_selector: PersonaSelector | null;
  thinking: boolean;
  editing_message_id: string | null;
  settings_open: boolean;
  persona_wheel_open: boolean;
  action_menu_message_id: string | null;
};

export type RocoRuntimeSettingsUiModel = {
  api_base_url: string;
  provider_base_url: string;
  model: string;
  runtime_mode: "deterministic" | "native";
  /**
   * Internal storage field only. Do not render as a visible local/cloud product
   * setting in V1.
   */
  transport_mode_internal: "local" | "cloud";
  allow_unsafe_lan_http: boolean;
  provider_key_configured: boolean;
  secure_store_available: boolean;
};

/**
 * Existing backend response fields consumed by the first RN UI.
 * Keep this local shape aligned with mobile/src/api/types.ts.
 */
export type BackendPresentationForUi = {
  reply?: string | null;
  why?: string | null;
  visible_warnings?: RocoVisibleWarning[] | null;
  detail_sections?: Array<{
    section_id: string;
    label: string;
    default_visibility: "collapsed" | "expanded";
    content_kind: RocoAnalysisSection["content_kind"];
    content: string;
  }> | null;
  followup_prompts?: string[] | null;
};

export type BackendPersonaEnvelopeForUi = {
  persona_id?: string | null;
  display_name?: string | null;
  rendered_answer?: string | null;
  sanitized?: boolean;
};

export type BackendAgentResponseForUi = {
  status: "ok" | "degraded" | "refused" | "failed";
  analysis_type:
    | "team_analysis"
    | "species_analysis"
    | "session_command"
    | "unsupported"
    | "runtime_failure"
    | "unknown";
  answer: string;
  presentation?: BackendPresentationForUi | null;
  persona?: BackendPersonaEnvelopeForUi | null;
};

export function resolveVisibleReply(response: BackendAgentResponseForUi): string {
  return (
    response.persona?.rendered_answer ??
    response.presentation?.reply ??
    response.answer
  );
}

export function buildAnalysisCardModel(
  response: BackendAgentResponseForUi,
): RocoAnalysisCardModel | null {
  const presentation = response.presentation;
  if (!presentation) {
    return null;
  }

  const sections = (presentation.detail_sections ?? [])
    .filter((section) => PUBLIC_ANALYSIS_SECTION_KINDS.has(section.content_kind))
    .map((section) => ({
      id: section.section_id,
      label: section.label,
      content: section.content,
      default_expanded: section.default_visibility === "expanded",
      content_kind: section.content_kind,
    }));

  const hasCardContent =
    Boolean(presentation.why?.trim()) ||
    (presentation.visible_warnings?.length ?? 0) > 0 ||
    sections.length > 0 ||
    (presentation.followup_prompts?.length ?? 0) > 0;

  if (!hasCardContent) {
    return null;
  }

  return {
    title: titleForAnalysisType(response.analysis_type),
    summary: presentation.why?.trim() || undefined,
    warnings: presentation.visible_warnings ?? [],
    sections,
    followup_prompts: presentation.followup_prompts ?? [],
  };
}

export function titleForAnalysisType(
  analysisType: BackendAgentResponseForUi["analysis_type"],
): string {
  switch (analysisType) {
    case "team_analysis":
      return "分析摘要";
    case "species_analysis":
      return "精灵判断";
    default:
      return "Roco 摘要";
  }
}

export function actionsForMessage(params: {
  message: RocoChatMessage;
  latest_user_message_id: string | null;
  regenerate_available: boolean;
}): RocoMessageActionAvailability {
  const { message, latest_user_message_id, regenerate_available } = params;
  if (message.role === "user") {
    const actions: RocoMessageAction[] = ["copy"];
    if (message.id === latest_user_message_id) {
      actions.push("rewrite");
    }
    actions.push("delete");
    return { message_id: message.id, actions };
  }

  return {
    message_id: message.id,
    actions: ["copy", "regenerate", "delete"],
    disabled_actions: regenerate_available
      ? undefined
      : {
          regenerate: "后端暂未提供重新生成接口",
        },
  };
}
