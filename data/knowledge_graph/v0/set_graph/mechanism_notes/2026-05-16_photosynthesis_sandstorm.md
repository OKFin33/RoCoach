# Mechanism Review: Photosynthesis Mark and Sandstorm

Date: 2026-05-16

Purpose: prevent Meta Graph v0 from promoting uncertain mechanics into stable
runtime advice.

## Checked Facts

- `光合作用`: Battle Dex/BWiki text says this is a grass status move, 4 energy,
  and grants `1` layer of `光合印记`.
- `光合印记`: local mechanism notes say it recovers `1` energy at turn end.
- In the current 光合武队 candidate cards, the stable active source of
  `光合印记` is `针叶巡林` via `光合作用`.
- `食尘短绒` with `特殊清洁场景` can steal `1` enemy mark at turn end, but this is
  not a stable active way to create `光合印记`.
- `沙涌`: Battle Dex/BWiki text says this is a ground status move, 7 energy, and
  changes weather to `沙暴` for 8 turns.
- `沙暴`: local mechanism notes and community guides agree that sandstorm
  reduces ground move energy cost. Exact discount wording differs by source
  (`减半`, `-2`, or strategy shorthand like `0-1耗`), so runtime cards should say
  "降低地系技能能耗" unless the exact source is cited.
- `扬沙`: Battle Dex/BWiki text says this is a ground physical move, 1 energy,
  60 power, and deals physical damage. PM confirmed it is unrelated to `沙暴`.

## Graph Decision

- Do not model `棋绮后` as the source of `光合印记`.
- Do not describe `光合印记` as a buff only for the main carry; model it as a team
  resource/economy window per PM correction.
- Do not model `食尘短绒` as a stable `光合印记` source; only mention mark stealing
  as an incidental upside.
- Do not model `芋香巨角蛛` as a weather setter from `扬沙`.
- Treat `扬沙` as a low-cost ground physical attack only, not as a sandstorm
  trigger or sandstorm resource chain.
