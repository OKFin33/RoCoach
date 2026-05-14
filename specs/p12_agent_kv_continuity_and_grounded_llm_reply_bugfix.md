# P12 Agent KV Continuity And Grounded LLM Reply Bugfix

Status: requested  
Date: 2026-05-07  
Owner: backend runtime + desktop integration  
Primary goal: make RoCoach V1 behave as one continuous Agent chat where every
normal user question is received, planned, and answered by the Agent boundary.
Routes only decide the Agent's internal work; they must not decide whether the
user gets an Agent reply.

## Zero-Context Summary

Current RoCoach desktop has a single active SQLite session and can persist some
runtime state across backend restart. That is not enough for V1 release. The
current user experience still splits into incompatible paths:

- native LLM path for some natural chat, such as greeting or broad guidance;
- deterministic local path for known species/team questions, such as
  `怎么反制圣羽翼王`.

This creates a false Agent surface. A user can see a slow LLM reply for `你好`,
then receive an immediate deterministic species summary for `怎么反制圣羽翼王`,
then ask `什么意思` and lose the semantic context of the previous battle answer.

This is a V1 blocker. Roco V1 is supposed to be a single Agent chat, not a
mixed command router wearing a chat skin. The router may choose tools,
grounding, clarifying questions, or zero-tool direct chat, but it lives inside
the Agent runtime boundary.

## Observed Failure

Repro from the running desktop/API process on 2026-05-07:

1. User asks `你好`.
2. Desktop waits for a model-like response.
3. User asks `怎么反制圣羽翼王`.
4. API returns immediately with:
   - `backend = deterministic`
   - `analysis_type = species_analysis`
   - a deterministic pre-grounded summary about 圣羽翼王.
5. User asks `什么意思`.
6. The reply behaves as if the previous battle answer is not part of the active
   Agent conversation.

Verified runtime facts:

- Electron-managed session DB:
  `~/Library/Application Support/Electron/roco_session/session.sqlite3`
- `session_meta.active_session_id` exists.
- `session_state.state_json.current_species_context` can be `圣羽翼王`.
- `session_state.native_messages_json` can exist, but deterministic turns are
  not integrated into the native conversation history.
- `/metadata.default_backend` currently reports `deterministic`.
- `api/release.py` reports KV continuity, but the product-level Agent continuity
  is not closed.

## Root Cause

The bug is not simply missing SQLite persistence.

Root cause is a broken boundary between:

- `AdvisorSessionState` KV fields;
- native provider message history;
- deterministic pre-grounding tool output;
- final user-visible Agent synthesis.

Current failure modes:

1. Known species/team routes can terminate in deterministic output instead of an
   LLM terminal response.
2. `_native_pregrounded_species_response` and `_native_pregrounded_team_response`
   label output as native-adjacent but do not actually perform LLM synthesis.
3. Deterministic turns are not written into a model-readable conversation digest.
4. Elliptical follow-up routing only covers narrow pronouns such as `它`, `这只`,
   and `这个精灵`; it does not understand `什么意思`, `解释一下`, `继续`, or
   `刚才那段`.
5. Desktop visible messages, SQLite state, and native model history can diverge
   while the UI still appears to be one continuous chat.
6. The current durable subject model is effectively a single current species
   slot plus compact turn text. It cannot represent ordinary coaching context
   where the user is discussing several species, roles, and relations such as
   `黑猫巫师 -> 配合恶魔狼主c`.

## Product Decision

For V1, all normal user questions must be Agent answers.

The routing scheme is an internal Agent planner:

- decide whether the Agent needs zero tools, one tool, multiple tools, grounded
  retrieval, clarification, or a controlled degraded fallback;
- decide which continuity summaries, topic-pool entities, team-setting entities,
  and active relation focus should be used;
- never decide that a normal user question bypasses the Agent and returns a raw
  deterministic terminal response.

General-chat rule:

- Because RoCoach is consumer-facing, general chat also enters the Agent
  boundary. It may use zero tools, but it must still use the active continuity
  layer, persona boundary, safety policy, and reasoning/synthesis path when
  needed.
- Off-domain or unsupported questions are still Agent-handled. They should
  receive a concise product-bounded answer, clarification, or refusal/degraded
  response; they must not fall back to a raw router or command-style unsupported
  message.
- Tool use is domain-conditional. General chat does not need forced retrieval,
  but any concrete Roco species, move, mechanism, team, counterplay, or relation
  claim must be grounded or explicitly marked as provisional/unsupported.

Architecture boundary:

- RoCoach is an Agentic runtime containing planner, grounding/retrieval,
  reasoning/synthesis, validation, continuity, and presentation loops.
- Retrieval is a grounding capability inside the Agent reasoning loop. It may
  have separate implementation modules such as `advisor/retrieval.py`, SQL
  repositories, or future D-layer case stores, but it must not become an
  independent user-facing answer path.
- Retrieval outputs are evidence/tool results. They are inputs to synthesis, not
  final answers.
- Any implementation where retrieval directly assembles normal user copy, or
  bypasses terminal Agent synthesis while native runtime is available, violates
  this launch.

