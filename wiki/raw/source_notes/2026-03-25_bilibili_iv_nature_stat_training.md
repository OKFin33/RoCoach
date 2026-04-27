---
source_id: "2026-03-25_bilibili_iv_nature_stat_training"
source_type: "bilibili_video_transcript"
published_date: "2026-03-25"
ingested_date: "2026-04-20"
status: "processed"
confidence: "provisional"
volatility: "shifting"
can_commit: "summary_only"
persona_free: true
raw_inputs:
  - "wiki/cache/个体0325/NoteGPT_洛克王国世界全网最详细喂奶级PVP攻略系列！对战基础篇第二期（个体值精讲）——圣龙骑士Roco-龙星出品.txt"
supporting_inputs:
  - "wiki/cache/PVP扫盲0419/NoteGPT_一口气让你彻底学会精灵对战！PVP扫盲，新手必看！.txt"
  - "wiki/cache/数值基础0405/NoteGPT_玩懂PVP！洛克王国属性&伤害计算公式！「洛克王国：世界」.txt"
  - "wiki/cache/速度线:词条 0403/NoteGPT_【洛克王国世界】pvp入坑指南硬核知识，全图鉴速度线计算_所有词条解释_配队逻辑.txt"
a_layer_refs:
  - "data/reference/luoke_world_type_database_v2.json"
  - "data/runtime/battle_dex.sqlite"
---

# 2026-03-25 IV / Nature / Stat Training Tutorial

## Source Context

The 2026-03-25 beginner PvP training tutorial focuses on individual-value
selection, nature, traits, marks, and enhancement. This source is useful for
B-layer advice about how to choose stat investment for a team role. Exact stat
formula authority remains in A-layer references.

## Extracted Claims

- Individual-value choice should be based on team role, species base stats, and
  usable skill pool.
- A species' base stat distribution is stable for the same species/form.
- Damage dealers usually choose the relevant attacking stat, then commonly HP
  and speed or a defensive stat depending on role and speed line.
- Pure defensive or utility pieces often prioritize HP, physical defense, and
  magical defense.
- Speed investment is contextual; the source gives a rule of thumb that speed
  base above roughly 120 is more likely to justify max speed investment, while
  slower species may not gain enough turn-order value from speed IVs alone.
- PvP normalizes some growth/level surfaces, but does not auto-perfect IVs.
- Key cultivation judgment: do not evaluate a species only by base stats; role,
  trait, and skill pool can make a non-obvious stat choice correct.

## A-Layer Cross-Checks

Current A-layer stat formula source states:

- PvP stats depend on species base stat, IV, and nature.
- IV initial range is 7-10.
- Up to 3 stats can have IV bonuses.
- PvP IV multiplier is 6, so PvP IV contribution range is 42-60.
- Nature boost is +20%; nature penalty is -10%.
- Same speed means random turn order.

## Review Notes

- Treat speed-threshold advice as B-layer taste, not a hard engine rule.
- Treat exact stat formulas as A-layer authority.
- Do not import effort-value or Pokemon-style training assumptions.
- A team recommendation should mention IV/nature constraints when a plan relies
  on speed control, bulk thresholds, or a specific attacking side.
