# Roco V1 Alpha Handoff - 2026-05-03

This document is for a zero-context successor Agent. It records the current
execution phase, release target, architectural boundaries, canonical files,
blocked/deferred work, and the shortest safe path to continue.

## 1. Current Phase

Roco is moving from feature/research work into **V1 Alpha release closure**.

The near-term goal is no longer to improve the tactical intelligence layer as
far as possible. The near-term goal is to ship a usable, honest Alpha with:

- one mobile Agent chat surface;
- a Python/FastAPI Product API backend;
- user-configurable OpenAI-compatible provider settings;
- structured battle-data grounding;
- team-context attachment;
- persona-safe, user-facing answers;
- no visible debug/tool/internal metadata in normal chat.

The current best release framing is:

> Self-hosted / developer Alpha, not App Store public release.

Reason:

- The mobile app is a React Native / Expo client.
- The Product API backend is Python/FastAPI with SQLite and Agent runtime.
- The backend is not embedded in the mobile app.
- Without a hosted HTTPS backend, a standalone APK/iOS app is not enough for
  ordinary users.

## 2. Immediate Decision State

### Accepted for V1 release claim

Roco V1 should claim only **A/B/C-layer grounded Agent chat**:

- **A layer**: structured battle data, species/move/stat/fact lookup, team
  context.
- **B layer**: curated wiki/mechanic/context knowledge used conservatively.
- **C layer**: governance, persona, call policy, output boundary, provider
  safety, runtime failure handling.

### Not accepted as V1 release claim

**D layer** expert demonstrations / P10h casebank are not release-blocking and
must not be marketed as V1 capability.

Reason:

- P10h showed `L3-exact` helps, but this may be same-source leakage.
- `L3-transfer` did not reliably outperform L2 in the existing diagnostics.
- Full-roster answer keys are currently under repair and blocked by TODO.

D-layer files may remain in the repo as research artifacts, but runtime should
not depend on them for V1 release readiness.

## 3. Product Boundary

V1 is a **single Agent chat product**.

Allowed:

- chat stream;
- prompt input;
- right-side settings drawer;
- provider/model/API settings;
- optional team-context builder under settings;
- persona selector / `You know who` default;
- hidden structured context sent to backend.

Forbidden in V1 primary UI:

- Team tab;
- Dex tab;
- calculator tab;
- evidence/debug panels;
- visible analysis cards;
- tool traces;
- backend/runtime/provider labels in normal answers;
- local/cloud transport language as ordinary user-facing copy.

Canonical UI/product references:

- `specs/v1_single_chat_app_shell_interaction_brief.md`
- `specs/roco_v1_chat_ui_direction_brief.md`
- `specs/roco_v1_ui_prototype_handoff_2026-04-26.md`
- `mobile/README.md`

## 4. Distribution Reality

### Current architecture

```text
Mobile Expo/RN app
  -> Product API URL
Python/FastAPI backend
  -> A/B/C runtime + SQLite + Agent
OpenAI-compatible provider
```

The backend is external to the phone.

### What this means

For external users there are three possible distribution modes:

1. **Developer Alpha / self-hosted**
   - User clones repo.
   - User runs backend locally or on their server.
   - Mobile client connects to that backend.
   - This is realistic in the current 2-day window.

2. **Hosted backend Alpha**
   - Project owner deploys backend on a VPS/cloud server.
   - Mobile app defaults to HTTPS Product API.
   - User still enters their own provider API key.
   - Backend must not store provider keys unless a separate key-custody design
     is accepted.
   - This is the shortest path to ordinary-user testing, but requires a server,
     domain/HTTPS, deployment hardening, rate limits, and privacy copy.

3. **Standalone mobile APK**
   - Backend/runtime is embedded or rewritten on-device.
   - Current repo is not built this way.
   - Not realistic for this V1 closure window.

### Android APK

APK can be a useful stretch target, but it is only a client unless a backend is
also available.

If Android work resumes, inspect:

- `mobile/package.json`
- `mobile/app.json`
- `mobile/README.md`
- `mobile/src/runtime/runtimeSettings.ts`

Known Android issue:

- Android emulator should use `http://10.0.2.2:8000` for a backend running on
  the host machine.
- The current provider-key safety policy only allows HTTPS or loopback HTTP.
  If using `10.0.2.2`, decide whether to treat it as Android-emulator loopback
  for development only. Do not allow arbitrary LAN HTTP to carry provider keys.

## 5. Canonical Read Order For Successor Agent

Read in this order. Do not start by reading old P10h experiments.

1. This file.
2. `specs/p10_v1_release_integration_plan.yaml`
3. `specs/p10b_chat_contract_integration_audit.yaml`
4. `specs/p10c_release_smoke_qa.yaml`
5. `specs/p10d_simulator_and_optional_live_smoke.yaml`
6. `specs/p10e_runtime_config_ux_repair_and_simulator_live_smoke.yaml`
7. `specs/p10f_chat_reply_simplification.yaml`
8. `specs/p10g_user_facing_answer_boundary.yaml`
9. `mobile/README.md`
10. `README.md`
11. `log/project_log.md` tail section only, unless exact history is needed.