Runtime-depth target:

```text
plan
  -> ground
  -> validate packet
  -> maybe retrieve more / ask clarification
  -> synthesize
  -> grade trace / answer
  -> persist continuity
  -> return user-visible answer
```

This must be a bounded agentic loop, not open-ended autonomy. V1 default cap:
one initial plan plus at most two repair iterations before either terminal
synthesis or a concise clarification/degraded response.

Explicit system controls may remain control operations, but ordinary
natural-language user questions must be answered through the Agent surface.

Static control allowlist:

- `POST /session/clear`
- desktop clear-current-chat action wired to the same service path
- exact slash command `/clear`
- release/metadata/status endpoints

Only these may return `static_control_response`. Unknown slash-like text,
ordinary natural-language text, and malformed control-looking user messages must
default to Agent handling or concise clarification, not router bypass.

`怎么反制圣羽翼王` is not a pure deterministic terminal path. It must be:

```text
user question
  -> plan counterplay/species grounded synthesis
  -> ground with approved tools
  -> validate compact grounding packet
  -> if packet is insufficient, retrieve more or ask one clarification
  -> run terminal LLM synthesis over the validated packet
  -> grade trace and answer shape
  -> persist a non-secret turn summary into KV
  -> return one user-facing Agent reply
```

Deterministic/local code remains mandatory as the source of confirmed facts. It
must not be the final user experience for normal user questions when native
runtime is configured and available.

## Required Behavior

### 1. Agent Reply Availability

When provider settings are complete and native runtime is available:

- `你好` uses native Agent chat.
- `怎么反制圣羽翼王` uses native Agent grounded synthesis.
- `什么意思` after that explains the previous 圣羽翼王 answer.
- Any ordinary user question enters the Agent boundary. If no tool is needed,
  the Agent may answer directly. If tools are needed, the Agent plans and calls
  them before answering.
- The final `AgentResponse.runtime_path` must be `native_llm_terminal` when
  native runtime is configured and available.
- `runtime_path` is the authoritative product-path field. `backend` describes the
  implementation/provider that executed the turn; it must not be used by UI or
  release gates to infer whether the answer was Agent terminal synthesis.
- The final answer must read like a tactical conclusion, not a raw fact dump.

When provider settings are missing or native runtime fails:

- The system may return deterministic fallback only if the response explicitly
  marks degraded mode in metadata/confidence notes.
- The UI/metadata must not imply full Agent availability.
- The fallback must not overwrite valid native history with an unrelated
  deterministic-only conversation state.
- Deterministic fallback may answer only when it can form a valid packet from
  verified local facts or already validated context. If it cannot form a valid
  packet, it must ask clarification or return a bounded degraded response.
- Deterministic fallback must not write native protocol history. It may write a
  compact degraded turn summary and trace metadata.

### 2. Grounded Tool Use

For `怎么反制圣羽翼王`, the Agent must ground before synthesis.

Required minimum grounding:

- resolve `圣羽翼王` via SQLite species lookup;
- fetch species profile;
- fetch available moves;
- retrieve relevant mechanism docs based on ability/move text and user intent;
- produce a compact counterplay packet including:
  - confirmed facts;
  - provisional tactical interpretation;
  - confidence limits;
  - recommended counterplay dimensions.

The final LLM reply must synthesize from this packet. It must not invent moves,
types, abilities, official live-meta facts, or unreviewed mechanics.

Packet validation gate:

- Before synthesis, the runtime must validate a compact `GroundingPacket` or
  equivalent internal object.
- Required packet fields:
  - `intent`
  - `subjects` with stable ids where resolved
  - `tool_calls`
  - `evidence_items`
  - `supported_claims`
  - `missing_evidence`
  - `confidence_floor`
  - `followup_or_clarification_needed`
  - `topic_pool_delta`
- `intent` must be an enum, with at least:
  - `general_chat`
  - `species_profile`
  - `counterplay`
  - `relation_team_core`
  - `team_analysis`
  - `followup_explanation`
  - `control_response`
- `subjects` must be a typed list with:
  - `subject_type`: `species`, `team`, `move`, `mechanic`, or `unknown`;
  - stable id when resolved, such as `canonical_species_id`;
  - `display_name`;
  - `resolution_status`: `resolved`, `ambiguous`, `unresolved`, or `invalid`;
  - optional `role_hint`.
- `tool_calls` must include tool name, normalized args digest, status
  (`success`, `failed`, `skipped`), returned evidence ids, and error code when
  failed.
- `missing_evidence` must be typed with `kind`, `severity`, and
  `can_repair_by`:
  - `kind`: `ambiguous_subject`, `missing_user_team`, `tool_failed`,
    `case_meta_unavailable`, `mechanism_doc_missing`, or `unsupported_claim`;
  - `severity`: `blocking` or `non_blocking`;
  - `can_repair_by`: `retrieve_more`, `ask_clarification`, or `degrade`.
- `confidence_floor` must be an enum such as `confirmed_only`,
  `confirmed_plus_provisional`, or `insufficient`.
