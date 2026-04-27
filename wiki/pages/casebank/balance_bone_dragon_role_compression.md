---
title: "Balance Bone Dragon Role Compression"
content_class: "casebank"
status: "reviewed"
confidence: "provisional"
sources:
  - "wiki/cache/超长精灵评级0412/NoteGPT_一口气讲明白所有宠物强度？！洛克王国世界pvp排行榜.txt"
  - "wiki/pages/team_building/core_team_construction.md"
  - "wiki/pages/roles/role_taxonomy.md"
  - "wiki/pages/mechanics/morale_and_revive.md"
a_layer_refs:
  - "data/runtime/battle_dex.sqlite"
last_reviewed: "2026-04-21"
reviewed_by: "user_reviewed_synthetic_case"
persona_free: true
---

# Balance Bone Dragon Role Compression

## Case

Question tested during dogfood:

```text
为什么很多平衡队会带骨龙？
```

The reviewed answer: 寂灭骨龙 is not mainly a fast carry. In balance teams it
compresses defensive pivot, resource exchange, and late-game threat into one
slot.

## A-Layer Checks

Known exact facts to retrieve before answering:

- `寂灭骨龙`: 龙/幽
- base profile: high physical attack, good HP and physical bulk, low speed
- trait `不朽`: 力竭3回合后复活
- Dragon/Ghost defensive profile under the current dual-type rule:
  resists 普, 草, 水, 火, 电, 翼, 武, 毒, and 虫; is weak to 冰, 龙, 萌,
  恶, 幽, and 光
- defense-response access includes options such as `掩护`, `等价交换`,
  `蜡质膜`, `雪替身`, `火焰护盾`, `淤泥表皮`, `报复`, `无畏之心`,
  and `吓退`
- offensive pressure includes physical options such as `坟场搏击`, `吹炎`,
  `龙之利爪`, and `穿膛`

## Reviewed Interpretation

Balance teams value members that can take a hit, preserve rotation, and still
threaten punishment. Bone Dragon fits that job because its defensive-response
pool can convert enemy attacks into damage reduction, energy swing, status,
forced displacement, or protection for the next entrant.

The Dragon/Ghost type is part of the role, not just flavor. It gives Bone
Dragon a broad set of practical switch-in lanes for balance teams, especially
against common neutral pressure that would otherwise force damage trades. The
same typing also creates clear team-building obligations: teammates must cover
Ice, Dragon, Cute, Dark, Ghost, and Light pressure rather than assuming Bone
Dragon can blanket-check everything.

`不朽` adds long-game board value: Bone Dragon can absorb pressure or be traded
off, then return after the revive condition. This makes it especially relevant
in games where both sides have already spent health and energy.

Important correction: Bone Dragon is not a free sacrifice. Fainting still
deducts morale/magic, and if it revives and faints again, morale/magic is
deducted again. Its value is repeated board presence and tempo/resource
conversion, not immunity to the PvP loss condition.

## Answer Shape

A good short answer should say:

```text
平衡队带骨龙，是因为龙/幽给了它很宽的换入面，再叠加大量防御应对技，
能把联防、资源交换和中后期再入场压力压缩在一个位置。
不朽让它能回到场上继续制造压力，但死亡仍然扣魔力，复活后再死还会再扣；
所以它不是免费送死位，而是能把一次阵亡转化成队友无伤入场、骗能量、
拖节奏和残局压力的资源位。
```

## Failure Modes

- Saying Bone Dragon is good because it has "three lives" without mentioning
  morale/magic cost.
- Ignoring Dragon/Ghost typing and reducing the role to trait text.
- Treating it as a speed carry despite its low speed.
- Treating wide resistance coverage as universal safety while ignoring Ice,
  Dragon, Cute, Dark, Ghost, and Light weaknesses.
- Ignoring that revive timing may be too slow for fast offense.
- Recommending it without checking whether the team needs a defensive pivot or
  already has too many low-tempo members.

## Review Status

Human reviewed as broadly correct on 2026-04-21, with the morale/magic revive
correction added.
