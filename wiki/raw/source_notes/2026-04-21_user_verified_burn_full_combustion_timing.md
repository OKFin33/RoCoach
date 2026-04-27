# Source Note: User-Verified Burn And Full Combustion Timing

```yaml
source_id: user_verified_burn_full_combustion_timing_2026_04_21
title: "User-verified burn timing and Full Combustion interaction"
source_type: user_confirmation
published_at: 2026-04-21
collected_at: 2026-04-21
origin_platform: codex_thread
can_commit: summary_only
sensitivity: public_summary
source_class:
  - battle_mechanics_confirmation
  - burn_timing
  - full_combustion_interaction
confidence: user_confirmed
volatility:
  mechanics_core: medium
status: confirmed_by_user_pending_a_layer
persona_risk: false
cross_game_risk: low
```

## Confirmed Statements

- `灼烧` 每层在正常结算时造成目标最大生命值 `2%` 的火系伤害。
- 该伤害受属性克制关系影响。
- `充分燃烧` 触发的额外灼烧伤害也按同一火系伤害逻辑理解。
- `充分燃烧` 造成的灼烧伤害是额外的，不会减少灼烧层数。
- 到回合结束时，本应正常结算的那次灼烧伤害仍会照常触发。
- 该回合结束时的正常灼烧结算会正常衰减灼烧层数。

## Operational Interpretation

The current best B-layer interpretation is:

1. `充分燃烧` first doubles existing burn stacks on the target.
2. The normal round-end burn instance deals `2%` max HP fire damage per stack,
   with type interaction still applying.
3. `充分燃烧` then triggers one immediate burn-damage instance under that same
   fire-damage model.
4. That immediate burn-damage instance is extra damage and does not itself
   consume burn stacks.
5. The regular end-of-round burn step still happens later in the same round.
6. The regular end-of-round burn step applies the normal burn-layer decay.

## Boundary

- This note confirms timing behavior needed for advisor reasoning.
- Exact UI timing, log ordering, and engine-hook names still belong in A-layer
  modeling if the project later formalizes executable battle simulation.
