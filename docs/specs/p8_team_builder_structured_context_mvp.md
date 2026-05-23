# P8 Team Builder Structured Context MVP

Date: 2026-04-28
Contract: `specs/p8_team_builder_structured_context_contract.yaml`

## Purpose

P8 reduces repeated manual team description by letting the user build a
structured team context from the local A-layer battle database, then attaching
that context to normal Agent Chat.

This is a Chat context feature, not a standalone Dex, calculator, simulator, or
team-analysis product route.

## Product Decisions

- First release supports one active team context.
- The data model must keep a `team_id` so later multiple saved teams or team
  switching does not require a contract rewrite.
- Team context persists locally on mobile across app restarts.
- Mobile must not use SecureStore for team context. Team context is not a
  secret, and it may exceed secure-storage comfort limits.
- Team size is 0..6 species. An empty active team is valid as local state but
  should not be attached to `/chat` unless the user intentionally keeps it
  active.
- Species selection is database-picker-only. Search text only filters backend
  database results; a slot cannot be saved without selecting a returned
  `species_id`.
- Move selection is database-picker-only. Search text only filters that species'
  backend available move list; a selected move must come from that list.
- Free text can be stored only as user notes. It must not become a species,
  move, ability, or confirmed battle fact.
- Roco World species have one fixed ability in the current model. Ability is
  copied from the selected species profile; the user does not choose it in P8.
- Each selected species has one nature.
- Each selected species can have 0..3 individual-value bonus stats, each with
  value 7..10.
- Each selected species can have 0..4 selected skills.

## User-Facing Shape

P8 lives under Settings -> `队伍设置`.

The first MVP can be a plain search-and-select builder. It does not need a
graphical dex grid, sprite gallery, drag-and-drop team board, calculator, or
independent analysis page.

Required flow:

1. User opens `队伍设置`.
2. User searches the local battle database for a species.
3. User selects a species result into a team slot.
4. App loads that species profile and its available move list.
5. User searches/filters inside that species' available move list and selects
   up to four moves.
6. User sets one nature and optionally selects 0..3 individual-value bonus
   stats, each with value 7..10.
7. User saves the active team context.
8. Chat automatically sends that context with future `/chat` requests.

Chat remains the only analysis output surface. The main Chat screen may show a
compact team-context chip, but it must not expose raw database/tool traces.

## Source Of Truth

Mobile must not read SQLite directly.

All team-builder lookup goes through Product API endpoints backed by:

```text
data/runtime/battle_dex.sqlite
```

Existing endpoints:

- `GET /species/search?q=...`
- `GET /species/{species_id}`

Required P8 endpoints:

- `GET /species/{species_id}/moves`
- optional `GET /moves/{move_id}` if mobile needs a standalone move detail page

No endpoint should accept mobile-supplied raw SQL, local file paths, or arbitrary
database field selection.

## Team Context Contract

`/chat` must accept structured context attachments:

```ts
type ChatRequest = {
  message: string;
  session_id?: string | null;
  persona_selector?: PersonaSelector | null;
  context_attachments?: ContextAttachment[];
};

type ContextAttachment = TeamContextAttachment;

type TeamContextAttachment = {
  kind: "team_context";
  schema_version: "team_context.v1";
  source: "team_builder";
  team_id: string;
  active: true;
  slots: TeamContextSlot[]; // 0..6
};
```

Each slot is database-grounded:

```ts
type TeamContextSlot = {
  slot_index: number; // 1..6
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

type TeamMoveSelection = {
  move_id: string;
  move_name: string;
  access_channel?: string | null;
  move_type?: string | null;
  category_raw?: string | null;
};

type TeamAbilitySnapshot = {
  ability_name: string;
  effect_text?: string | null;
};

type TeamNature = {
  label?: string | null;
  plus_stat?: TeamStatKey | null;
  minus_stat?: TeamStatKey | null;
};

type TeamIndividualValueBonus = {
  stat: TeamStatKey;
  value: number;
};

type TeamStatKey = "hp" | "atk" | "defense" | "spa" | "spd" | "spe";
```

Validation rules:

- `slots` length: 0..6.
- `slot_index`: integer 1..6 and unique.
- `species_id`: required and must resolve through backend battle dex.
- `selected_moves`: 0..4.
- every `move_id` must be present in that species' available move list.
- `fixed_ability` is copied from backend species profile and is not user-chosen.
- `nature`: required for selected species. If the game supports neutral nature,
  represent it explicitly rather than omitting nature.
- `individual_value_bonuses`: 0..3 items; each stat appears at most once.
- `individual_value_bonuses.value`: integer 7..10. This is grounded in
  `data/reference/luoke_world_type_database_v2.json` stat formula
  `iv_rules.initial_range`.
- `notes` are optional user text and must be treated as unverified user context.

There is no `unresolved` or `user_supplied` move status in P8. If the move is
not in the database-backed available move list, it cannot be selected as a
structured move.

## Agent Integration

P8 attaches team context to `/chat`; it must not create a separate user-facing
Team Analyze result surface.

Runtime behavior:

- backend validates `context_attachments`
- valid team context updates the session's current team substrate
- deterministic team structure analysis can use selected species types
- native Agent instructions can see compact structured team context
- selected moves and fixed ability are available as provisional set context for
  role reasoning
- notes are clearly marked as user notes, not confirmed facts

If a user asks a team question and a valid active team context exists, the Agent
should use it instead of asking the user to manually re-enter the team.

## Storage

Mobile stores the active team context locally.

First release may expose only one active team, but local storage should be shaped
as a collection:

```ts
type TeamContextStore = {
  schema_version: "team_context_store.v1";
  active_team_id: string | null;
  teams: TeamContextAttachment[];
};
```

This keeps later multi-team switching cheap without requiring P8 to ship a full
team-management UI.

## Security And Privacy

- Provider API keys remain request-scoped settings and are unrelated to team
  storage.
- Team context must not be stored in SecureStore.
- Team context must not be logged wholesale by the API.
- API responses must not echo raw request headers or local database paths.
- Mobile must not display raw tool traces or raw SQL-origin payloads.

## Non-Goals

- no graphical dex grid in P8
- no official IP sprites/assets
- no direct mobile SQLite access
- no free-text species creation
- no free-text move creation
- no independent `/team/analyze` product page
- no calculator UI
- no battle simulator
- no casebank retrieval expansion
- no web/live meta lookup

## Implementation Surfaces

Likely backend files:

- `api/contracts.py`
- `api/main.py`
- `api/services/advisor_service.py`
- `advisor/runtime.py`
- `advisor/battle_dex.py`
- `battle_engine/contracts.py`
- `tests/test_api.py`
- `tests/test_advisor.py`

Likely mobile files:

- `mobile/src/api/types.ts`
- `mobile/src/api/client.ts`
- `mobile/src/roco/teamContext.ts`
- `mobile/src/components/roco/TeamContextBuilder.tsx`
- Settings drawer integration
- Chat request construction
  - Active team context is attached silently through `context_attachments`.
  - Chat main screen must not render an active-team chip in V1.

## Acceptance Criteria

- User can build one active team context through database search/filter and
  result selection.
- Team context accepts 0..6 selected species.
- Species slots require backend `species_id`; free-text species cannot be saved
  as structured slots.
- Move selection is limited to backend available moves for the selected species;
  move search only filters the available move list.
- Each selected species has one nature, 0..3 individual-value bonus stats valued
  7..10, and 0..4 selected moves.
- `/chat` accepts `context_attachments` and validates team context.
- Agent uses valid active team context for team questions instead of asking for
  manual re-entry.
- Chat remains the only analysis output surface.
- No Team/Dex/Calculator tab or standalone product route is added.
- Team context persists locally across app restarts.
- Mobile typecheck passes.
- Backend tests cover valid context, invalid species, invalid moves, partial
  team, and no secret/path leakage.

## A-Layer Stat Rule

The exact Roco World individual-value bonus range is confirmed by:

- `data/reference/luoke_world_type_database_v2.json`
- `wiki/raw/source_notes/2026-03-25_bilibili_iv_nature_stat_training.md`

Current rule:

- IV initial range: 7..10
- up to 3 stats can have IV bonuses
- PvP IV multiplier: 6
- PvP IV contribution range: 42..60
- nature boost: +20%
- nature penalty: -10%
