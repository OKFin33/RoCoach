# Manual Battle Data Supplement

Date: 2026-04-14

Purpose:

- preserve PM-provided game-context corrections without overwriting wiki-canonical raw data
- separate human-verified battle supplements from crawler-discovered wiki artifacts
- record exclusion and review policy for out-of-scope forms

Status:

- accepted as the current manual supplement input layer under data-source policy B
- must be consumed by a later resolver/importer as a reviewed supplement, not as raw wiki replacement

## Scope Boundary

This file is not a replacement for wiki source artifacts.

It is a manual supplement layer for:

- hidden or non-human-facing battle-scope exclusions
- known wiki omissions
- mechanics notes that may matter to later Agent reasoning

## Exclusion Decision

Decision:

- exclude the following hidden special forms from the current battle dex target
- exclude current clearly unreleased / not-yet-live forms from the current battle dex target
- do not patch missing base stats for them
- if similar forms appear later, request human review before inclusion

Current excluded forms:

- 炽心勇狮（悲鸣的样子）
- 炽焰狮（悲鸣的样子）
- 圣羽翼王（被噩梦侵蚀的样子）
- 松仔（悲鸣的样子）
- 松叶羊（悲鸣的样子）
- 水滴蛇（悲鸣的样子）
- 水蛇锁（悲鸣的样子）
- 小勇狮（悲鸣的样子）
- 游蛇魔使（悲鸣的样子）
- 针叶巡林（悲鸣的样子）
- 卡瓦重（火山附近的样子）
- 怒目怂猫（山间竹林的样子）
- 卡卡虫（火山附近的样子）
- 凡雀
- 千棘海刺
- 紫翎鹰
- 小怂猫（山间竹林的样子）
- 丢丢（火山附近的样子）
- 寒音蛇（本命年的样子）
- 梦游（穿星星睡衣的样子）
- 凡鹰
- 古钟蛇（本命年的样子）
- 梦悠悠（穿星星睡衣的样子）

Human-review trigger rule:

- if a species form is not visible in the human-facing dex entry path and also looks like a special plot-only / non-player-usable form, do not auto-ingest it
- if the page also lacks required battle stats, treat it as out-of-scope candidate until a human confirms battle availability
- if a form page exists in wiki but the form is manually confirmed as not yet live, do not auto-ingest it into the current battle dex target
- importer status for this pattern: `human-review-before-ingest`

Follow-up PM clarification for current placeholder / zero-stat species pages:

- the current batch of placeholder all-zero entries in importer review is treated as non-live or cut content for the present game version
- they should be excluded from the current battle dex target rather than kept in `review_required`
- current manually excluded zero-stat entries:
  - 怒目怂猫（山间竹林的样子）
  - 卡卡虫（火山附近的样子）
  - 凡雀
  - 千棘海刺
  - 紫翎鹰
  - 小怂猫（山间竹林的样子）
  - 丢丢（火山附近的样子）
  - 寒音蛇（本命年的样子）
  - 梦游（穿星星睡衣的样子）
  - 凡鹰
  - 古钟蛇（本命年的样子）
  - 梦悠悠（穿星星睡衣的样子）

## Manual Species Canonical Overrides

These overrides exist for cases where multiple wiki pages describe the same playable species/form and the conflict is naming or maintainer-style noise rather than a true gameplay distinction.

Resolver rule:

- do not keep this pattern in long-term `review_required` if PM has confirmed the intended canonical record
- preserve all wiki source refs in provenance
- prefer the manually selected source page for first-pass ingest
- use our own normalized naming/stage conventions where the wiki pages disagree only on formatting or maintainer preference

### 权杖-V

- source_status: manual_verified_by_pm
- species_id: species_3d2f11185009b67c
- canonical_display_name: 权杖-V
- preferred_source_page_id: source_bc1c2be5441bb830
- normalized_initial_species_name: 权杖-II
- normalized_evolution_stage: 最终形态
- notes:
  - `权杖-V` and `权杖-Ⅴ` are treated as the same playable species/form
  - current accepted canonical row should match the later wiki page and the in-game dex screenshot
  - roman numeral / spacing variance is treated as normalization noise, not a gameplay distinction
  - `Ⅱ阶` vs `最终形态` is treated as maintainer-style inconsistency; current project normalization uses `最终形态`

### 花魁蜂后

