# Mechanism Review Checklist

Date: 2026-04-21
Status: Historical review pass, refreshed context on 2026-04-22

## Scope Note

This file is a review-pass artifact, not the canonical current-state registry.

Its job is to preserve:

- what was reviewed
- what reasoning was accepted
- what open questions existed during the pass

It should not be read as the current live wiring state.

For current live state, prefer:

- `meta/wiki/mechanism_registry_2026-04-21.md`
- `meta/wiki/compile_use_contract_2026-04-22.md`

This checklist records the current review pass over:

- missing reviewed mechanism pages
- mechanisms already present in repo context but not yet wired cleanly into
  reviewed/runtime handling

Status labels:

- `reviewed-now`: current review was sufficient to define the intended meaning
- `reviewed-provisional`: suitable for a reviewed mechanism page with
  `provisional` confidence
- `lexicon-candidate`: should be considered for runtime mechanism-token
  detection
- `defer`: known but not worth promoting yet

## A. Runtime Recognizes The Token But Reviewed Page Is Missing

Historical status:

- completed in the 2026-04-21 mechanism coverage pass
- these entries are kept here to preserve reviewed reasoning, not to signal
  current missing-page work

### 1. 传动

- status: `reviewed-provisional`
- current explanation:
  - `传动N` means the skill shifts by `N` slots at round start
  - skill slots form a 4-slot cyclic ring; overflow wraps, so `5 = 1`
  - if multiple carried skills have transmission, resolution follows movement
    order step by step rather than as a single simultaneous collapse
  - current user-reviewed example for two `传动1` skills is considered clear
    enough for a first reviewed page
  - current game text is: at round start, skills carrying `传动X` move downward
    by `X` positions, and this effect can stack
- still open:
  - whether some species/traits can rewrite resolution order

### 2. 迸发

- status: `reviewed-provisional`
- current explanation:
  - `迸发` triggers on the first action after entry
  - it is not limited to attack skills
  - current working assumption is that passive replacement entry also counts
- still open:
  - confirm whether any entry subtype is excluded

### 3. 蓄力

- status: `reviewed-provisional`
- current explanation:
  - first turn: spend the energy and enter a charged state
  - next turn: the player must choose the same charge skill to release it
  - other carried skills are unavailable while still holding the charge
  - player may choose `聚能` or switch out to cancel the charge
  - being hit by an attack that can respond to status does not by itself break
    the charge and does not trigger the expected response effect
  - the opponent does not know which specific charge move is being prepared
  - current version skills carrying the charge keyword all cost `3` energy
  - `架势` lets the next charge move release directly; because `架势` costs 0,
    the charge move then pays its normal energy cost on that later turn
  - `嫉妒` on 伊兰亚龙 is a special rewrite: during the charge stage, other
    carried skills may be used, and their shown energy cost is reduced by the
    energy previously spent on the charge move
- still open:
  - exact UI/log language for the charge state

### 4. 奉献

- status: `reviewed-provisional`
- current explanation:
  - `奉献` belongs to the team, not just the current spirit
  - it persists across spirits
  - current version trigger sources are only `虫群` and `啃咬`
  - current reviewed effects:
    - give 2 layers of poison
    - gain 10% lifesteal
    - combo count +1
    - power +20
    - energy cost -2
- still open:
  - exact storage / display model in battle UI

### 5. 萌化

- status: `reviewed-provisional`
- current explanation:
  - `萌化` is a debuff
  - each layer regresses the spirit by one evolution stage
  - regression continues until the initial form
  - base-form-linked stats and traits revert to the regressed form; this is not
    a percentage debuff model
  - current HP does not automatically rescale to the new max HP; max HP itself
    changes with the regressed form
- still open:
  - exact term used in logs for stacked regression

## B. Already Reviewed Somewhere, But Runtime Lexicon Should Be Reconsidered

Historical status:

- `灼烧` and `魔力` have since been wired into runtime lexicon
- `复活` remains intentionally deferred as a standalone runtime token

### 6. 灼烧

