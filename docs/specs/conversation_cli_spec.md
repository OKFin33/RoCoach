# Conversation CLI Spec

## Purpose

Define the first user-facing delivery surface for the advisor:

- `conversational Agent CLI`

## Product Goal

The CLI should feel like a constrained battle advisor, not a shell wrapper around
one-shot commands.

Boundary note:

- the CLI is the first delivery surface, not the final product presentation
  standard
- it may remain more explicit/debug-friendly than mobile or future public chat
  surfaces
- raw analytical fields that are acceptable in CLI are not automatically the
  correct default public UX
- future product surfaces may route analytical facts through synthesis,
  presentation, and persona before the user sees the answer

For MVP, the CLI is allowed to run in a temporary dual-track mode:

- a deterministic path may coexist with `pydantic_ai_native` during migration
- the approved runtime direction remains `PydanticAI` native
- this dual-track period does not expand MVP scope
- default backend policy is `auto`:
  - use `pydantic_ai_native` when valid native model env config exists
  - otherwise fall back to `deterministic`
  - if native execution fails or times out under `auto`, fall back to
    `deterministic` for supported deterministic/species flows
  - after native failure under `auto`, the current CLI process may skip further
    native attempts and use deterministic fallback directly
  - explicit backend overrides must be preserved

It should support:

- natural-language questions
- iterative refinement
- team-context carryover inside the current session

## Session Model

Each CLI session should maintain:

- current team
- current user goals
- current constraints
- last answer summary
- last referenced species or slot

The session should end cleanly when the user exits.

No cross-session persistence in v1.

## Supported User Intents

### 1. Team Structure Analysis

Examples:

- “分析这队联防”
- “这队有什么洞”
- “补洞方向是什么”

### 2. Species Role Discussion

Examples:

- “这只精灵在这队里更像主C还是辅助”
- “它在受队里是不是联防件”

### 3. Team Identity Discussion

Examples:

- “这队更像平衡还是受队”
- “节奏是不是太慢”

### 4. Iterative What-If

Examples:

- “如果把 3 号位换成火系呢”
- “不想太被动，怎么改”

## Suggested Slash Commands

Natural language remains primary, but the CLI may expose:

- `/team`
- `/set-team`
- `/show-team`
- `/analyze`
- `/clear`
- `/help`
- `/exit`

Slash commands should improve usability, not replace natural language.

## Output Rules

Every response should include:

- concise answer
- evidence summary
- confidence notes
- optional next-step prompts

When useful, responses should separate:

- `hard facts`
- `interpretation`
- `what-if guidance`

CLI-specific note:

- the CLI may show analytical structure more directly than future public/mobile
  surfaces
- this is acceptable because the CLI doubles as an inspection surface
- future presentation layers should preserve the same grounded content while
  defaulting to a more coach-like conversational reply
- the product's eventual default `Reply + Why` surface should not be blocked by
  the CLI remaining more explicit

## Tool Use

The CLI should delegate to the advisor runtime.

It should not directly reimplement:

- structure scoring
- retrieval
- semantic judgement

## Failure Behavior

If the user asks for unsupported features:

- reject cleanly
- explain the current boundary
- offer a nearby supported path
- for future/live-meta or official balance prediction, state that the MVP has no
  web/live official-balance feed and cannot predict future buffs/nerfs or live
  meta changes

If evidence is insufficient:

- answer partially
- mark uncertainty
- suggest what extra input would improve confidence

If only a partial team is supplied:

- the CLI may still analyze the supplied slots
- output must clearly mark the analysis as partial-team
- follow-up options should ask for the missing slots

If native runtime/provider execution fails:

- under `auto`, fall back to deterministic when possible
- under `auto`, avoid repeated timeout stalls in the same CLI process after
  native has been marked unhealthy
- under explicit `pydantic_ai_native`, return a bounded native failure response
- no CLI command should hang indefinitely

## First Delivery Boundary

V1 should support:

- current team entry
- team structure analysis
- battle-dex-backed species profile lookup
- constrained semantic discussion
- follow-up questions within the same session
- a migration-safe CLI surface while runtime internals move toward
  `PydanticAI` native orchestration

V1 should not support:

- persistent saved sessions
- autonomous web search
- full team export/import management
- GUI

## Implementation Notes

The CLI should sit above:

- `advisor runtime`
- `battle-dex retrieval`
- `doc retrieval`

For MVP, the CLI should not require:

- `case retrieval`
- tactical casebank context as a live dependency

It should be thin and render typed runtime outputs into readable terminal text.

Backend selection is CLI policy only. It must not add new tools, retrieval
branches, memory behavior, or semantic-analysis scope.

When rendering evidence, the CLI should keep output compact while ensuring at
least one approved doc/context item is visible when doc retrieval ran.

The CLI is allowed to remain closer to the analytical contract than mobile,
because it functions as both user interface and debug/inspection surface.
