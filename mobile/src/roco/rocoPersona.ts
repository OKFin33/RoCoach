import type { PersonaSelector, RocoPersonaUiId } from "./rocoTheme";

export type PersonaWheelOption =
  | {
      ui_id: "you_know_who";
      label: "You know who";
      selector: {
        kind: "managed";
        persona_id: "you_know_who";
        version: "draft.v1";
        revision: 1;
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
    kind: "managed",
    persona_id: "you_know_who",
    version: "draft.v1",
    revision: 1,
  },
  ai_assistant: {
    kind: "built_in",
    persona_id: "lattice_support_coach",
  },
};

export const DEFAULT_PERSONA_UI_ID: RocoPersonaUiId = "you_know_who";
export const DEFAULT_PERSONA_SELECTOR: PersonaSelector =
  PERSONA_UI_TO_BACKEND[DEFAULT_PERSONA_UI_ID];

export const PERSONA_WHEEL_OPTIONS: PersonaWheelOption[] = [
  {
    ui_id: "you_know_who",
    label: "You know who",
    selector: {
      kind: "managed",
      persona_id: "you_know_who",
      version: "draft.v1",
      revision: 1,
    },
    avatar: "agent_you_know_who",
    enabled: true,
  },
  {
    ui_id: "ai_assistant",
    label: "默认AI助手",
    selector: {
      kind: "built_in",
      persona_id: "lattice_support_coach",
    },
    avatar: "agent_ai_assistant",
    enabled: true,
  },
  {
    ui_id: "add_persona",
    label: "添加人格",
    selector: null,
    avatar: "persona_add",
    enabled: true,
    reserved_seam: true,
  },
];

export function selectorForPersonaUiId(uiId: RocoPersonaUiId): PersonaSelector | null {
  if (uiId === "add_persona") {
    return null;
  }
  return PERSONA_UI_TO_BACKEND[uiId];
}
