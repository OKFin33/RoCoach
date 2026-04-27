---
title: "Fire Fox Wing King Balance Team Reconciliation"
content_class: "casebank"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-04-22_firefox_wingking_balance_team_share.md"
  - "wiki/pages/team_building/core_team_construction.md"
  - "wiki/pages/roles/role_taxonomy.md"
  - "wiki/pages/mechanics/speed_priority_and_swift.md"
  - "wiki/pages/mechanics/transmission_and_skill_slots.md"
  - "wiki/pages/mechanics/entry_exit_and_replacement_timing.md"
  - "wiki/pages/mechanics/marks_and_persistence.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-22"
reviewed_by: "user_shared_case_reconciliation"
persona_free: true
---

# Fire Fox Wing King Balance Team Reconciliation

## Case

Question family tested in-thread:

```text
给定队伍:
尖嘴狐仙 / 圣羽翼王 / 声波缇塔 / 奇丽花 / 岚鸟 / 寂灭骨龙

先做结构分析，再和高分段玩家分享进行比对。
```

The value of this case is not whether the source's ladder-strength rhetoric is
literally true. The value is that it lets us compare:

- model-first structural inference
- against a current-version high-ladder player decomposition of the same team

## A-Layer Checks

Known exact facts to retrieve before reasoning:

- species identities and aliases:
  - 尖嘴狐仙
  - 圣羽翼王
  - 声波缇塔
  - 奇丽花
  - 岚鸟
  - 寂灭骨龙
- relevant traits:
  - 火狐 `灵魂灼伤`
  - 翼王 `飓风`
  - 岚鸟 `顺风`
  - 骨龙 `不朽`
- relevant move-cluster hooks:
  - 啮合 / transmission-related moves on 缇塔 and 奇丽花
  - `焚烧烙印` on 火狐
  - swift/wing pairing on 岚鸟 + 翼王

## Initial Model Reading

The initial model-side reading in-thread correctly identified:

- the team is not pure offense; it is a balance-oriented structure
- 骨龙 is a resource/pressure slot rather than a simple speed carry
- 火狐 is not best read as the team's main weather starter
- 岚鸟 and 翼王 form a linked wing/swift pairing
- 缇塔 is a midgame damage spike and setup slot

## Source-Guided Corrections

The high-ladder share sharpened several points that the initial model reading
either underweighted or only half-caught.

### 1. 奇丽花 Is Not Merely A Sustain Battery Here

The share treats 奇丽花 as:

- 核心输出位
- 核心啮合手

This is a major correction. In this build, 奇丽花 should not be described only
as a support/economy slot. It is one of the team's real offensive axes.

### 2. The Team Is Better Read As A Template Fusion

The source explicitly frames the team as a fusion of:

- 骨龙平衡队
- 啮合平衡队
- 水刃翼王

So the best interpretation is not "clever goodstuff with some synergies." It is
a mature current-version balance-template fusion.

### 3. 火狐 Is A Core Defensive Pivot, Not Merely A Utility Slot

The source strongly emphasizes:

- pure bulk fire fox
- slower speed is preferred
- defensive soak into `高温回火`
- `焚烧烙印` as critical anti-mark utility

This reinforces the corrected doctrine view that 火狐 is a structural defensive
pivot and anti-mark stabilizer.

### 4. 双啮合轴 Matters

The source assigns both:

- 声波缇塔
- 奇丽花

as core 啮合 pieces. This means the team is not running one setup damage axis
plus five helpers. It is using dual pressure lanes layered onto a balance shell.

## Reconciled Interpretation

A stronger reviewed answer is:

```text
这队是一支成熟的当前版本平衡模板融合队。
骨龙和火狐负责联防、状态处理、反强化、清印记与节奏缓冲；
缇塔和奇丽花形成双啮合输出轴；
岚鸟和翼王构成迅捷/收割轴。
所以它不是单核队，也不是简单强宠拼盘，而是多轴平衡压制队。
```

## What The Model Got Right

- team class: balance-oriented, not pure offense
- 骨龙 as a resource-exchange / pressure slot
- 火狐 not as a weather-first slot
- 翼王 + 岚鸟 as a genuine paired module

## What Needed Correction

- 奇丽花 was initially under-read as too support-heavy
- the team was initially described as too "goodstuff-like" and not enough as a
  mature template fusion
- 火狐's structural importance was initially under-ranked

## Failure Modes

- Reducing 奇丽花 to a sustain battery and missing its role as a real output axis.
- Describing the team as a random pile of strong units.
- Treating 火狐 as a side utility slot rather than a core defensive pivot.
- Explaining 翼王 in isolation and missing the 岚鸟 pairing.
- Ignoring that current-version team labels such as `水刃翼王` can encode a real
  build identity rather than just one move mention.

## Review Status

This case is reviewed as a useful reconciliation sample:

- model structural inference was directionally correct
- source-guided role correction materially improved the answer
- the resulting pattern is suitable for future casebank retrieval when the
  system needs examples of "balance template fusion" rather than single-axis
  archetype reading
