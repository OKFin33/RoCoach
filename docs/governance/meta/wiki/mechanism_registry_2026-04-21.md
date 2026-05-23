# Mechanism Registry

Date: 2026-04-21
Refreshed: 2026-04-22

## Purpose

This file is the canonical registry for Battle Wiki mechanism coverage.

It separates:

- reviewed mechanism-page coverage
- runtime token/lexicon coverage
- parent-topic representation
- explicitly deferred standalone work

It exists so future debugging does not depend on conversation memory.

## Status Labels

- `fully_wired`
  - a reviewed page exists
  - runtime token lookup is wired
- `represented_in_parent`
  - the token is runtime-wired or deliberately covered through a reviewed
    parent topic
  - no standalone page is required in the current version
- `reviewed_only`
  - reviewed doctrine exists
  - runtime standalone token is intentionally not wired
- `deferred`
  - no standalone page/token is currently required
  - tracked to avoid future ambiguity

## Fully Wired Core Topics

These mechanism topics have both:

- a reviewed mechanism page
- runtime token lookup

| Token / Mechanism | Reviewed Page | Runtime Lexicon | Status | Notes |
|---|---|---|---|---|
| `迅捷` | `speed_priority_and_swift.md` | yes | `fully_wired` | Shared topic with `先手` and `速度` |
| `先手` | `speed_priority_and_swift.md` | yes | `fully_wired` | Shared topic with `迅捷` and `速度` |
| `速度` | `speed_priority_and_swift.md` | yes | `fully_wired` | Shared topic with `迅捷` and `先手` |
| `印记` | `marks_and_persistence.md` | yes | `fully_wired` | Mark-cluster entry token |
| `天气` | `weather_and_field_effects.md` | yes | `fully_wired` | Weather-cluster entry token |
| `应对` | `response_counterplay.md` | yes | `fully_wired` | Response/counterplay token |
| `传动` | `transmission_and_skill_slots.md` | yes | `fully_wired` | Mechanical skill-slot movement |
| `迸发` | `burst_trigger_and_entry_actions.md` | yes | `fully_wired` | Entry-action trigger cluster |
| `蓄力` | `charge_and_release.md` | yes | `fully_wired` | Charge/release cluster |
| `奉献` | `bug_contribution_fengxian.md` | yes | `fully_wired` | Team-level bug contribution mechanic |
| `萌化` | `degeneration_and_menghua.md` | yes | `fully_wired` | Degeneration / de-evolution mechanic |
| `灼烧` | `burn_timing_and_full_combustion.md` | yes | `fully_wired` | Burn timing and `充分燃烧` model |
| `冻结` | `status_effects_and_persistence.md` | yes | `fully_wired` | Status-cluster topic |
| `中毒` | `status_effects_and_persistence.md` | yes | `fully_wired` | Status-cluster topic |
| `寄生` | `status_effects_and_persistence.md` | yes | `fully_wired` | Status-cluster topic |
| `聚能` | `energy_actions_and_focus.md` | yes | `fully_wired` | Baseline resource action |
| `魔力` | `morale_and_revive.md` | yes | `fully_wired` | Morale-loss mechanics |
| `换人` | `entry_exit_and_replacement_timing.md` | yes | `fully_wired` | Entry/exit timing cluster |
| `离场` | `entry_exit_and_replacement_timing.md` | yes | `fully_wired` | Entry/exit timing cluster |
| `脱离` | `entry_exit_and_replacement_timing.md` | yes | `fully_wired` | Entry/exit timing cluster |
| `回场` | `entry_exit_and_replacement_timing.md` | yes | `fully_wired` | Entry/exit timing cluster |
| `入场` | `entry_exit_and_replacement_timing.md` | yes | `fully_wired` | Entry/exit timing cluster |
| `替换上场` | `entry_exit_and_replacement_timing.md` | yes | `fully_wired` | Entry/exit timing cluster |
| `主动离场` | `entry_exit_and_replacement_timing.md` | yes | `fully_wired` | Entry/exit timing cluster |

## Represented In Parent Topics

These are real mechanics, aliases, or sub-mechanics, but the current version
does not require a standalone page because a reviewed parent topic already
covers them.

| Token / Mechanism | Current Home | Runtime Lexicon | Status | Notes |
|---|---|---|---|---|
| `打断` | `response_counterplay.md` | yes | `represented_in_parent` | Treated as a special response-side effect, not a standalone page |
| `雨天` | `weather_and_field_effects.md` | yes | `represented_in_parent` | Weather subtype |
| `沙暴` | `weather_and_field_effects.md` | yes | `represented_in_parent` | Weather subtype |
| `雪天` | `weather_and_field_effects.md` | yes | `represented_in_parent` | Same in-game mechanism as `暴风雪` |
| `暴风雪` | `weather_and_field_effects.md` | yes | `represented_in_parent` | Same in-game mechanism as `雪天` |
| `棘刺印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Negative mark subtype |
| `光合印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Positive mark subtype |
| `蓄势印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Positive mark subtype |
| `龙噬印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Positive mark subtype |
| `中毒印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Negative mark subtype |
| `降灵印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Negative mark subtype |
| `攻击印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Positive mark subtype |
| `湿润印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Positive mark subtype |
| `减速印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Negative mark subtype |
| `蓄电印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Also conceptually touches `迸发` |
| `风起印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Positive mark subtype |
| `星陨印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Negative mark subtype |
| `清印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Mark operation |
| `驱散印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Mark operation |
| `偷印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Mark operation |
| `覆盖印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Mark operation |
| `转换印记` | `marks_and_persistence.md` | yes | `represented_in_parent` | Mark operation |

## Reviewed But Not Standalone Runtime-Wired

These topics already have reviewed doctrine coverage, but a standalone runtime
token is intentionally not wired in the current version.

| Token / Mechanism | Reviewed Page | Runtime Lexicon | Status | Notes |
|---|---|---|---|---|
| `复活` | `morale_and_revive.md` | no standalone token | `reviewed_only` | Covered through morale/revive parent topic; kept deferred as independent trigger |

## Explicitly Deferred Standalone Work

These items are tracked so they do not get lost, but the current version does
not require standalone reviewed pages or standalone runtime tokens.

| Token / Mechanism | Current Home | Status | Notes |
|---|---|---|---|
| `连击` | none standalone | `deferred` | Current working cap is 99; add standalone page only if doctrine demand grows |
| standalone `打断` page | `response_counterplay.md` parent | `deferred` | Current parent-topic treatment is sufficient |
| standalone `复活` token | `morale_and_revive.md` parent | `deferred` | Current runtime focus is morale, not revive as a first-class retrieval trigger |

## Current Debug Order

If a mechanism retrieval bug appears, audit in this order:

1. token mapping exists in `advisor/retrieval.py`
2. reviewed page exists under `wiki/pages/mechanics/`
3. page compiles into `wiki/compiled/`
4. relevant tests exist under:
   - `tests/test_retrieval.py`
   - `tests/test_advisor.py`

## Scope Note

This registry is a Battle Wiki governance artifact.

It does not decide:

- A-layer schema structure
- runtime enforcement beyond token/page coverage
- future automated wiki-maintenance workflow

Those belong to separate console/main-thread implementation work.
