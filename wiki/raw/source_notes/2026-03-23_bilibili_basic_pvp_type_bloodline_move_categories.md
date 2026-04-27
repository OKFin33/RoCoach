# Source Note: Bilibili Basic PvP Tutorial - Type, Bloodline, Move Categories

```yaml
source_id: bilibili_2026_03_23_basic_pvp_type_bloodline_move_categories
title: "洛克王国世界全网最详细喂奶级PVP攻略系列！对战基础篇第一期（属性、血脉、技能类型）"
creator_or_channel: "Local龙星 / 圣龙骑士出品"
source_type: video_transcript
published_at: 2026-03-23
collected_at: 2026-04-20
local_transcript_path: "wiki/cache/属性、血脉、技能类型0324/NoteGPT_洛克王国世界全网最详细喂奶级PVP攻略系列！对战基础篇第一期（属性、血脉、技能类型）——圣龙骑士出品.txt"
can_commit: summary_only
sensitivity: public_summary
source_class:
  - mechanics_tutorial
  - beginner_pvp_tutorial
  - type_bloodline_move_boundary
confidence: provisional
volatility:
  mechanics_core: shifting
  examples: ephemeral
a_layer_required: true
persona_risk: false
cross_game_risk: medium
status: intake_complete
```

## Intake Decision

This source is a narrow beginner PvP tutorial focused on:

- attribute/type basics
- bloodline basics
- resonance magic examples
- move category basics
- response/counterplay triangle

Use it as a corroborating source for core mechanics terminology and doctrine
candidates. Do not use it as exact fact authority.

## Transcript Quality Note

The transcript has a useful main section from roughly `00:02` to `06:45`, then
degrades into low-value or corrupted outro-like text. Only the coherent main
section is used for claim extraction.

## Main Extracted Claims

### Type Claims

- The game has `18` attributes/types.
- Each type has different offensive and defensive relations.
- A species' defensive matchup should be understood through its own type
  profile.
- Bad positioning occurs when a species stays into an unfavorable type matchup.
- Defensive switching / coverage thinking is introduced through the example of
  avoiding a Fire species into Water or Ground pressure.

Review state:

- Broad concept aligns with existing project primer.
- Exact type-chart details must remain A-layer facts.

### Bloodline Claims

- Bloodline is described as separate from the species' own type.
- A species with a Poison bloodline is not thereby treated as a Grass/Poison
  defensive species.
- Bloodline can provide access to a unique corresponding bloodline-type move.
- Bloodline can affect resonance magic such as `愿力冲击`.
- When no special case applies, bloodline may default to the species' main type.

Review state:

- Strong B-layer doctrine candidate.
- Exact bloodline acquisition and default rules need A-layer confirmation.

### Resonance Claims

- `愿力强化` is equipped as a resonance magic and used from the battle bag.
- After use, the first move slot is replaced by `愿力冲击`.
- `愿力冲击` is described as having a strong response-to-status effect with
  `+150%` damage on successful response.
- `首领化` is described as another currently open resonance option.
- Future bloodline magic is mentioned speculatively and must not be treated as
  implemented fact.

Review state:

- Useful for glossary and mechanics context.
- Exact usage limits and values require A-layer or direct game validation.

### Move Category / Response Claims

- Moves are divided into three categories: attack, defense, and status.
- The categories create a response triangle:
  - attack responds to status
  - status responds to defense
  - defense responds to attack
- This is described as a guessing game layer.
- `聚能` is described as a status-category action.
- Attack example `闪燃` is described as receiving a large power multiplier when
  successfully responding to status.
- Defense moves are described as sharing damage reduction as a common feature.
- Status moves that can respond to defense are described as currently rarer but
  high-impact.

Review state:

- Strong B-layer doctrine candidate.
- Do not globalize example-specific multipliers.

## Doctrine Candidates

### Candidate 1: Separate type, bloodline, and move type

The source reinforces that bloodline is not defensive type identity and should
not be interpreted as changing a species' type profile.

Target:

```text
wiki/pages/mechanics/type_bloodline_move_boundary.md
```

Confidence: `provisional`

### Candidate 2: Response is a move-category guessing layer

The source gives a compact beginner framing for the attack / defense / status
response triangle.

Target:

```text
wiki/pages/mechanics/response_counterplay.md
```

Confidence: `provisional`

### Candidate 3: Resonance examples belong to mechanics context, not type truth

The source uses `愿力冲击` and `首领化` as basic examples. These should be
documented as battle-system mechanics with strict A-layer fact references.

Target:

```text
wiki/pages/mechanics/resonance_magic.md
```

Confidence: `provisional`

## A-Layer Cross-Check Needed

Before promotion beyond draft:

- verify current move category labels
- verify `聚能` category and behavior
- verify `愿力冲击` type derivation and response effect
- verify current resonance options and usage limits
- verify whether bloodline defaulting to main type is universal or common-case
- verify exact type chart and defensive type rules through structured data

## Risks

- Early-release source date: 2026-03-23.
- Several transcript errors: `洛皇国`, `陆狂国`, `怨力` likely OCR/ASR noise.
- Creator uses analogy to another game for `首领化` visual comparison; this is
  not mechanic authority and should not enter doctrine.
- Example-specific move effects may be patch-sensitive.

## Current Handling

Action:

- keep as summarized source note
- do not commit full transcript
- use with the 2026-04-02 tutorial as cross-source support for draft mechanics
  pages
