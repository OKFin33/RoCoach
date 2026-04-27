---
source_id: "2026-04-07_bilibili_mark_tutorial_screenshot"
source_type: "bilibili_video_screenshot_plus_user_correction"
published_date: "2026-04-07"
ingested_date: "2026-04-20"
status: "processed"
confidence: "provisional"
volatility: "shifting"
can_commit: "summary_only"
persona_free: true
raw_inputs:
  - "wiki/cache/印记速成0407/NoteGPT_《洛克王国：世界》魔法学院新生速成，印记全解读！.txt"
  - "user-provided screenshot in current thread, 2026-04-20"
human_corrections:
  - "龙噬印记: 释放完 3 能耗技能并造成伤害后，获得双攻 +30% buff"
  - "风起印记: 先手攻击时，本次技能威力 +20%"
  - "星陨印记触发: 使用非幻系技能攻击带有星陨印记的精灵；与攻击方精灵属性无关"
  - "冥想的减伤 80% 和应对攻击给 2 层星陨印记是技能效果，不是星陨印记自身效果"
  - "减速印记每层速度 -10；速冻给 2 层即合计 -20"
  - "棘刺印记和降灵印记的离场惩罚按层数叠加"
---

# 2026-04-07 Mark Tutorial Screenshot

## Source Context

The transcript in `wiki/cache/印记速成0407/` states that the video shows a
complete mark/effect table on screen and asks viewers to pause and save it.
The cached transcript does not contain that table as text.

The user provided the screenshot in the current thread on 2026-04-20 and then
manually corrected several OCR/interpretation points. This note records the
recognized table as a provisional source note for B Wiki and as a candidate
input for later A-layer mark modeling.

## Recognized Direct Mark-Producing Skills

This table records skills shown in the screenshot that directly create marks.
It is not an exhaustive source list: species traits, forms, or other skills may
also create, transfer, replace, or consume marks.

| Skill | Type | Cost | Target | Mark | Effect Text / Interpretation |
|---|---:|---:|---|---|---|
| 棘刺 | 普通 | 2 | Enemy | 棘刺印记 | When the marked fielded spirit leaves, the entering replacement loses 6% HP per layer. |
| 光合作用 | 草系 | 4 | Self | 光合印记 | At end of round, gain 1 energy per layer. |
| 蓄势待发 | 地系 | 4 | Self | 蓄势印记 | All attack-skill power +30%; energy cost +1. |
| 龙威 | 龙系 | 5 | Self | 龙噬印记 | After using a 3-cost skill and dealing damage, gain physical and magical attack +30%. |
| 疫病吐息 | 毒系 | 3 | Enemy | 中毒印记 | At end of round, deal poison-type damage equal to 3% HP per layer. |
| 降灵 | 幽系 | 2 | Enemy | 降灵印记 | When the marked fielded spirit leaves, the entering replacement loses 1 energy per layer. |
| 主场优势 | 普通 | 3 | Self | 攻击印记 | All skill power +10%. |
| 打湿 | 水系 | 4 | Self | 湿润印记 | All skill energy cost -1 per layer. |
| 速冻 | 冰系 | 4 | Enemy | 减速印记 | Enemy gains 2 layers; speed -10 per layer. |
| 增压电池 | 电系 | 2 | Self | 蓄电印记 | Attack skills gain burst/迸发: current power +10. |
| 风起 | 翼系 | 4 | Self | 风起印记 | When attacking first, current skill power +20%. |
| 冥想 | 幻系 | 4 | Enemy via response | 星陨印记 | `冥想` itself reduces damage by 80% and responds to attacks by giving the attacker 2 layers of 星陨印记. The mark is triggered when a non-illusion skill attacks a spirit with the mark; all layers are consumed and extra illusion-type damage is dealt. |

## Global Mark Claims

- Marks are separate from ordinary buffs/debuffs.
- Marks persist through switching.
- A spirit can hold at most one positive mark and one negative mark at the same
  time.
- Positive marks can replace positive marks; negative marks can replace
  negative marks.
- Some skills can clear, convert, steal, or otherwise manipulate marks.

## Review Notes

- The screenshot table should seed `wiki/pages/mechanics/marks_and_persistence.md`.
- Exact implementation belongs in a later A-layer mark registry, not in raw
  move/species fields.
- Do not treat the listed skills as the only possible sources of these marks.
- Do not treat `冥想`'s response effect as the intrinsic effect of 星陨印记.
- Do not make 星陨印记 depend on attacker species type; the confirmed trigger is
  non-幻系 skill use.

## Candidate Follow-Ups

- Confirm whether all listed mark effects scale linearly by layer.
- Confirm whether `攻击印记`, `蓄势印记`, `蓄电印记`, and `风起印记` are positive
  marks for replacement-limit purposes.
- Confirm whether `中毒印记`, `棘刺印记`, `降灵印记`, `减速印记`, and `星陨印记`
  are negative marks for replacement-limit purposes.
- Confirm exact timing for end-of-round energy and damage effects relative to
  poison, burn, freeze, weather, and fainting checks.