- `followup_or_clarification_needed` must include a boolean plus optional
  `question_text` and `reason_code`.
- `evidence_items` must use a strong schema:
  - `evidence_id`
  - `source_type`
  - `entity_ref` or `source_path`
  - `version`
  - `confidence_tier`
  - `content_digest`
  - `retrieval_reason`
- `supported_claims` must map each grounded claim to evidence:
  - `claim_id`
  - `claim_text_digest`
  - `supporting_evidence_ids`
  - `support_level`: `confirmed`, `provisional`, or `unsupported`
  - `provisional_reason` when not confirmed
- If required evidence for the planned answer is missing, the runtime may perform
  one bounded retrieve-more iteration. If the missing item is user-specific
  intent or ambiguous anchor, it must ask one concise clarification instead of
  inventing.
- Packet validation must fail closed: no terminal answer may claim a grounded
  conclusion that is not supported by packet evidence.
- Negative validation tests must cover invalid subjects, failed required tool
  calls, unsupported claims, ambiguous missing evidence, and clarification
  required but absent.

Relation/team-core evidence boundary:

- V1 relation/team-core advice is allowed, but it must state its evidence level.
- With only A/B-layer facts and reviewed mechanism snippets, the answer may give
  a `provisional` tactical judgement such as "基于当前资料/技能机制的初步判断".
- It must not present casebank/meta-graph/live-meta experience as confirmed when
  D-layer/case retrieval is out of scope or unavailable.
- If the user asks for environment-level certainty or mature lineup experience,
  the Agent must say that current evidence does not support that level and ask
  for concrete team/matchup context or provide a bounded provisional answer.

Consumer uncertainty copy contract:

- Do not expose internal labels such as A/B/D layer, packet, source, backend,
  runtime path, or model name.
- Use natural evidence tiers in normal copy:
  - confirmed fact: `已确认的是...`, `这只精灵当前资料里有...`;
  - bounded tactical judgement: `按当前资料看...`, `更像是...`, `可以先按...理解`;
  - missing team/matchup context: `还要看你另外几只怎么补...`, `如果对面有...会反转`;
  - unavailable case/meta certainty: `仅凭这两只还不能断言这是成熟核心`;
  - clarification request: `你是想围绕它主C打，还是只问这两只怎么配合？`
- Relation/team-core answers should preserve practical usefulness. They should
  not become legal disclaimers; the boundary copy should be one short phrase or
  one concise caveat attached to the actual advice.
- Answer-shape checks must reject affirmative unsupported certainty claims such
  as `最优`, `必带`, `稳吃`, `环境答案`, or `成熟核心` unless the packet has matching
  case/meta/live evidence. Negated or caveated uses such as
  `仅凭这些还不能断言这是成熟核心` are allowed and should be treated as correct
  uncertainty copy.

Retrieval placement rule:

- SQL species lookup, move lookup, mechanism-doc retrieval, and future D-layer
  case retrieval are all approved grounding tools/capabilities selected by the
  Agent planner.
- They may run deterministically and may live in independent code modules for
  maintainability.
- They must return bounded evidence with source/confidence metadata into the
  Agent loop.
- They must not render normal chat answers directly.

Trace and answer grading gate:

- Every ordinary Agent turn must produce a hidden `AgentExecutionTrace` or
  equivalent QA record.
- Minimum fields:
  - `turn_id`
  - `session_id`
  - `plan_intent`
  - `loop_iterations`
  - `tool_calls`
  - `retrieval_refs`
  - `grounding_packet_status`
  - `topic_pool_delta`
  - `runtime_path`
  - `answer_shape_checks`
  - `final_grade`
- Trace storage boundary:
  - trace is local QA/test metadata, not normal response payload;
  - default normal UI must not display raw traces;
  - traces must exclude provider keys, raw request headers, and hidden
    chain-of-thought;
  - traces are not written to long-term archive by default; archive may include
    summary counts/status only.
- Required answer checks:
  - no raw JSON/tool payload/route/backend label in normal copy;
  - no Constitution-forbidden internal labels in normal copy, including
    `A-layer`, `B-layer`, `D-layer`, `source`, `prompt`, model/provider names,
    route names, backend/runtime labels, or raw tool names;
  - grounded claims cite packet evidence internally;
  - relation questions mention and preserve both relation endpoints;
  - degraded/native-failure paths are marked in metadata;
  - unsupported/clarification paths are concise and actionable.
- Failed grading must either repair within the bounded loop or return a safe
  clarification/degraded answer. It must not silently ship a failed answer.
- Grader mechanism:
  - deterministic checks are authoritative for leakage, required metadata,
    packet support, runtime_path, relation endpoints, and degraded markers;
  - optional LLM grading may judge readability or tactical usefulness, but must
    not override deterministic fact-support checks;
  - final grade values are `pass`, `repaired`, `clarify`, or `degraded`.

Loop state machine:

- Loop states: `planned`, `grounding`, `packet_invalid`, `packet_valid`,
  `needs_clarification`, `synthesizing`, `grading`, `repairing`, `terminal`.