For runtime implementation context:

- `api/main.py`
- `api/services/advisor_service.py`
- `advisor/runtime.py`
- `agent_core/orchestrator.py`
- `agent_core/synthesis.py`
- `agent_core/persona.py`
- `agent_core/presentation.py`
- `mobile/App.tsx`
- `mobile/src/screens/ChatScreen.tsx`
- `mobile/src/runtime/runtimeSettings.ts`
- `mobile/src/api/client.ts`
- `mobile/src/roco/rocoPresentation.ts`
- `mobile/src/roco/teamContext.ts`

For tests:

- `tests/test_api.py`
- `tests/test_advisor.py`
- `tests/test_agent_core_orchestrator.py`
- `tests/test_public_hardening.py`
- `tests/test_p10h_prebattle_ablation_harness.py` only if touching P10h.

## 6. Current P7-P10 State

### P7 Real Agent Chat

Status: implemented and previously live-provider-smoked.

Canonical files:

- `specs/p7_real_agent_chat_contract.yaml`
- `specs/p7_real_agent_chat_core.md`
- `artifacts/p7b/`

Important boundary:

- Default behavior should be Agent chat.
- Deterministic router is compatibility/hint/fallback, not the product default.

### P8 Team Builder Structured Context

Status: implemented.

Canonical files:

- `specs/p8_team_builder_structured_context_mvp.md`
- `specs/p8_team_builder_structured_context_contract.yaml`
- `mobile/ROCO_P8_TEAM_BUILDER_UI_HANDOFF.md`

Important boundary:

- Team context is silently attached to chat.
- The main chat screen should not display a visible active-team chip in V1.
- Team Builder is under settings, not a standalone product route.

### P9 Runtime / Model Policy

Status: closed enough for V1 custom single-model Alpha.

Canonical files:

- `specs/p9c_agent_call_policy_contract.yaml`
- `specs/p9c_agent_loop_policy_contract.yaml`
- `specs/p9d_foundational_infrastructure_audit.md`
- `specs/p9e_runtime_policy_closure_contract.yaml`
- `specs/p9e_deepseek_v4_reference_profile.yaml`

Important boundary:

- V1 should support custom single-model configuration.
- DeepSeek reference profile is evidence/recommendation, not a complex UI
  preset matrix.
- Do not expose per-call model routing to ordinary V1 users.

### P10 Release Integration

Status: mostly integrated; needs fresh release closure.

Evidence:

- `specs/p10d_simulator_and_optional_live_smoke.yaml`
- `specs/p10e_runtime_config_ux_repair_and_simulator_live_smoke.yaml`
- `specs/p10f_chat_reply_simplification.yaml`
- `specs/p10g_user_facing_answer_boundary.yaml`
- `artifacts/p10d_simulator_and_live_smoke/`
- `artifacts/p10e_runtime_config_ux_repair/`

Remaining release risks:

- Need fresh post-P10G iOS live smoke.
- Android smoke is open.
- Slow-call/loading UX may still be weak.
- Hosted backend / distribution mode is undecided.
- README/release notes need to match the actual distribution mode.

## 7. P10h / D-Layer Current State

P10h is now post-V1 enhancement work.

Canonical status files:

- `artifacts/p10h_prebattle_ablation_experiment_plan_2026_05_01.md`
- `specs/p10h_prebattle_ablation_experiment_plan.md`
- `artifacts/p10h_prebattle_ablation/STALENESS_AUDIT_2026_05_03.md`
- `artifacts/p10h_prebattle_ablation/inputs/*.yaml`
- `artifacts/p10h_intuition_demo_pack/`

Important current facts:

- Previous 45-call and R1 experiments are historical partial-roster diagnostics.
- They must not be cited as full-roster performance evidence.
- Active full-roster inputs contain `roster_revision_warning: TODO`.
- Normal P10h build should block until answer keys are repaired.
- Case label mapping is:
  - Case A: `prebattle_wingking_poison_vs_snake_balance`
  - Case B: `prebattle_poison_vs_starfall`
  - Case C: `prebattle_thunder_wingking_fast_balance`
- Do not refer to cases by bare `1/2/3`.

Recent P10h corrections:

- Case C old `落陨星兔` what-if was moved to `orphaned_fragments`.
- Case B question subject corrected from opponent-side to our-side balance
  poison.
- Dragon-Breath Pal resource wording corrected: Pal-caused KOs add 1 extra
  magic loss, making relevant faint cost 2; Pal's own faint also costs 2.
- Thunder/Wing King mechanism corrected:
  - move is `双联脉冲`, not `双人脉冲`;
  - `双联脉冲`: 造成魔伤，迸发：本技能使用次数+1;
  - `雷暴`: 造成魔伤，迸发：本技能获得所有生效过的迸发，每获得1种，本技能能耗+1，威力+10;
  - 闪电鳗鱼 lead value is 泡沫幻影 scouting/rotation, 双联脉冲 laying a
    reusable burst for later 雷暴, and potential pressure into common leads such
    as 圆号鱼.

