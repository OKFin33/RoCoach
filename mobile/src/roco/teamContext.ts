import * as FileSystem from "expo-file-system/legacy";

import type { TeamContextAttachment } from "../api/types";

export type TeamContextStore = {
  schema_version: "team_context_store.v1";
  active_team_id: string | null;
  teams: TeamContextAttachment[];
};

const STORE_FILE = "roco-team-context-store.json";

export const EMPTY_TEAM_CONTEXT_STORE: TeamContextStore = {
  schema_version: "team_context_store.v1",
  active_team_id: null,
  teams: [],
};

export function createTeamId(): string {
  return `team-${Date.now()}-${Math.round(Math.random() * 10000)}`;
}

export function getActiveTeamContext(store: TeamContextStore): TeamContextAttachment | null {
  if (!store.active_team_id) {
    return null;
  }
  return store.teams.find((team) => team.team_id === store.active_team_id) ?? null;
}

export function activeChatContextAttachments(store: TeamContextStore): TeamContextAttachment[] {
  const active = getActiveTeamContext(store);
  if (!active || active.slots.length === 0) {
    return [];
  }
  return [active];
}

export function upsertActiveTeamContext(
  store: TeamContextStore,
  team: TeamContextAttachment,
): TeamContextStore {
  const teams = store.teams.filter((candidate) => candidate.team_id !== team.team_id);
  return {
    schema_version: "team_context_store.v1",
    active_team_id: team.team_id,
    teams: [...teams, team],
  };
}

export async function loadTeamContextStore(): Promise<TeamContextStore> {
  try {
    const path = await storePath();
    const info = await FileSystem.getInfoAsync(path);
    if (!info.exists) {
      return EMPTY_TEAM_CONTEXT_STORE;
    }
    return normalizeStore(JSON.parse(await FileSystem.readAsStringAsync(path)));
  } catch {
    return EMPTY_TEAM_CONTEXT_STORE;
  }
}

export async function saveTeamContextStore(store: TeamContextStore): Promise<void> {
  const path = await storePath();
  await FileSystem.writeAsStringAsync(path, JSON.stringify(normalizeStore(store)));
}

async function storePath(): Promise<string> {
  const directory = `${FileSystem.documentDirectory ?? ""}roco/`;
  if (!directory.trim()) {
    throw new Error("Local document storage is unavailable.");
  }
  await FileSystem.makeDirectoryAsync(directory, { intermediates: true });
  return `${directory}${STORE_FILE}`;
}

function normalizeStore(value: unknown): TeamContextStore {
  if (!isRecord(value)) {
    return EMPTY_TEAM_CONTEXT_STORE;
  }
  const teams = Array.isArray(value.teams)
    ? value.teams.filter(isTeamContextAttachment)
    : [];
  const activeTeamId = typeof value.active_team_id === "string" ? value.active_team_id : null;
  return {
    schema_version: "team_context_store.v1",
    active_team_id: teams.some((team) => team.team_id === activeTeamId) ? activeTeamId : null,
    teams,
  };
}

function isTeamContextAttachment(value: unknown): value is TeamContextAttachment {
  return (
    isRecord(value) &&
    value.kind === "team_context" &&
    value.schema_version === "team_context.v1" &&
    value.source === "team_builder" &&
    typeof value.team_id === "string" &&
    value.active === true &&
    Array.isArray(value.slots)
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