- Allowed actions: `retrieve_more`, `ask_clarification`, `synthesize`, `repair`,
  `degrade`.
- Stop reasons: `answered`, `clarification_required`, `degraded_native_failure`,
  `degraded_packet_insufficient`, `max_iterations`, `control_response`.
- Tool calls are deduped by tool name and normalized arguments within a turn
  unless a previous call explicitly filled different missing evidence.
- `packet_status` is monotonic within a turn except that `packet_invalid` can
  become `packet_valid` after retrieve-more; a valid packet must not be made less
  specific by later repair.
- Max repair depth remains one initial pass plus two repair iterations.

### 3. Counterplay Intent

Add or tighten a first-class internal route for counterplay questions.

Examples:

- `怎么反制圣羽翼王`
- `圣羽翼王怎么打`
- `怎么针对它`
- `这只怎么处理`
- `碰到它怎么办`

This route may reuse species grounding, but it is not a user-visible mode. The
final Agent answer must be oriented toward counterplay, not merely species
positioning.

Expected answer shape:

- identify what 圣羽翼王 threatens based on grounded facts;
- explain what is confirmed vs provisional;
- give practical counterplay axes such as speed/priority, response timing,
  pressure on resource/magic, team role disruption, and move-category baiting
  only when grounded by available evidence;
- ask for the user's team only when needed for specific matchup advice.

### 4. Topic Pool KV Continuity Across All Runtime Paths

KV continuity must include deterministic-grounded turns, not only native model
messages. It must also preserve the active product conversation as a small
topic graph, not as a single `current_species_context` slot.

This is a two-layer continuity model. The topic pool preserves durable entities,
roles, relations, and active focus. `recent_turn_summaries` remains mandatory
because it preserves what was said, what conclusion was reached, and what
grounding evidence supported that conclusion. Neither layer replaces the other.

Memory product boundary:

- P12 implements active-session continuity only.
- P12 may use user-facing wording such as `记住当前对话里我们在聊谁/怎么搭配`
  after acceptance, but it must not claim full user memory, long-term memory, or
  personalization memory.
- Complete memory is a future layer, not a P12 dependency. It would require:
  cross-session recall, user preference/profile memory, user-managed memory UI,
  memory edit/delete/export controls, feedback learning, retention policy, and
  memory-specific evals for stale/wrong/private recall.
- Near-term upgrade path after P12 is `V1.1 user-controlled preferences and
  current/common team memory`, not unbounded autonomous long-term memory.

Add a non-secret topic continuity layer to `AdvisorSessionState`, for example:

```python
conversation_topic_pool: ConversationTopicPool
recent_turn_summaries: list[AdvisorTurnSummary]
```

`current_species_context` may remain temporarily as a backwards-compatible
derived field, but it must not be the primary continuity mechanism for routing,
grounding, native instructions, or restart recovery.

Minimum topic-pool fields:

- `species`: bounded list of mentioned/resolved species entries.
- `relations`: bounded list of user-stated or inferred relation edges.
- `active_focus`: current question focus, including whether the user is asking
  about one species, a relation, a team core, or a follow-up.
- `updated_at` / turn references sufficient for TTL and recency decisions.

Minimum `ConversationActiveFocus` fields:

- `focus_type`: `none`, `single_species`, `relation`, `team_core`,
  `followup`, or `team_analysis`.
- `subject_species_ids`: ordered list of resolved species ids when available.
- `subject_display_names`: display fallback for unresolved subjects.
- `relation_edge_id`: id of the active relation edge when `focus_type=relation`
  or `team_core`.
- `from_species_id` / `to_species_id` and optional `from_role` / `to_role` for
  relation/team-core focus.
- `anchor_turn_id`: turn that established the focus.
- `updated_turn_id`: latest turn that refreshed the focus.
- `confidence`: `unresolved`, `user_mentioned`, `team_seeded`, or
  `tool_resolved`.

Active-focus transitions:

- explicit single species mention sets `single_species` unless relation markers
  connect it to an existing anchor.
- relation markers such as `配合`, `搭配`, `围绕`, `辅助`, `保`, `主C`, `副C`,
  `首发`, or `收割` set `relation` or `team_core` and preserve the prior anchor
  when plausible.
- short follow-ups reuse the last grounded active focus.
- ambiguous multi-anchor follow-ups ask one clarification and do not mutate focus
  until clarified.
- clear/reset sets `focus_type=none` and removes pending follow-up anchors.

Minimum species entry fields:

- `canonical_species_id`: stable SQLite species id when resolved. This is the
  join key for grounding, team-context merge, and relation edges.
- `display_name`
- `canonical_name`
- `aliases`
- `role_hints`, such as `首发`, `主C`, `副C`, `功能位`, `收割`
- `source_records`: list of source records, not a singular source string
- `mention_count`
- `last_seen_turn`
- `confidence`

Minimum source record fields:

- `source_type`: `user_mention`, `team_setting`, `tool_resolution`, `summary`, or
  `active_focus`.
- `turn_id` or `attachment_id`
- `confidence`
- `last_seen_turn`