Do not resume P10h unless the release closure is paused or complete.

## 8. Proposed Next Slice: P11 V1 Alpha Release Closure

Create or execute a bounded P11 release-closure slice. Suggested scope:

### P11a Release readiness audit

Check:

- backend `/metadata`, health, `/chat`, model diagnostic;
- mobile settings persistence;
- persona selector sends `you_know_who`;
- team context silently attaches to chat;
- no analysis cards;
- no visible internal metadata in normal chat.

### P11b Slow-call loading UX minimum

V1 must not look frozen during provider calls.

Minimum acceptable behavior:

- sending state visible;
- disabled send button while request is in flight;
- useful retry/failure text;
- no infinite spinner without a way out.

Do not build a full streaming system unless already cheap.

### P11c Fresh iOS live smoke after P10G

Required scenarios:

- Product API diagnostic ok.
- Model diagnostic ok with request-scoped provider config.
- Normal chat returns non-runtime-failure assistant response.
- Missing/invalid provider key gives actionable setup guidance.
- Team context path does not render a visible team chip but reaches backend.
- No provider key appears in terminal/artifacts/screenshots.

### P11d ABC coach smoke cases

Small, not research-scale. 5-8 cases proving release claim:

- A-layer species/move fact lookup works.
- B-layer mechanic/context explanation can be used conservatively.
- C-layer output boundary prevents internal labels and overclaim.
- Persona answer remains user-facing.

Do not use P10h D-layer claims in this smoke.

### P11e Release docs

Update or create:

- root `README.md` quickstart;
- `mobile/README.md` install/run;
- `.env.example`;
- `docs/RELEASE_NOTES_V1_ALPHA.md`;
- `docs/KNOWN_LIMITATIONS_V1_ALPHA.md`;
- privacy/security note for provider API keys.

Must explicitly state the selected distribution mode:

- self-hosted developer Alpha; or
- hosted backend Alpha; or
- Android APK client with required backend.

## 9. Recommended Two-Day Plan

### Day 1

- Stop P10h runtime-affecting work.
- Run release readiness audit.
- Patch loading/failure UX if needed.
- Run backend unittest and mobile typecheck.
- Draft release docs and known limitations.

### Day 2

- Run fresh iOS simulator live smoke.
- Run ABC smoke cases.
- If time permits, run Android emulator smoke.
- If EAS/build environment is ready, generate Android preview APK as a stretch.
- Produce final release verdict:
  - ready as self-hosted developer Alpha;
  - ready with accepted residuals;
  - blocked with exact blockers.

## 10. Validation Commands

Use repo-standard tests. Do not assume pytest.

Backend:

```bash
.venv/bin/python -m unittest discover -s tests
```

Targeted backend/API:

```bash
.venv/bin/python -m unittest tests.test_api tests.test_advisor tests.test_agent_core_orchestrator tests.test_public_hardening
```

Mobile:

```bash
cd mobile && npm run typecheck
```

Expo iOS:

```bash
cd mobile && npm run ios
```

Expo Android emulator:

```bash
cd mobile && npm run android
```

Backend local:

```bash
./scripts/run_local_api.sh
```

## 11. Security Boundaries

Never print or store provider API keys in artifacts.

Provider key transport:

- HTTPS Product API: allowed.
- loopback HTTP local development: allowed.
- arbitrary LAN HTTP: not allowed for provider key transport.

If Android emulator needs host-backend access via `10.0.2.2`, treat this as a
development-only exception only after explicit implementation and documentation.
Do not generalize to all private LAN IPs.

For hosted backend:

- use HTTPS;
- do not store user provider keys by default;
- use request-scoped provider key handling;
- add rate limiting if project-owned provider keys are ever used;
- document unofficial status and no affiliation with game/IP owner.

## 12. What Not To Do Next

Do not:

- continue P10h experiments as a release blocker;
- add desktop UI;
- promise App Store availability;
- promise standalone APK without backend;
- expose D-layer high-player reasoning as release-ready;
- reintroduce analysis cards;
- show raw tool traces / confidence / evidence ids in user chat;
- weaken provider-key HTTPS policy for convenience.

## 13. Open Decisions For PM

The next Agent should surface these decisions, but not block all engineering on
them:

1. Is V1 Alpha distributed as self-hosted developer Alpha only?
2. Should we deploy a temporary hosted HTTPS backend for non-developer testing?
3. Should Android APK be a stretch deliverable for this release?
4. Is Android QA required before public GitHub release, or accepted residual?
5. Should D-layer docs remain in repo release branch as experimental artifacts,
   or be clearly tucked under `artifacts/` only?

## 14. Current Best Recommendation

Ship V1 as:

> Roco V1 Alpha: self-hosted ABC-grounded battle coach Agent.

Do not claim:

> high-player tactical intuition;
> D-layer expert demonstration reasoning;
> App Store readiness;
> standalone mobile operation.

This is the honest, shippable boundary.
