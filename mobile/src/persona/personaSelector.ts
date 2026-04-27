import type { PersonaSelector } from "../api/types";

export type PersonaSelectionMode = "default" | "built_in" | "managed";

export type PersonaSelectorDraft = {
  mode: PersonaSelectionMode;
  personaId: string;
  version: string;
  revision: string;
};

export type PersonaSelectorPayload = {
  persona_selector?: PersonaSelector;
};

export function createDefaultPersonaSelectorDraft(): PersonaSelectorDraft {
  return {
    mode: "default",
    personaId: "",
    version: "",
    revision: "",
  };
}

export function createBuiltInPersonaSelectorDraft(personaId: string): PersonaSelectorDraft {
  return {
    mode: "built_in",
    personaId,
    version: "",
    revision: "",
  };
}

export function personaSelectorDraftError(draft: PersonaSelectorDraft): string | null {
  if (draft.mode === "default") {
    return null;
  }

  if (!draft.personaId.trim()) {
    return "Persona ID is required for explicit persona selection.";
  }

  if (draft.mode === "built_in") {
    return null;
  }

  if (!draft.version.trim()) {
    return "Managed persona version is required.";
  }

  const revision = parseRevision(draft.revision);
  if (revision === null) {
    return "Managed persona revision must be a positive integer.";
  }

  return null;
}

export function buildPersonaSelectorPayload(draft: PersonaSelectorDraft): PersonaSelectorPayload {
  const selector = buildPersonaSelector(draft);
  return selector ? { persona_selector: selector } : {};
}

function buildPersonaSelector(draft: PersonaSelectorDraft): PersonaSelector | null {
  if (draft.mode === "default" || personaSelectorDraftError(draft) !== null) {
    return null;
  }

  const personaId = draft.personaId.trim();
  if (draft.mode === "built_in") {
    return {
      kind: "built_in",
      persona_id: personaId,
    };
  }

  const revision = parseRevision(draft.revision);
  if (revision === null) {
    return null;
  }

  return {
    kind: "managed",
    persona_id: personaId,
    version: draft.version.trim(),
    revision,
  };
}

function parseRevision(value: string): number | null {
  const revision = Number(value.trim());
  return Number.isInteger(revision) && revision > 0 ? revision : null;
}