Source update rules:

- Upsert source records by `(source_type, turn_id/attachment_id)` where possible.
- Removing a species from the active team removes only `team_setting` source
  records for that team attachment.
- The species entry remains if any `user_mention`, `tool_resolution`, `summary`,
  or current `active_focus` source record remains.
- If no source records remain and the entry is not active focus, evict it on the
  next topic-pool compaction.

Minimum relation edge fields:

- `type`, such as `synergy`, `counterplay`, `supports`, `protects`,
  `checks`, `replaces`, `competes_with`
- `from_species_id`
- `to_species_id`
- `from_display_name`
- `to_display_name`
- optional `from_role` / `to_role`
- `evidence_text` or `evidence_turn_id`
- `confidence`

Minimum turn summary fields:

- `turn_id`
- `user_message_excerpt`: short redacted excerpt for diagnostics only
- `user_message_digest`
- `intent_digest`
- `route_intent`
- `resolved_subject`
- `answer_digest`
- `grounding_refs`
- `tool_names`
- `runtime_path`
- `backend`: implementation/provider metadata only
- `created_at`

Rules:

- store compact summaries, not raw hidden reasoning;
- do not persist raw user messages in backend continuity state;
- keep full visible transcript frontend-owned unless a separate explicit product
  requirement changes that boundary;
- redact obvious secrets, tokens, keys, phone numbers, and account identifiers
  from `user_message_excerpt`;
- never store provider API keys or raw request headers;
- keep native protocol messages serialized with `ModelMessagesTypeAdapter`;
- include deterministic-grounded turn summaries and compact topic-pool state in
  native instructions for the next turn;
- summaries carry answer continuity; topic pool carries object/relation
  continuity. The planner must use both when resolving follow-ups;
- keep the topic pool bounded with deterministic eviction:
  - default maximums: 16 species entries and 32 relation edges;
  - upsert species by `canonical_species_id` when resolved, otherwise by
    normalized display/alias text with `confidence=unresolved`;
  - increment `mention_count` on explicit user mention, tool resolution, or
    team-setting seed refresh;
  - promote confidence in this order:
    `unresolved < user_mentioned < team_seeded < tool_resolved`;
  - dedupe relation edges by `(type, from_species_id, to_species_id, from_role,
    to_role)` when ids exist, otherwise by normalized display names;
  - evict lowest priority first: unresolved entries, stale low-confidence
    entries, lowest `mention_count`, oldest `last_seen_turn`;
  - never evict a species referenced by the current `active_focus` unless the
    user clears/resets the session;
- user-configured team slots are an input source into the same pool, not a hard
  prerequisite for advice. A user can get coaching by typing names naturally;
  team setting only makes bulk context input easier.

Team-setting seed protocol:

- Ingestion boundary is `/chat.context_attachments` with `kind=team_context`
  as defined by P8. Backend may materialize the validated attachment into
  `AdvisorSessionState.current_team`; the topic pool must be seeded from that
  validated structured state, not from raw frontend text.
- Seed/update runs during request intake before route planning, so the router can
  use active team species for pronouns and `我这队` questions on the same turn.
- Team seeded entries add a `source_record` with `source_type=team_setting` and
  preserve `canonical_species_id`, `display_name`, selected moves, nature, and
  slot index as compact non-secret context.
- Removing a species from the active team removes the `team_setting` source from
  that pool entry. It must not delete the entry if it also has user-mention,
  tool-resolution, or active-focus evidence.
- User chat mentions and tool resolution can promote or keep an entry after it
  leaves the team. Team settings are convenient structured input, not ownership
  over the conversation topic.
- Invalid team attachments are attachment-level validation failures under the P8
  contract. They must be discarded/diagnosed and must not partially mutate the
  topic pool.
- Invalid team attachments must not block unrelated ordinary chat. If the message
  is not explicitly asking for team analysis, the runtime should ignore the
  invalid attachment for that turn, avoid topic-pool mutation, add diagnostic
  metadata, and answer using non-team context. The `/chat` request itself should
  not be rejected unless the current user intent explicitly depends on team
  analysis. Explicit team-analysis requests may be blocked with a concise request
  to fix team settings.
- P8 `species_id` maps to P12 `canonical_species_id`. The materializer must
  validate every slot and selected move before mutation, then compact slot index,
  selected moves, nature, and source markers into topic-pool entries only after
  the full attachment passes validation.

### 5. Multi-Species And Relation Follow-Up Support

The router must resolve short follow-ups against the topic pool, active focus,
and previous turn summaries.

Required follow-up examples:

- `什么意思`
- `解释一下`
- `展开说`
- `继续`
- `那怎么打`
- `这是什么意思`
- `你刚才说的副C是什么意思`
- `配合恶魔狼主c` after discussing `黑猫巫师`
- `那它辅助谁更好`
- `我这队怎么围绕它打`
- `这六只里谁适合首发`

If a recent grounded turn exists, these must route to either:

- native general chat with recent turn summaries in instructions; or
- grounded follow-up synthesis with the topic pool, active focus, and relevant
  grounding packets.

