# Cache Inventory 2026-04-20

```yaml
inventory_id: cache_inventory_2026_04_20
cache_root: "wiki/cache"
created_at: 2026-04-20
status: draft
can_commit: summary_only
```

## Purpose

Inventory the current `wiki/cache/` materials and decide how each source should
be handled by the Battle Wiki intake process.

The cache itself is not a doctrine source. It is an intake staging area.

## Global Rules

- Do not commit `.DS_Store`.
- Do not commit full video transcripts as doctrine pages.
- Do not commit large PDF/image raw assets unless explicitly approved.
- Convert useful material into `wiki/raw/source_notes/` summaries.
- Promote only cross-checked, reviewed claims into `wiki/pages/`.
- Treat current-meta and rating content as volatile snapshots.

## File Classes Found

```text
txt: video transcript / NoteGPT output
docx: extracted or manually organized text
pdf: slide deck / visual source
png: screenshot source image
.DS_Store: local macOS junk, ignore
```

## Source Groups

### 1. `冠军队伍逻辑0308`

Source:

- `NoteGPT_冠军配队的底层逻辑！【洛世界PVP教学】.txt`

Likely class:

- `team_building_methodology`
- `role_taxonomy_candidate`

Main value:

- role framing around output / support / interception
- team construction order
- core-first team-building logic

Risk:

- terminology may conflict with existing role taxonomy
- early source date

Recommended action:

- create source note
- compare with `specs/role_taxonomy.md`
- extract doctrine candidates for `wiki/pages/team_building/` and
  `wiki/pages/roles/`

Priority: high

### 2. `属性、血脉、技能类型0324`

Source:

- `NoteGPT_洛克王国世界全网最详细喂奶级PVP攻略系列！对战基础篇第一期（属性、血脉、技能类型）——圣龙骑士出品.txt`

Likely class:

- `mechanics_tutorial`
- `type_bloodline_move_boundary`

Current handling:

- source note created:
  `wiki/raw/source_notes/2026-03-23_bilibili_basic_pvp_type_bloodline_move_categories.md`
- draft page created:
  `wiki/pages/mechanics/type_bloodline_move_boundary.md`

Priority: processed

### 3. `个体0325`

Source:

- `NoteGPT_洛克王国世界全网最详细喂奶级PVP攻略系列！对战基础篇第二期（个体值精讲）——圣龙骑士Roco-龙星出品.txt`

Likely class:

- `build_investment_methodology`
- `stat_allocation_methodology`

Main value:

- individual values / nature / traits / marks / enhancement as build decisions
- role, stat profile, and move pool as inputs to investment choice
- distinction between output and defensive support stat priorities
- speed investment heuristic

Risk:

- many exact numbers and item rules belong to A-layer or product onboarding,
  not B doctrine
- speed threshold claims are meta-sensitive

Recommended action:

- summarize as source note
- extract only methodology: role + stats + move pool determine investment
- do not copy exact item or value rules into B doctrine without validation

Priority: medium-high

### 4. `主流阵容0326`

Sources:

- `PvP主流阵容全回顾.pdf`
- `帮我整理出每一页的所有文本，对应页码和内容.docx`

Cleaned intake artifact:

- `wiki/raw/source_notes/2026-03-26_mainstream_pvp_archetype_deck.md`

Likely class:

- `archetype_snapshot`
- `team_casebank_seed`
- `historical_meta_observation`

Main value:

- 44-page deck covering seven teams:
  - 雷暴队
  - 鹿核队
  - 毒队
  - 星陨队
  - 武队
  - 虫队
  - 幽灵队
- team identity, core members, gameplay loop, difficulty, projected strength
- useful archetype and casebank seed material

Risk:

- very large PDF raw asset
- mixes beta history, public-test prediction, and team evaluation
- exact team/member claims may be stale
- slide extraction may distort text order

Recommended action:

- do not commit raw PDF unless explicitly approved
- use the cleaned Markdown artifact instead of raw PDF/Word for normal intake
- create version observation, not stable doctrine
- later split into casebank drafts per archetype

Priority: cleaned; high for archetype map, low for exact recommendations

### 5. `联防先读0327`

Source:

- `NoteGPT_从零开始入门洛克王国PVP！用联防和先读来构筑战斗的基础！.txt`

Likely class:

- `team_building_methodology`
- `battle_review_case`

Main value:

- introduces defensive switching and prediction
- shows how to avoid bad matchups through rotation
- gives practical battle sequence examples

Risk:

- transcript quality is noisy
- examples are single-match and context-dependent

Recommended action:

- create source note
- extract doctrine into `defensive_structure` and `prediction` pages
- selected examples may become casebank entries

Priority: high

### 6. `速度线:词条 0403`

Source:

- `NoteGPT_【洛克王国世界】pvp入坑指南硬核知识，全图鉴速度线计算_所有词条解释_配队逻辑.txt`

Likely class:

- `mechanics_tutorial`
- `speed_line_methodology`
- `glossary_seed`