- status: `lexicon-candidate`
- current explanation:
  - normal burn deals `2%` max-HP fire damage per stack
  - type interaction applies to that damage
  - `充分燃烧` adds an extra immediate burn-damage instance that does not reduce
    stacks
  - the burn-damage instance from `充分燃烧` follows the same fire-damage model
  - the normal end-of-round burn still resolves later and that later normal
    resolution does reduce stacks
- source anchor:
  - `wiki/pages/mechanics/burn_timing_and_full_combustion.md`

### 7. 魔力

- status: `lexicon-candidate`
- current explanation:
  - fainting normally deducts magic/morale
  - revive does not refund it
  - if a revived spirit dies again, magic/morale is deducted again
  - relevant known modifiers:
    - 卡瓦重 trait: faint loss `-1`
    - 帕尔 chain trait: on KO, enemy loses +1; on being KO'd, self loses +1
    - 翼王 trait: when defeated by enemy, self loses +1
    - bone-dragon-related revive edge case remains part of this cluster

### 8. 复活

- status: `defer`
- current explanation:
  - currently only a narrow set of examples, mainly bone-dragon-style revival
  - do not force a standalone runtime lexicon token yet

## C. Present In Repo Context, But Not Yet Properly Reviewed/Wired

Historical status:

- `冻结` / `中毒` / `寄生` / `聚能` / `入场 / 离场 / 脱离 / 换人`
  have since been consolidated into reviewed pages and runtime wiring
- `连击` remains deferred
- `打断` remains represented under the parent `应对` topic

### 9. 冻结

- status: `reviewed-now`
- current explanation:
  - each layer freezes `5%` max HP
  - every time freeze layers increase, the game checks whether lost HP plus
    frozen HP reaches max HP and then exhausts if so
  - ice spirits are immune
  - switching preserves freeze on the same individual, but the next spirit does
    not inherit it
  - weather/end-of-round freeze application follows normal action resolution;
    skill resolution happens before round-end weather/freeze settlement

### 10. 中毒

- status: `reviewed-now`
- current explanation:
  - ordinary poison deals `3%` poison-type damage per stack
  - `中毒印记` also deals `3%` poison-type damage
  - poison mark is not the same as ordinary poison
  - poison mark cannot be negated by poison-type immunity in the same way as
    ordinary poison; poison-type immunity does not protect against poison-mark
    damage in the same way

### 11. 寄生

- status: `reviewed-now`
- current explanation:
  - grass sustain mechanism
  - drains `6%` of the target's max HP at round end and heals the user for the
    same amount
  - this is not treated as grass-type damage

### 12. 聚能

- status: `reviewed-now`
- current explanation:
  - default action
  - restores 5 energy
  - counts as a status action
  - if interrupted, it fails
  - being responded to is not the same thing as being interrupted

### 13. 入场 / 离场 / 脱离 / 换人

- status: `reviewed-now`
- current explanation:
  - player-initiated switch and active leave are coupled but not identical
  - some effects care only that a replacement occurred, regardless of reason
    such as `棘刺印记`
  - therefore future reviewed writing should distinguish:
    - active player switch
    - active leave caused by skill/effect
    - forced replacement
    - passive replacement after faint

### 14. 连击

- status: `reviewed-now`
- current explanation:
  - current working upper limit should follow the common buff-layer cap of `99`

### 15. 打断

- status: `reviewed-now`
- current explanation:
  - `打断` is not the same as generic response
  - it should be treated as a special extra effect under the broader response
    family
  - current working judgement is that only attack skills carry explicit
    interrupt wording in observed current-version cases, for example `地刺`
- recommended page strategy:
  - fold into `应对` reviewed doctrine first
  - create a standalone page only if later evidence shows it is too large or
    too structurally distinct

## Historical Follow-Up Recommendation

High-priority reviewed-page creation:

1. `传动`
2. `迸发`
3. `蓄力`
4. `奉献`
5. `萌化`

High-priority lexicon additions:

1. `灼烧`
2. `魔力`

High-priority doctrine consolidation candidate:

1. `入场 / 离场 / 脱离 / 换人`

## Completion Note

This checklist has already been actioned for the first-pass mechanism coverage.

Do not use it as a current TODO list without cross-checking:

- `meta/wiki/mechanism_registry_2026-04-21.md`
- `advisor/retrieval.py`
- `log/project_log.md`
