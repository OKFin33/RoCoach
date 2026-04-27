# Source Note: Bilibili Battle System Intro And 18-Type Overview

```yaml
source_id: bilibili_2026_04_02_battle_system_intro_18_types
title: "洛克王国世界：真正的战斗系统入门！18种系别机制简介"
source_type: video_transcript
published_at: 2026-04-02
collected_at: 2026-04-20
origin_platform: bilibili
source_url: "https://b23.tv/Sdcasmr"
local_transcript_path: "/Users/okfin3/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_9axqslh60sls22_faf9/msg/file/2026-04/【洛克王国世界：真正的战斗系统入门！18种系别机制简介-哔哩哔哩】 httpsb23tvSdcasm.docx"
can_commit: summary_only
sensitivity: public_summary
source_class:
  - mechanics_tutorial
  - type_mechanism_overview
confidence: provisional
volatility:
  mechanics_core: shifting
  type_identity_summary: shifting
  early_meta_examples: ephemeral
a_layer_required: true
persona_risk: false
cross_game_risk: low
status: intake_complete
```

## Intake Decision

This source is useful as an early public mechanics tutorial and type-system
overview, but it must not be treated as authoritative truth.

Use it for:

- mechanics claim extraction
- glossary candidate discovery
- doctrine candidate induction
- cross-check targets against A-layer data and PM review

Do not use it for:

- direct exact fact authority
- long-term type balance conclusions
- unverified skill value tables
- current meta recommendations
- copying transcript text into the wiki

## Why `summary_only`

The source is a public video transcript, but the transcript itself is creator
content. Commit only summarized claims, citation metadata, and review notes.
Do not commit the full transcript.

## Main Extracted Claims

### Battle UI And Resource Claims

- Battle UI exposes active species attributes, restraint relation, traits,
  move details, buffs, debuffs, energy, field effects, and battle log details.
- Energy is a shared tactical constraint for both sides; ordinary upper bound is
  described as `10`, with exceptions possible.
- `聚能` is described as a no-energy option that restores `5` energy.
- `聚能` is described as a state-category action that can be countered by
  state-response mechanics.
- Battle logs can be used to infer opponent move cost, damage, type, and
  whether repeat usage is possible next turn.

Review state:

- High doctrine value.
- Exact numbers need A-layer or PM confirmation.

### Resonance / Bag Claims

- `首领化` is described as a once-per-battle resonance action for eligible
  bloodline species, requiring corresponding token ownership.
- `首领化` is described as changing battle form, stats, and sometimes trait
  effect during battle, not permanent evolution.
- `愿力强化` is described as converting the first move that turn into
  `愿力冲击`, with limited uses and cooldown.
- `愿力冲击` is described as bloodline-typed rather than species-type-typed.
- Bag actions are described as not consuming the turn, with PvE-only recovery
  item behavior separated from PvP.

Review state:

- Useful for mechanics glossary.
- Needs direct game or A-layer validation before becoming confirmed doctrine.

### Type / Bloodline Boundary Claims

- Species defensive type is described as fixed by `系别`, not changed by
  `血脉`.
- Bloodline is described as affecting available moves and `愿力冲击` type.
- Type restraint is described as move type against target species type, not
  attacker species type against defender species type.

Review state:

- High-priority doctrine candidate.
- Should be cross-checked against existing domain primer and structured data.

### Switch / Buff Persistence Claims

- Most ordinary buffs and debuffs are described as disappearing after switching.
- Some effects can apply to every switched-in species.
- Some effects are described as permanent after use.
- Marks and some statuses are described as persisting through switch.
- Switching consumes the turn.

Review state:

- Valuable B-layer doctrine candidate.
- Needs careful taxonomy: ordinary buff, debuff, mark, status, permanent
  self-modification, backline/team effect.

### Turn Order Claims

- Turn order is described as priority first, then speed.
- Any priority value is described as overriding speed.
- Affinity/environment speed effects are described as not applying in PvP.

Review state:

- Candidate mechanics page material.
- Exact priority semantics require A-layer or direct rule confirmation.

### Move Category / Counterplay Claims

- Every move is described as one of three categories: attack, defense, status.
- There are corresponding response targets: respond to attack, defense, or
  status.
- Response is described as triggering additional move effects, not necessarily
  interruption or damage nullification.
- Beta-test baseline response effects are described as removed in public
  release.
- Current response value is described as move-specific rather than universal.
- Defense moves responding to attack are described as percentage damage
  reduction plus possible counter-effect.
- Status moves responding to defense are described as strong setup or swing
  tools.
- Attack moves responding to status are described as maximizing damage or
  sometimes interrupting specific status actions.

Review state:

- Very high B-layer value.
- Must not over-generalize exact effects across all moves.

### Mark / Status Claims

- Marks are described as distinct from ordinary buffs/debuffs and persist on
  field through switching.
- Each species is described as able to hold at most one positive mark and one
  negative mark at a time.
- Status examples include `寄生`, `灼烧`, `冻结`, `中毒`.

Review state:

- Strong candidate for mechanics glossary and doctrine page.
- Exact stacking and persistence rules need confirmation.

## Type-Mechanism Summary Claims

These claims are useful as a taxonomy draft, not as final fact authority.

- Normal: broad utility, cost manipulation, forced switch, dispel, mark removal,
  degeneration, multi-hit, burst.
- Grass: sustain, `寄生`, `光合印记`, growth-style damage ramp.
- Fire: burn-based percentage pressure, damage ramp, burn disappears on switch.
- Water: rain weather, water move power increase in rain, `润泽印记`, cost
  reduction.
- Light: cross-type move usage and bonuses based on other equipped or used move
  types.
- Ground: defense, anti-multi-hit, anti-switch, forced switch, sandstorm,
  `蓄势印记`.
- Ice: `冻结` as max-HP pressure, switch-persistent freeze, snow weather,
  enemy cost increase.
- Electric: `迸发` on first action after entry, self-leave/re-entry loops,
  forced leave/return, damage stacking by leave count, `蓄电印记`.
- Poison: poison percentage damage, poison disappearing on switch, poison mark
  persisting and applying to entrants, conversion from poison stacks to poison
  mark.
- Bug: `奉献` as hidden team/backline contribution for Bug allies, including
  multi-hit, cost reduction, poison, power, and lifesteal variants.
- Martial: high reward from successful response, weak baseline if response
  fails.
- Dragon: high raw power balanced by `蓄力`; support tools can bypass or alter
  charge constraints.
- Wing: `迅捷` as active-switch entry trigger; requires energy and triggers only
  one swift move; passive replacement after death does not trigger.
- Cute: `萌化` / degeneration, stat and trait changes, post-beta nerf notes,
  more likely current use as targeted counterplay or buff-transfer support.
- Ghost: energy control, zero-energy burst, `降灵印记`, active-leave wording
  distinction.
- Evil: lifesteal and exchange mechanics, including buff/debuff, health, or
  move exchange.
- Machine: `传动` as skill-position movement, positional support, cost
  reduction, speed/power support, permanent ramp through position changes.
- Illusion: `星陨印记` as detonated mark damage, consumed on detonation, can be
  used either for detonation burst or multi-hit scaling.

## Doctrine Candidates

### Candidate 1: Roco combat is resource-and-response centric

The source frames combat as more than attribute restraint. Energy, move
category, response targeting, and switching create the core tactical layer.

Suggested target:

```text
wiki/pages/mechanics/response_counterplay.md
wiki/pages/team_building/resource_tempo.md
```

Confidence: `provisional`

### Candidate 2: Defensive type and offensive move type must be separated

The source explicitly separates species `系别`, bloodline, and move type.
This is central to avoiding naive "species type beats species type" reasoning.

Suggested target:

```text
wiki/pages/mechanics/type_bloodline_move_boundary.md
wiki/pages/glossary/type_bloodline_move.md
```

Confidence: `provisional`

### Candidate 3: Role comes from mechanism access, not only type identity

The type overview repeatedly describes the same type as a mechanism package:
cost control, sustain, marks, forced switch, entry triggers, charge mechanics,
or exchange effects. This supports B-layer role reasoning based on mechanism
access and team context rather than static type label.

Suggested target:

```text
wiki/pages/roles/contextual_role_assignment.md
wiki/pages/team_building/mechanism_compression.md
```

Confidence: `provisional`

### Candidate 4: Switching is both defensive reset and resource risk

The source describes switching as clearing many ordinary buffs/debuffs while
preserving marks and some status/effects. This makes switch decisions depend on
effect persistence class, not only type matchup.

Suggested target:

```text
wiki/pages/mechanics/switch_persistence.md
wiki/pages/team_building/defensive_structure.md
```

Confidence: `provisional`

### Candidate 5: Early type summaries are volatile

The source was published near initial release and includes references to beta
mechanics and public-release changes. The type identity summaries should be
treated as early map-building, not stable long-term meta doctrine.

Suggested target:

```text
wiki/raw/version_observations/2026-04-02_early_type_identity_snapshot.md
```

Confidence: `low_confidence` for meta strength claims, `provisional` for
mechanism taxonomy claims.

## A-Layer Cross-Check Needed

Before promoting claims to reviewed doctrine, check:

- energy upper bound and exceptions
- `聚能` exact classification and recovery amount
- resonance action usage limits and cooldowns
- move category universe and category labels
- response target semantics
- priority and speed ordering
- mark stacking limits
- switch persistence classes
- each type-specific named mechanism against move/ability data

## Risks

- Early-release volatility: source is from 2026-04-02.
- Transcript quality issues: several OCR/transcription errors in type names and
  terms.
- Exact values may be patch-sensitive.
- Creator explanations may simplify edge cases.
- Type summaries mix mechanics, examples, and current strength impressions.

## Current Handling

Action:

- keep as summarized raw source note
- do not copy full transcript
- use as candidate seed for mechanics and glossary pages
- defer `reviewed` promotion until A-layer and PM review