- source_status: manual_verified_by_pm
- species_id: species_62289c78a3b186dc
- canonical_display_name: 花魁蜂后
- preferred_source_page_id: source_26271ab50bd7efd2
- override_ability_name: 虫群鼓舞
- override_ability_effect_text: 队伍中每有1只其他的虫系精灵，自己入场时获得攻防速+10%。
- notes:
  - PM clarified the first three stages of this chain use `虫群鼓舞 +10%`
  - this override is needed because the current wiki page shows the wrong ability name / text assignment on this stage
  - species base stats remain aligned to wiki and to the screenshot: total `382`

### 女王蜂

- source_status: manual_verified_by_pm
- species_id: species_ec83c314cf3ed3eb
- canonical_display_name: 女王蜂
- preferred_source_page_id: source_cf197351184ed12c
- override_ability_name: 虫群突袭
- override_ability_effect_text: 队伍中每有1只其他的虫系精灵，自己入场时获得攻防速+15%。
- notes:
  - PM clarified the boss form uses `虫群突袭 +15%`
  - first three stages use `虫群鼓舞 +10%`; current wiki assignment is therefore stale or misassigned on this chain
  - species base stats remain aligned to wiki and to the screenshot: total `364`
  - this chain should no longer be described as `纯削弱`; the current best-known interpretation is `面板降、特性升`

## Manual Move Supplements

These move records are currently unresolved from wiki crawl artifacts but were manually confirmed by PM from game context.

Resolver rule:

- these records may enter the importer as manual supplement candidates
- they do not replace or delete raw wiki artifacts
- if a later wiki-canonical `{{技能信息}}` page appears, preserve provenance and prefer the wiki record as the canonical move source unless human review says otherwise

### 溶解液

- source_status: manual_verified_by_pm
- wiki_status: unresolved_move_name
- move_name: 溶解液
- move_type: 毒
- category_raw: 魔攻
- energy_cost: 2
- power: 35
- effect_text: 造成魔伤，敌方获得两层中毒。

### 龙之舞

- source_status: manual_verified_by_pm
- wiki_status: unresolved_move_name
- move_name: 龙之舞
- move_type: 龙
- category_raw: 状态
- energy_cost: 5
- power: null
- effect_text: 蓄力，提高150%攻击力，速度+60。
- mechanics_notes:
  - 龙系蓄力是特殊机制：第一回合使用，第二回合生效

Manual anomaly note:

- `湿润印记` no longer counts as a manual canonical move supplement
- current PM clarification is that the canonical move is `打湿`, while `湿润印记` is the印记/effect name
- if a species learnset still contains `湿润印记`, treat it as a source anomaly / alias candidate pending human review rather than auto-ingesting it as a move

## Manual Move Alias Rules

Resolver rule:

- use these mappings only in importer/resolver
- preserve raw wiki move names in crawl artifacts
- do not create a fake canonical move page for the alias source

- alias: 湿润印记 -> 打湿
- notes:
  - current PM clarification is that `湿润印记` is the印记/effect name, while the canonical move is `打湿`
  - current known source occurrence is from the excluded `千棘海刺` page, but keeping the alias explicit is cleaner than leaving a permanent false unresolved

## Manual Mechanics Notes

These are not raw move fields. They belong to later mechanics modeling or Agent context.

### 印记 System Notes

- source_status: manual_verified_by_pm
- notes:
  - 湿润印记效果为能耗 -1
  - 印记不会因轮换而消失
  - 单位最多同时拥有 1 个正面印记和 1 个负面印记
  - 特殊技能可清除印记，例如：倾泻、食腐、焚烧烙印

Modeling guidance:

- do not force these notes into the raw wiki move schema
- keep them in a later mechanics or Agent supplement layer
- Agent should not be assumed to know印记 semantics unless this supplement layer is provided

Importer / Agent rule:

- these notes are allowed as mechanics supplement inputs
- they must not be flattened into raw move/species fields during first-pass importer design

## Pending Human Clarification

### 溶解扩散

Current crawler finding:

- ability name conflict exists between two effect texts in wiki-derived species pages

Known conflicting texts from artifacts:

1. 每携带1个毒系技能进入战斗,水系技能使敌方获得1层中毒。
2. 每携带一个毒系技能,水系技能额外赋予2层中毒。

Human-confirmed current text:

- 每携带1个毒系技能，水系技能使敌方中毒+1层。

Resolution note:

- treat the `+1层` wording as the current manual-verified supplement baseline
- keep the wiki-derived conflict visible in crawl artifacts for provenance