Main value:

- speed-line reasoning
- stat calculation references
- common terms: marks, weather, buffs/debuffs, freezing, degeneration,
  contribution, burst, swift
- practical method: know hot species speed lines rather than memorize all

Risk:

- exact formulas and speed values belong to A-layer
- several transcript/OCR errors
- current hot species references are volatile

Recommended action:

- create source note
- extract methodology page for speed-line reasoning
- send exact formulas/values to A-layer validation

Priority: high

### 7. `战斗系统入门:18属性 0402`

Source:

- `【洛克王国世界：真正的战斗系统入门！18种系别机制简介-哔哩哔哩】 httpsb23tvSdcasm.docx`

Likely class:

- `mechanics_tutorial`
- `type_mechanism_overview`

Current handling:

- source note created:
  `wiki/raw/source_notes/2026-04-02_bilibili_battle_system_intro_18_types.md`
- version observation created:
  `wiki/raw/version_observations/2026-04-02_early_type_identity_snapshot.md`

Note:

- user clarified the later no-voice subtitle/demo section can be ignored.

Priority: processed

### 8. `天气速成0404`

Source:

- `NoteGPT_《洛克王国：世界》魔法学院新生速成，玩转天气机制！.txt`

Likely class:

- `mechanics_tutorial`
- `weather_glossary_seed`

Main value:

- rain, sandstorm, snowstorm basics
- weather duration/reset framing
- relationship between weather and type/team advantage

Risk:

- exact effects and durations require A-layer validation
- source is short and simplified

Recommended action:

- create source note
- combine with 0402 and 0403 before drafting weather page

Priority: medium

### 9. `数值基础0405`

Sources:

- `NoteGPT_玩懂PVP！洛克王国属性&伤害计算公式！「洛克王国：世界」.txt`
- six PNG screenshots

Likely class:

- `formula_source`
- `mechanics_tutorial`
- `a_layer_cross_check`

Main value:

- stat and damage calculation claims
- STAB / same-type bonus claim
- attribute restraint and damage formula discussion
- screenshots likely preserve formula visual evidence

Risk:

- formula content is exact-mechanics territory and belongs primarily to A-layer
- screenshots are raw media and should not be committed by default
- high risk if B doctrine starts owning formula truth

Recommended action:

- create source note
- route formula claims to A-layer validation
- only extract B doctrine such as "damage advice must respect formula and
  uncertainty"

Priority: high for A-layer validation, medium for B doctrine

### 10. `印记速成0407`

Source:

- `NoteGPT_《洛克王国：世界》魔法学院新生速成，印记全解读！.txt`

Likely class:

- `mechanics_tutorial`
- `mark_glossary_seed`

Main value:

- marks differ from ordinary buffs/debuffs
- marks persist through switching
- one positive and one negative mark limit
- mark-based team construction

Risk:

- claims on number of marks and exact effects require validation

Recommended action:

- create source note
- use with 0402 and 0403 for `marks_and_persistence` draft

Priority: high

### 11. `基本攻略0411`

Source:

- `NoteGPT_再见了毒攻略！这才是pvp的正确入坑姿势，一个视频帮你决定是否入坑洛克王国世界pvp.txt`

Likely class:

- `beginner_pvp_orientation`
- `counterexample_seed`

Main value:

- frames PvP around attribute restraint and guessing/response
- warns against bad guides / low-quality recipes
- useful for recommendation taste and anti-patterns

Risk:

- rhetorical and opinionated
- may overstate early meta simplicity

Recommended action:

- summarize as source note
- extract anti-garbage-guide principles for recommendation taste

Priority: medium

### 12. `萌新百科0411`

Source:

- `NoteGPT_【洛克王国：世界】保姆级萌新大百科.txt`

Likely class:

- `general_game_onboarding`
- `low_priority_non_pvp_context`

Main value:

- broad game onboarding
- small battle-system section: battle UI, 10 energy, action choices, type
  restraint, sample PvE recommendations

Risk:

- explicitly says it is not PvP-focused
- lots of non-battle content irrelevant to B Wiki

Recommended action:

- do not prioritize
- mine only if we need a beginner glossary cross-check

Priority: low

### 13. `为什么需要速度0412`

Sources:

- `NoteGPT_为什么要加速度性格的精灵？.txt`
- one PNG screenshot

Likely class:

- `speed_line_snapshot`
- `current_meta_observation`

Main value:

- explains why speed nature matters
- provides examples of boosted speed thresholds
- mentions same-speed tie as random

Risk:

- current environment and speed examples are volatile
- screenshot is raw image source

Recommended action:

- combine with 0403 speed-line source
- create version observation, not stable speed table

Priority: medium

### 14. `超长精灵评级0412`

Source:

- `NoteGPT_一口气讲明白所有宠物强度？！洛克王国世界pvp排行榜.txt`

Likely class:

- `rating_snapshot`
- `early_meta_observation`
- `species_role_signal`

Main value:

- large current-environment species ranking discussion
- many role and matchup comments
- useful for extracting "why a species is strong" patterns

Risk:

- extremely volatile
- opinionated ranking
- long transcript with many exact species claims
- should not become default recommendation truth

Recommended action:

- create only a high-level source note initially
- mine specific claims only when multiple sources mention the same pattern
- use for casebank/role priors with low confidence

Priority: low for doctrine, medium for future role-signal mining

### 15. `图鉴1-43号常用配置0412`

Source:

- `NoteGPT_【洛克王国世界】全图鉴pvp_pve常用精灵如何养成配置，了解常用技能池，避免信息差（1-34号图鉴）.txt`

Likely class:

- `species_set_examples`
- `a_layer_cross_check`

Main value:

- common builds and move pools for early dex species
- role hints and anti-information-gap notes

Risk:

- mostly exact species/set guidance, not generic doctrine
- patch-sensitive
- high chance of conflict with battle-dex or current meta

Recommended action:

- do not promote to generic B doctrine
- use selectively for casebank examples after A-layer validation

Priority: low-medium

### 16. `光合武队0414`

Source:

- `NoteGPT_《光合武队怎么玩？一期视频讲清它的底层逻辑》.txt`

Likely class:

- `team_casebank_seed`
- `archetype_methodology`

Main value:

- explains a team archetype through bottom-level logic
- discusses energy exchange, mark economy, long-game plan, and endgame
  conversion
- high value as a casebank example

Risk:

- current team strength is volatile
- exact members and moves need A-layer validation

Recommended action:

- create source note
- later draft casebank entry for 光合武队
- extract generic doctrine around resource tempo and endgame conversion

Priority: high

### 17. `冷门阵容电球咩咩0415`

Source:

- `NoteGPT_【洛克阴阵容1】版本最强最阴！闪电无线连-电球咩咩！.txt`

Likely class:

- `niche_team_case`
- `low_confidence_casebank_seed`

Main value:

- illustrates how a niche species can become a win condition through move,
  trait, and team support
- useful for "same weak-looking species, different context" doctrine

Risk:

- meme/clickbait framing
- likely low sample size
- exact combo legality and consistency require validation

Recommended action:

- create low-confidence case note only if needed
- do not generalize without more examples

Priority: low-medium

### 18. `熟悉热门技能特性0417`

Source:

- `NoteGPT_洛克王国PVP焚决·上集（缓解精灵培养焦虑，熟悉热门技能特性）.txt`

Likely class:

- `current_meta_training`
- `popular_skill_trait_snapshot`

Main value:

- reduces build anxiety by focusing on popular traits and skills
- may identify recurring meta mechanics

Risk:

- very current-meta-sensitive
- exact skill/trait claims are A-layer facts

Recommended action:

- summarize as version observation
- mine only stable recommendation-taste doctrine: learn hot skills/traits to
  read opponent intent

Priority: medium

### 19. `PVP扫盲0419`

Source:

- `NoteGPT_一口气让你彻底学会精灵对战！PVP扫盲，新手必看！.txt`

Likely class:

- `mechanics_tutorial`
- `beginner_pvp_orientation`
- `glossary_seed`

Main value:

- broad mechanics sweep:
  - stats
  - individual values
  - move categories
  - response
  - energy management
  - buffs/debuffs
  - marks
- useful as a later cross-check source for multiple pages

Risk:

- broad and long
- some exact numbers and examples need validation
- may contain casual analogy and simplification

Recommended action:

- create source note
- use as cross-source support for response, energy, buff/debuff, mark pages

Priority: high

## Proposed Processing Order

1. `联防先读0327`
2. `冠军队伍逻辑0308`
3. `速度线:词条 0403`
4. `印记速成0407`
5. `PVP扫盲0419`
6. `主流阵容0326`
7. `数值基础0405`
8. `光合武队0414`

Rationale:

- first build generic doctrine pages
- then add glossary/mechanics cross-checks
- then add archetype and casebank snapshots
- keep volatile species ratings and exact build lists for later mining

## Immediate Draft Page Opportunities

Existing:

- `wiki/pages/mechanics/type_bloodline_move_boundary.md`

Next candidates:

- `wiki/pages/mechanics/response_counterplay.md`
- `wiki/pages/mechanics/marks_and_persistence.md`
- `wiki/pages/mechanics/speed_line_reasoning.md`
- `wiki/pages/team_building/defensive_structure.md`
- `wiki/pages/team_building/resource_tempo.md`
- `wiki/pages/roles/contextual_role_assignment.md`
- `wiki/pages/archetypes/archetype_labels_are_hypotheses.md`

## Git Handling

Safe to commit:

- this inventory
- summarized source notes
- doctrine pages
- schema/policy files

Do not commit by default:

- `wiki/cache/`
- `.DS_Store`
- raw PDF deck
- raw screenshots
- full transcripts if copyright or size risk is unacceptable

If `wiki/cache/` must remain local, add it to `.gitignore` after Git boundary is
repaired.