They must not return the generic MVP unsupported message when the previous turn
contains a usable grounded subject.

Relation continuity rule:

- If the prior active focus is species A and the new user message introduces
  species B with relation markers such as `配合`, `搭配`, `围绕`, `辅助`, `保`,
  `主C`, `副C`, `首发`, or `收割`, the planner must treat this as a relation or
  team-core query involving A and B. It must not blindly replace A with B as the
  only active subject.
- If the topic pool contains multiple plausible anchors, ask one concise
  clarification instead of guessing.
- The final answer should state the relation being answered in natural copy,
  for example: `如果你的意思是让黑猫巫师服务恶魔狼主C...`.

Evolution-default rule:

- In ordinary battle/coaching language, a base-stage or shorthand species name
  defaults to the final evolution on the same evolution line. Example: `小夜有
  什么玩法` and `小朔夜有什么玩法` resolve to `朔夜伊芙` unless the user explicitly
  asks about the unevolved/base form.
- Explicit non-final-form markers such as `未进化`, `不进化`, `一阶`, `低阶`,
  `初始形态`, `原始形态`, `小形态`, or `本体` preserve the lower-stage subject.
- Structured lookup commands may still preserve the exact requested species so
  the app remains usable as a dex.

User-visible uncertainty copy rule:

- Internal terms such as `provisional`, `reviewed`, `D-layer`, `案例库`,
  `grounding packet`, `runtime_path`, and tool/trace labels must not appear in
  the primary user-facing answer.
- When evidence is partial, express the boundary as natural coaching copy:
  `按现在看到的信息`, `稳一点说`, `别把它当固定套路`, or `要看配招和队友保护`.
  Do not over-explain the backend reason.

### 6. Desktop/API Contract

Desktop already persists `session_id` and visible messages. Keep that behavior,
but add enough runtime diagnostics for QA:

- response metadata must reveal whether the final answer was:
  - `native_llm_terminal`
  - `deterministic_degraded_fallback`
  - `static_control_response`
- `/metadata` must not make full Agent continuity claims unless this bugfix is
  complete.
- normal UI should not show backend labels as main copy, but QA logs/tests must
  be able to assert the path.
- normal UI should never present route names, raw tool results, rules, or
  structured grounding packets as the main answer to an ordinary question.
- When active team context actually affects an answer, normal copy should make
  that context legible in natural language, e.g. `按你当前队伍这几只看...`, without
  showing debug chips or raw attachments.
- Team context materially affects an answer when a final supported claim uses
  evidence whose source record includes `team_setting`, or when active focus was
  seeded from validated team context for the current answer. Snapshot tests must
  cover one positive case with the natural hint and one negative case without it.
- Latency/timeout UX:
  - default provider timeout: 45 seconds;
  - default per-tool timeout: 8 seconds;
  - default max total turn timeout: 60 seconds;
  - defaults may be overridden by environment/config for tests and local
    development, but acceptance must use concrete configured values;
  - desktop must show a loading state for native/loop work and allow safe cancel
    when supported;
  - timeout exits through `deterministic_degraded_fallback` or concise
    clarification metadata, not a hanging spinner.
  - negative tests must simulate provider hang, tool hang, and max-turn timeout.

### 7. State Migration, Atomicity, And Reconciliation

State compatibility is part of the product contract.

- `AdvisorSessionState` must carry an explicit state schema version or be wrapped
  by a versioned session-state envelope.
- P11 -> P12 migration must fill defaults:
  - empty `conversation_topic_pool`;
  - empty or bounded `recent_turn_summaries`;
  - empty trace state;
  - preserved `current_team`, `current_species_context`, and native history when
    compatible.
- Unknown future fields must be ignored or preserved according to a documented
  policy; bad JSON or incompatible native history must drop only the unsafe part
  and emit a controlled diagnostic event.

Per-turn commit model:

- Generate one `turn_id` at request intake.
- Validate context attachments before route planning.
- Build a staged state delta for summary, topic pool, native history pointer,
  current team, and trace summary.
- Commit staged state in one SQLite transaction after terminal response is
  generated and graded.
- If the response is generated and graded but the state commit fails, return the
  user-visible answer with diagnostic metadata:
  `continuity_persisted=false`, `session_event=continuity_not_persisted`, and a
  redacted internal error code. Do not claim continuity was saved.
- If no response can be generated because the session store is unavailable before
  planning, public app paths return a controlled degraded/clarification response
  with `continuity_persisted=false`.

Session reconciliation protocol:

- SQLite `active_session_id` remains authoritative.
- Stale desktop `session_id` maps to active session with a `reconciled` event
  unless that id was explicitly cleared after archive.
- A cleared session id must not be allowed to resurrect old summaries, topic
  pool, native history, or current team.
- Native history deserialization failure drops native messages only; summaries
  and topic pool are the fallback continuity source.
- DB lock/corruption may use in-memory fallback only in explicit dev mode; public
  app paths must surface a recoverable degraded event.

Clear/reset atomicity:

- Clear chat must atomically reset visible messages, recent summaries, topic
  pool, native history, pending follow-up targets, and current-species focus.
- V1 policy: preserve user-configured team settings in frontend/app settings, but
  clear backend active conversation team context.
- Clear chat sets `AdvisorSessionState.current_team=None`, removes
  `team_setting` source records from topic-pool entries, evicts entries that have
  no remaining source records, clears active focus, clears recent summaries,
  clears native history, and instructs frontend visible messages to clear.
- Team settings re-enter the conversation only when the desktop sends a validated
  `team_context` attachment on a later `/chat` request.
- Archive records must not participate in future active routing.

## Non-Goals

Do not add:

- multi-session UI;
- global long-term memory;
- persona growth memory;
- official live-meta/web search;
- hosted key custody;
- D-layer/P10h casebank dependency;
- battle-engine exact simulator.

This is a V1 continuity and Agent-runtime closure bugfix, not a new product
surface.

## Implementation Notes

Likely files:

- `advisor/contracts.py`
  - extend `AdvisorSessionState` with compact turn summaries and
    `ConversationTopicPool`.
  - add `GroundingPacket` and `AgentExecutionTrace` models or exact equivalents.
- `advisor/runtime.py`
  - add counterplay route.
  - add relation/team-core routing over the topic pool.
  - implement bounded loop:
    `plan -> ground -> validate packet -> maybe retrieve/clarify -> synthesize
    -> grade trace/answer`.
  - make known species/team grounded questions use LLM terminal synthesis when
    native runtime is available.
  - keep retrieval calls inside grounding/tool execution before synthesis; do not
    introduce a separate retrieval terminal responder.
  - write turn summaries after every successful user-visible response.
  - update the topic pool after every successful user-visible response.
  - feed recent summaries and compact topic-pool state into
    `_native_instructions`.
- `api/services/session_store.py`
  - serialize new state fields through existing Pydantic JSON path.
  - implement schema migration, per-turn atomic commit, reconciliation, and
    clear/reset atomicity.
- `api/services/advisor_service.py`
  - ensure request-scoped native runtime and active SQLite store stay aligned.
- `api/release.py`
  - keep release metadata conservative until acceptance passes.
- `desktop/src/renderer/App.tsx`
  - no major UI change required unless adding QA/degraded notices.
- `tests/test_advisor.py`
  - add route and native synthesis tests.
- `tests/test_api.py`
  - add `/chat` session continuity and restart tests for mixed deterministic/native
    turns.
- `tools/p11_session_kv_e2e_smoke.py`
  - extend or add a P12 smoke for the concrete user path.

## Acceptance Tests

### Unit

1. Router:
   - `怎么反制圣羽翼王` resolves as counterplay/species grounded synthesis.
   - `什么意思` after a grounded species answer resolves to previous subject.
   - `配合恶魔狼主c` after a grounded `黑猫巫师` turn resolves as a relation/team-core
     query involving both species, not as a single-subject `恶魔狼` query.
   - relation markers such as `配合`, `搭配`, `围绕`, `辅助`, `主C`, `首发` update
     active focus instead of discarding the prior anchor.
   - `什么意思` with no prior grounded turn asks a concise clarifying question.
   - ordinary user questions are classified into internal Agent plans, not into
     user-visible bypass modes.
   - only allowlisted controls (`POST /session/clear`, desktop clear action,
     exact `/clear`, release/metadata/status endpoints) may return
     `static_control_response`.
   - bounded loop stops after the configured maximum and returns clarification or
     degraded response instead of unbounded tool calls.

2. State:
   - grounded deterministic/tool turns write `recent_turn_summaries`.
   - turn summaries store redacted excerpts/digests, not raw user messages.
   - mentioned/resolved species write bounded `conversation_topic_pool.species`.
   - relation turns write bounded `conversation_topic_pool.relations`.
   - team-setting entries can seed the topic pool without requiring the user to
     complete a team before chatting.
   - topic-pool species use `source_records`, and removing a team slot removes
     only the `team_setting` source while preserving user/tool/focus evidence.
   - `ConversationActiveFocus` writes concrete focus fields and follows
     single-species, relation, follow-up, ambiguity, and clear/reset transitions.
   - invalid team attachments create diagnostics without partial topic-pool
     mutation; unrelated ordinary chat still succeeds.
   - explicit team-analysis intent with invalid team attachment returns a concise
     fix-team-settings response.
   - turn summaries exclude provider keys and raw request headers.
   - state JSON round-trips through SQLite.
   - P11 state migrates to P12 defaults without losing safe fields.
   - bad state JSON or incompatible native history emits controlled diagnostics.
   - per-turn staged state commits atomically or fails with no split-brain state.
   - commit failure after answer generation returns the answer with
     `continuity_persisted=false` and does not update active continuity.
   - clear/reset preserves frontend/app team settings but clears backend
     `current_team`, topic-pool `team_setting` sources, active focus, summaries,
     native history, and visible messages.
   - `AgentExecutionTrace` excludes provider keys, raw request headers, and hidden
     chain-of-thought.
   - trace retention respects configured local-only TTL/count caps.

