---
title: "PvP Stat Normalization And IV Selection"
content_class: "mechanics"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/raw/source_notes/2026-03-25_bilibili_iv_nature_stat_training.md"
  - "wiki/cache/PVP扫盲0419/NoteGPT_一口气让你彻底学会精灵对战！PVP扫盲，新手必看！.txt"
  - "wiki/cache/速度线:词条 0403/NoteGPT_【洛克王国世界】pvp入坑指南硬核知识，全图鉴速度线计算_所有词条解释_配队逻辑.txt"
a_layer_refs:
  - "data/reference/luoke_world_type_database_v2.json"
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-20"
reviewed_by: "systematic_cache_and_a_layer_check"
persona_free: true
---

# PvP Stat Normalization And IV Selection

## Claim

PvP stat reasoning should separate three layers:

- A-layer exact calculation: species base stats, IVs, nature, and formula
- B-layer investment judgment: which stats matter for a role
- team-level taste: whether a threshold actually changes matchup decisions

The advisor must not assume PvP auto-perfects a spirit. Current source material
supports that PvP normalizes level/growth-like surfaces, while IVs still matter.

## Strategic Use

When recommending a set or judging a team, ask:

- What is this member's job: damage, utility, defensive pivot, mark engine,
  weather setter, cleaner, or counterpiece?
- Which attacking side does its actual skill pool use?
- Does speed investment cross a meaningful speed line, or is the member still
  slower than the threats it cares about?
- Is bulk needed on the physical side, magical side, or both?
- Does the plan rely on exact turn order, damage thresholds, or survival
  thresholds?

The common bad recommendation is to select IVs by species base stats alone.
Roco advice should combine role, base stats, trait, and skill pool.

## Evidence

The current A-layer stat source states that PvP six-dimensional stats depend on
species base stat, IV, and nature. It also records the formulas, IV range,
PvP IV multiplier, nature boost/penalty, and same-speed random rule.

The 2026-03-25 IV tutorial explains that IV choice depends on role, base stat,
and skill pool. It uses examples where a defensive-looking species may still
want an attacking IV because its relevant counter-skill uses that attacking
side.

The 2026-04-19 beginner sweep explicitly states that PvP does not fill missing
IVs, while level/star-like surfaces are automatically normalized.

## Confidence

`provisional`.

High confidence:

- PvP stat formula depends on base stat, IV, and nature.
- IVs are not automatically perfected in PvP.
- Nature has a large enough effect to matter in recommendations.
- Same-speed order is random.

Medium confidence:

- speed-base 120 as a practical investment heuristic
- which exact growth surfaces are auto-normalized and how they are named in
  current UI

## A-Layer Boundary

This page does not own executable formulas or current species stat values.

Exact stat calculation and species base stats belong to:

```text
data/reference/luoke_world_type_database_v2.json
data/runtime/battle_dex.sqlite
```

This page only defines how the advisor should use those facts in reasoning.

## Known Failure Modes

- Assuming PvP auto-perfects IVs.
- Recommending speed investment that does not change relevant turn order.
- Recommending an attacking IV on the wrong attacking side.
- Treating a speed heuristic as a hard rule.
- Forgetting that same-speed outcomes are random.
- Treating current community threshold advice as patch-stable.

## Draft Review Questions

- Which exact UI surfaces are normalized in PvP: level, star/growth, temporary
  trial values, or other cultivation surfaces?
- Should an A-layer stat calculator API expose final PvP values for a chosen IV
  and nature profile?
- Which speed-line thresholds should enter B-layer taste after more battle
  cases are reviewed?
