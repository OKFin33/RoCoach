# Source Note: Mainstream PvP Archetype Deck

```yaml
source_id: deck_2026_03_26_mainstream_pvp_archetypes
title: "公测 PVP 阵容推荐 / PvP 主流阵容全回顾"
source_type: slide_deck_with_word_extraction
published_at: 2026-03-26
published_at_basis: "inferred_from_cache_folder_name"
collected_at: 2026-04-20
creator_or_channel: "灰鼠的蓝灯 / Plus"
primary_input: "wiki/cache/主流阵容0326/帮我整理出每一页的所有文本，对应页码和内容.docx"
pdf_reference: "wiki/cache/主流阵容0326/PvP主流阵容全回顾.pdf"
pdf_pages: 44
word_table_rows: 45
can_commit: summary_only
sensitivity: public_summary
source_class:
  - archetype_snapshot
  - team_casebank_seed
  - historical_meta_observation
confidence: provisional
volatility: shifting
a_layer_required: true
persona_risk: false
cross_game_risk: low
status: cleaned_md_created
```

## Intake Decision

This file is the cleaned Markdown intake artifact for the `主流阵容0326` cache
group.

Use this Markdown note as the source-controlled intake surface. Do not commit
the raw PDF deck or full Word extraction by default.

The Word extraction was used as the primary text input because it contains a
page-indexed table. The PDF was used as a structure check: it has `44` pages
and the extracted page order matches the deck structure.

## Source Scope

The deck reviews seven teams:

1. 雷暴队
2. 鹿核队
3. 毒队
4. 星陨队
5. 武队
6. 虫队
7. 幽灵队

The deck mixes:

- internal-test history
- public-release prediction
- archetype explanation
- team-loop teaching
- difficulty and strength evaluation

Therefore, it is useful for B-layer archetype and casebank design, but not as
current-meta truth.

## Handling Rules

Allowed:

- use as an archetype map
- use as a casebank seed
- extract generic team-loop doctrine
- compare with later sources to detect stable archetype logic
- use page references for traceability

Forbidden:

- treating deck ratings as current strength truth
- copying complete slide text into doctrine pages
- using exact species, move, or trait claims without A-layer validation
- using beta-version performance as public-release fact

## Page Structure Map

```text
01        cover
02        deck purpose and seven-team list
03-07     雷暴队
08-12     鹿核队
13-17     毒队
18-23     星陨队
24-28     武队
29-35     虫队
36-42     幽灵队
43        summary
44        closing
```

## Archetype Summaries

### 雷暴队

```yaml
pages: [3, 4, 5, 6, 7]
keywords:
  - 迸发
  - 雷暴
  - 高速压制
  - 爆发斩杀
confidence: provisional
volatility: shifting
```

Core loop:

- use entry-triggered `迸发` effects and setup actions to prepare a high-impact
  `雷暴` burst
- bring the final attacker in after enough enabling effects are ready
- convert speed and burst into immediate KO pressure

Doctrine value:

- teaches "burst archetype as accumulated condition conversion"
- useful for explaining why an explosive team may still depend on staging,
  entry timing, and resource preparation

Risks:

- deck explicitly discusses beta-to-public changes
- exact move cost, trigger stacking, and strength claims require A-layer
  validation

Possible B Wiki targets:

```text
wiki/pages/archetypes/burst_condition_conversion.md
wiki/pages/casebank/teamcase_thunderburst.md
```

### 鹿核队

```yaml
pages: [8, 9, 10, 11, 12]
keywords:
  - 首领化
  - 上场强化
  - 核心养成
  - 安全入场
confidence: provisional
volatility: shifting
```

Core loop:

- build around one scaling core
- create repeated safe entry windows
- accumulate permanent or long-horizon advantages
- avoid overcommitting all resources to a weakened solo carry

Doctrine value:

- clear example of "core-first construction"
- shows why a carry archetype needs support, entry routing, resource protection,
  and fallback pressure

Risks:

- deck says the main core was heavily nerfed across tests
- public-release strength is only a forecast

Possible B Wiki targets:

```text
wiki/pages/team_building/core_first_construction.md
wiki/pages/archetypes/scaling_core_teams.md
```

### 毒队

```yaml
pages: [13, 14, 15, 16, 17]
keywords:
  - 中毒
  - 中毒印记
  - 印记保护
  - 长盘运营
confidence: provisional
volatility: shifting
```

Core loop:

- establish poison or poison-mark pressure
- convert accumulated poison state into later benefits through dedicated
  species, traits, or moves
- rely on durability and long-game operation rather than immediate burst
- protect mark progress and restart after cleanse

Doctrine value:

- teaches "damage-over-time as pressure conversion"
- useful for explaining that slow archetypes still need a visible conversion
  path from attrition to win condition

Risks:

- exact poison and poison-mark effects belong to A-layer
- public-release inheritance of beta mechanics is uncertain

Possible B Wiki targets:

```text
wiki/pages/mechanics/marks_and_persistence.md
wiki/pages/archetypes/attrition_mark_teams.md
```

### 星陨队

```yaml
pages: [18, 19, 20, 21, 22, 23]
keywords:
  - 星陨印记
  - 印记爆发
  - 叠层
  - 迅捷收割
confidence: provisional
volatility: shifting
```

Core loop:

- apply and increase star-fall mark layers
- use a dedicated converter to turn mark layers into burst damage
- preserve alternative conversion routes when the main converter cannot enter
  safely
- pressure opponents because clearing or ignoring marks can both carry risk

Doctrine value:

- teaches "mark as stored threat"
- useful for distinguishing mark accumulation from direct damage and for
  explaining why conversion timing matters

Risks:

- exact mark trigger, partial consumption, and converter effects require
  A-layer validation
- public-release nerfs may change reliability

Possible B Wiki targets:

```text
wiki/pages/archetypes/stored_mark_burst.md
wiki/pages/casebank/teamcase_starfall.md
```

### 武队

```yaml
pages: [24, 25, 26, 27, 28]
keywords:
  - 应对
  - 打断
  - 叠加强化
  - 正面对抗
confidence: provisional
volatility: shifting
```

Core loop:

- repeatedly use high-value response moves to interrupt or punish opponent
  startup
- force the game into direct exchange patterns
- accumulate background progress toward a terminal carry while fighting
- use defensive response moves to threaten the opponent's own pressure turns

Doctrine value:

- strong example of "interaction-first pressure"
- helps separate blind offense from response-driven tempo control

Risks:

- exact response move effects, interruption behavior, and carry stacking rules
  require validation
- deck notes public-release nerfs to stats and move distribution

Possible B Wiki targets:

```text
wiki/pages/mechanics/response_counterplay.md
wiki/pages/archetypes/interaction_pressure_teams.md
```

### 虫队

```yaml
pages: [29, 30, 31, 32, 33, 34, 35]
keywords:
  - 奉献
  - 虫群
  - 共享强化
  - 苦尽甘来
confidence: provisional
volatility: shifting
```

Core loop:

- accumulate shared contribution effects through selected traits and moves
- stack several categories of enhancement onto specific payoff moves
- delay the decisive payoff until enough layers exist
- rely partly on opponent unfamiliarity if the archetype is underplayed

Doctrine value:

- teaches "shared team resource as delayed payoff"
- useful for casebank patterns where the visible field state does not explain
  all future threat

Risks:

- exact contribution categories and limits are A-layer facts
- deck itself warns that information-gap value drops once opponents understand
  the structure

Possible B Wiki targets:

```text
wiki/pages/archetypes/shared_resource_payoff.md
wiki/pages/casebank/teamcase_bug_contribution.md
```

### 幽灵队

```yaml
pages: [36, 37, 38, 39, 40, 41, 42]
keywords:
  - 能量控制
  - 控能
  - 后排强化
  - 限制转收益
confidence: provisional
volatility: shifting
```

Core loop:

- reduce opponent energy through traits and moves
- force the opponent into awkward low-energy decisions
- convert energy denial into tempo, health, or KO pressure
- use opponent forced actions such as 聚能 or switching as tactical openings

Doctrine value:

- very strong B-layer case for "control is not a win condition until converted"
- useful for resource-tempo doctrine and recommendation taste

Risks:

- deck discusses multiple nerfs from test versions
- exact zero-energy punishment and energy-loss rules require validation

Possible B Wiki targets:

```text
wiki/pages/team_building/resource_tempo.md
wiki/pages/archetypes/resource_denial_teams.md
```

## Cross-Archetype Doctrine Candidates

### Candidate 1: Every archetype needs a conversion path

The deck repeatedly frames team identity as a path from setup condition to
visible advantage:

- 雷暴: triggered setup -> burst
- 鹿核: safe entries -> scaling carry
- 毒队: poison state -> attrition win
- 星陨: mark layers -> burst conversion
- 武队: response wins -> tempo and terminal scaling
- 虫队: contribution layers -> payoff move
- 幽灵: energy denial -> tempo or KO

Target:

```text
wiki/pages/team_building/conversion_path.md
```

Confidence: `provisional`

### Candidate 2: Archetype strength is context-bound

The deck constantly qualifies team strength through:

- test-version history
- public-release changes
- nerfs
- pilot difficulty
- opponent familiarity
- resource-management burden

Target:

```text
wiki/pages/archetypes/archetype_labels_are_hypotheses.md
```

Confidence: `provisional`

### Candidate 3: Resource control must be converted

The幽灵队 section makes the cleanest claim: limiting opponent energy is not
the final objective. The team must convert that hidden advantage into tempo,
health, or kills.

Target:

```text
wiki/pages/team_building/resource_tempo.md
```

Confidence: `provisional`

### Candidate 4: Information-gap teams decay as the field learns them

The虫队 discussion explicitly frames unfamiliarity as part of practical
success. Once the opponent understands key timing and failure points, the same
team can lose a large part of its edge.

Target:

```text
wiki/pages/recommendation_taste/information_gap_warning.md
wiki/pages/counterexamples/ranking_without_failure_modes.md
```

Confidence: `provisional`

## A-Layer Cross-Check Needed

Before casebank promotion, validate:

- exact names and IDs of all listed species
- move names and move effects
- trait effects
- mark effects and layer behavior
- energy costs and trigger rules
- public-release changes versus beta/test claims
- whether named team members exist in current battle-dex

## Recommended Wiki Actions

Immediate:

- use this note as the only committed summary for the `主流阵容0326` deck
- keep raw PDF/DOCX in local cache only
- do not promote deck strength ratings to doctrine

Next:

- create `wiki/pages/archetypes/archetype_labels_are_hypotheses.md`
- create `wiki/pages/team_building/conversion_path.md`
- create low-confidence casebank drafts only after A-layer name/effect checks

## Raw Asset Retirement Policy

After Git boundary repair:

- add `wiki/cache/` to `.gitignore` unless the PM explicitly wants to version
  sanitized cache inputs
- keep this Markdown note as the durable intake artifact
- delete or archive raw PDF/DOCX locally only after confirming no further visual
  or text extraction is needed