3. Native:
   - with `TestModel`, `怎么反制圣羽翼王` produces
     `runtime_path=native_llm_terminal`.
   - required species tools are called before final answer.
   - final answer includes grounded facts and counterplay synthesis.
   - final answer is natural Agent copy, not route/rule/tool payload output.
   - uncertainty-copy checks allow negated/caveated phrases such as
     `不能断言这是成熟核心` but reject affirmative unsupported certainty claims.
   - no unsupported MVP fallback appears.
   - invalid or incomplete packet triggers retrieve-more or clarification before
     terminal synthesis.
   - invalid subject, failed required tool call, unsupported claim, and ambiguous
     missing evidence fail packet validation.
   - failed answer-shape grading repairs or safely degrades within the bounded
     loop.
   - fallback answers only from valid packets or verified local facts; otherwise
     asks clarification.

### API

Run this sequence through `/chat` with native headers:

```text
你好
怎么反制圣羽翼王
什么意思
```

Expected:

- all three requests return the same authoritative active `session_id`;
- second response is LLM terminal synthesis over tool grounding;
- second response asserts `runtime_path=native_llm_terminal` when native runtime
  is available;
- third response references/explains the previous 圣羽翼王 answer;
- no response leaks provider keys;
- no response says `当前 MVP 只支持...` for this supported flow.

Run this relation sequence through `/chat` with native headers:

```text
为什么黑猫经常用来首发
黑猫巫师
配合恶魔狼主c
```

Expected:

- all three requests return the same authoritative active `session_id`;
- final response has `runtime_path=native_llm_terminal` when native runtime is
  configured and available;
- topic pool contains stable entries for both 黑猫巫师 and 恶魔狼, including
  `canonical_species_id` when both resolve from SQLite;
- topic pool contains a relation/team-core edge preserving 黑猫巫师 as the prior
  anchor and 恶魔狼 as the related 主C target;
- final answer discusses how 黑猫巫师 relates to or supports 恶魔狼主C, not only
  what 恶魔狼 does;
- no response leaks raw route names, tool JSON, backend labels, or provider
  secrets in normal user copy.
- final answer includes a natural team-context hint only when final claims use
  validated team-setting evidence or active focus seeded from team context.

Run invalid team attachment cases through `/chat`:

```text
你好
我这队怎么围绕它打
```

Expected:

- unrelated ordinary chat with invalid `team_context` succeeds using non-team
  context, includes diagnostic metadata, and does not mutate topic pool;
- explicit team-analysis intent with invalid `team_context` returns a concise
  fix-team-settings response;
- no partial team species or relation entries are written.

### Restart

1. Send `怎么反制圣羽翼王` with native headers.
2. Stop backend.
3. Restart backend against the same session DB.
4. Send `什么意思` with the same or stale desktop `session_id`.

Expected:

- backend reconciles to the active session;
- recent turn summary survives restart;
- answer explains the previous 圣羽翼王 analysis;
- if native protocol history is incompatible, the compact turn summary still
  supports a useful grounded follow-up.
- topic pool survives restart and can answer relation follow-ups such as
  `配合恶魔狼主c` after the prior `黑猫巫师` context.
- stale session ids reconcile to the authoritative active session without
  resurrecting cleared state.

### Desktop Smoke

In Electron desktop:

1. Configure provider base URL, model, and key.
2. Ask `你好`.
3. Ask `怎么反制圣羽翼王`.
4. Verify a model-like wait occurs or QA metadata confirms `native_llm_terminal`.
5. Ask `什么意思`.

Expected:

- second answer is not immediate deterministic terminal output;
- third answer uses previous context;
- visible chat remains one session;
- clear-chat still archives/resets only the active session.

## Release Gate

V1 cannot be described as having `active-session continuity` until this passes.

Post-fix release wording may use consumer phrasing such as `记住当前对话上下文`
or `当前对话连续性`, but must not imply cross-session long-term memory. P12
continuity does not equal persona memory, global long-term memory, or V2 memory.

Allowed pre-fix wording:

- `SQLite active session persistence is partially implemented.`
- `Native Agent and deterministic grounding continuity is not closed.`

Forbidden pre-fix wording:

- `Agent memory is ready.`
- `RoCoach remembers you across chats.`
- `Grounded battle questions are all LLM Agent replies.`
- `V1 external Alpha is ready for ordinary users.`

## Completion Definition

P12 is complete when:

- every normal user question enters the Agent boundary;
- grounded battle questions use deterministic tools for facts and LLM synthesis
  for the final answer;
- deterministic/tool turns and native turns share one KV continuity model;
- short follow-ups resolve against recent grounded context;
- multi-species relation follow-ups resolve through a bounded conversation topic
  pool rather than a single current-species slot;
- backend restart does not break the above;
- tests and smoke checks prove the sequence:
  `你好 -> 怎么反制圣羽翼王 -> 什么意思`;
- tests and smoke checks prove the sequence:
  `为什么黑猫经常用来首发 -> 黑猫巫师 -> 配合恶魔狼主c`.
