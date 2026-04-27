# Source Note: Detailed 18-Type Mechanism Extraction From 2026-04-02 Tutorial

```yaml
source_id: bilibili_2026_04_02_battle_system_intro_18_types
title: "洛克王国世界：真正的战斗系统入门！18种系别机制简介"
source_type: video_transcript
published_at: 2026-04-02
collected_at: 2026-04-21
origin_platform: bilibili
source_url: "https://b23.tv/Sdcasmr"
local_transcript_path: "/Users/okfin3/project/GitHub/OKFin33/Roco/wiki/cache/战斗系统入门:18属性 0402/【洛克王国世界：真正的战斗系统入门！18种系别机制简介-哔哩哔哩】 httpsb23tvSdcasm.docx"
can_commit: summary_only
sensitivity: public_summary
source_class:
  - mechanics_tutorial
  - type_mechanism_overview
  - early_public_learning_note
confidence: provisional
volatility:
  mechanics_core: shifting
  type_identity_summary: shifting
  named_examples: ephemeral
a_layer_required: true
persona_risk: false
cross_game_risk: low
status: intake_detailed_extraction_complete
```

## Scope

This note re-reads the 2026-04-02 tutorial DOCX and extracts the explicit
mechanics claims for:

- battle baseline concepts directly tied to type understanding
- each of the 18 types
- named special terms mentioned in the tutorial

This note is still `summary_only`. It does not authorize direct fact use without
review. It exists to support:

- future reviewed mechanics pages
- mechanism lexicon construction
- agent retrieval hardening

## Global Battle-System Claims Mentioned Before The Type Tour

These are not type-specific, but the tutorial uses them as prerequisites for
understanding later type mechanisms.

### Battle Resource And Action Baseline

- Typical energy cap is described as `10`, with exceptions.
- `聚能` restores `5` energy.
- `聚能` is described as a `状态` action and can be responded to by
  status-response effects.
- Using a skill, switching, or capture consumes the turn.
- Bag actions such as resonance magic and recovery bottle are described as not
  consuming the turn.

### Type / Bloodline / Move Boundary

- `系别` is permanent and defines defensive restraint.
- `血脉` is changeable and affects move access.
- Restraint is move type against target species type.
- A fire-type species using a non-fire move does not automatically apply
  fire-type restraint.
- `愿力冲击` type follows bloodline rather than species type.

### Buff / Debuff / Mark / Persistence

- Most ordinary buffs and debuffs disappear after switching.
- Marks persist through switching.
- Some effects can apply to all future entrants.
- Some effects are permanent once gained.
- Each species can hold at most one positive mark and one negative mark at the
  same time.

### Turn Order

- Speed determines order unless priority / first-strike value exists.
- Priority is said to override speed.
- Environment speed bonuses are described as absent in PvP.

### Move Categories / Response

- All skills are attack, defense, or status.
- Response is category-specific: respond to attack, defense, or status.
- Response is an extra-effect trigger, not a universal interrupt.
- Public release no longer has the old beta universal response bonus baseline.
- Current response value is move-specific.

## Type Mechanism Extraction

Below, `explicit` means the tutorial stated it directly. `inference` is only
used when the tutorial structure strongly implies a role but does not state it
as a rule sentence.

### 普通

Explicit claims:

- Normal is the broadest utility pool.
- Normal covers defense, attack, and status widely.
- Common functions listed:
  - increase or reduce energy cost
  - force target to leave
  - dispel buffs
  - dispel marks
  - cause degeneration / regression
  - multi-hit
  - burst

Interpretation note:

- The tutorial frames Normal less as a narrow mechanism family and more as the
  general-purpose utility bucket.

### 草

Explicit claims:

- `光能聚集`: after using other grass moves, this move gains `+60` permanent
  power each time.
- `寄生`: drains `6%` of the target's life each end of turn and heals the user.
- Same-type species are generally immune to their own type's special effect.
- Grass has a positive mark: `光合印记`.
- `光合印记`: recover `1` energy at turn end.
- Grass has many self-heal tools.

Interpretation note:

- The tutorial presents Grass as sustain plus persistent economy.

### 火

Explicit claims:

- Fire damage ramps through `灼烧`.
- `灼烧`: each stack burns `2%` max life at turn end.
- Burn is a negative effect, not a mark.
- Burn clears when the target leaves the field.

Cross-check correction added on 2026-04-21:

- The tutorial's `2%` burn number is not stable enough for direct reuse.
- Later external glossary material conflicted with the tutorial on the exact
  numeric value.
- User-confirmed battle verification in the current thread currently takes
  precedence for B-layer review:
  - normal burn deals `2%` max-HP fire damage per stack
  - type interaction still applies to that burn damage
  - `充分燃烧` triggers an extra immediate burn-damage instance without
    reducing burn stacks
  - the normal end-of-round burn instance still resolves separately and that
    round-end instance does reduce stacks
- Treat the tutorial's fire section as an early public explanation, not as the
  final authority for burn timing or exact numeric scaling.

Interpretation note:

- Fire is framed as percentage-burn pressure with snowballing damage.

### 水

Explicit claims:

- Water introduces the weather concept.
- `雨天`: on-field water moves gain `+50%` power.
- Water has `润泽印记`.
- `润泽印记`: each layer reduces all-skill cost by `1`.
- Water design is said to revolve heavily around cost reduction.
- Example given: a water defense move can reduce all-skill cost by `2` on
  successful response to attack.

Interpretation note:

- Water is framed as weather window plus cost compression.

### 光

Explicit claims:

- Light can use other types of moves well.
- `天光`: becomes the same type as the current weather.
- Light gets bonuses based on other equipped or used move types.
- `过曝`: each use of another type's move adds `+30` power.
- `折射`: gains different extra effects based on what non-light move types are
  equipped.

Interpretation note:

- Light is framed as cross-type exploitation and loadout-dependent scaling.

### 地

Explicit claims:

- Ground has strong defense tools.
- Ground has many effects that reduce enemy hit count / combo count.
- Ground has anti-switch tools:
  - stop the enemy from leaving
  - force the enemy to leave
- Ground weather: `沙暴`.
- `沙暴`: ground-skill cost is halved.
- Ground has `蓄势印记`.
- `蓄势印记`: all attack power `+30%`, but all attack cost `+1`.

Interpretation note:

- Ground is framed as tempo denial, switch control, and heavy-move enabling.

### 冰

Explicit claims:

- `冻结`: each stack freezes `5%` of the target's life.
- If current HP is below the frozen amount, the target is immediately defeated.
- Freeze persists when the target leaves; it cannot be cleared by switching.
- Ice weather: `暴风雪`.
- `暴风雪`: each turn, every on-field non-ice species gains `2` freeze stacks,
  including your own non-ice species.
- Ice has many tools that increase enemy energy cost.

Interpretation note:

- Ice is framed as max-HP pressure plus persistent punishment.

### 电

Explicit claims:

- Electric has a special trigger called `迸发`.
- `迸发` means an effect that triggers on the first action after entering.
- Electric can self-control leave / return loops to trigger `迸发` repeatedly.
- `集中`: return to backline at turn end, enabling another future `迸发`.
- `过载电路`: after returning, the next move both triggers `迸发` and is used
  twice; this spends double energy because the move is actually used twice.
- Electric also has tools to force enemy leave / return.
- Some electric damage scales with repeated leave / return counts.
- Electric has `蓄电印记`.
- `蓄电印记`: `迸发` moves gain `+10` power per layer.

Interpretation note:

- Electric is framed as re-entry rhythm and repeated first-action exploitation.

### 毒

Explicit claims:

- Poison relies on `中毒`.
- `中毒`: each stack deals `3%` poison damage.
- Regular poison clears when the target leaves, like burn.
- Poison can also create a negative mark, distinct from regular poison.
- Poison mark also deals `3%` poison damage.
- Poison mark remains on the field and damages every entrant at turn end.
- Poison skills or poison traits can convert regular poison into poison mark.

Interpretation note:

- Poison is framed as two-layer pressure:
  - normal switch-clearing poison
  - switch-persistent poison mark

### 虫

Explicit claims:

- Bug centers on `奉献`.
- `奉献` is not a mark and not an ordinary buff.
- It is a hidden backline/team contribution that benefits all Bug allies.
- Five `奉献` variants are listed:
  - hit count `+1`
  - energy cost `-2`
  - enemy gets `2` poison stacks
  - move power `+20`
  - gain `10%` lifesteal
- The tutorial gives an example where stacked `奉献` turns a high-cost bug move
  into a much cheaper and much stronger move.

Interpretation note:

- Bug is framed as hidden team-bank value that later explodes on a carry turn.

### 武

Explicit claims:

- Martial is defined by successful response payoff.
- If the response call is correct, martial moves become extremely strong.
- If response fails, martial baseline numbers are very mediocre.
- Examples named:
  - `截拳` on response to status can interrupt
  - `散手`, `无影脚`, `爆冲`, `技巧打击`, `应门` all get massive value on
    successful response

Interpretation note:

- Martial is framed as the highest read-reward family.

### 龙

Explicit claims:

- Dragon's defining drawback is `蓄力`.
- `蓄力` means the skill is prepared this turn and resolves next turn.
- During the charge turn / charge state, some other tools can bypass or alter
  the restriction.
- `架势`: recover `20%` life and make the next move not need charge.
- Some dragon species have traits that let them use any move on the second turn
  after charging.
- Dragon has very high raw damage because it pays the charge tax.
- `龙噬印记`: after using a `3`-cost move, gain `+30%` dual attack.

Interpretation note:

- Dragon is framed as heavy power with charge manipulation.

### 翼

Explicit claims:

- Wing centers on `迅捷`.
- Tutorial explanation of `迅捷`:
  - when a species actively enters during a round, it immediately uses the
    first skill in its list that has `迅捷`
  - this occurs before the round then proceeds normally
  - it requires active switching, not replacement after the current mon dies
  - only one `迅捷` skill triggers
  - the user must have enough energy, or `迅捷` does not fire
- `疾风连袭` is described as a way to leverage all previously used swift skills.
- `翼王` is cited as a key example because its trait can give `迅捷` to shared
  skills with another wing ally.
- `风墙` is highlighted as special because it has `迅捷`, allowing immediate
  defensive value on active switch.

Review note:

- This is an especially important candidate for a reviewed mechanics page.
- Current B wiki does not yet contain a reviewed `迅捷` / wing timing page.

### 萌

Explicit claims:

- Cute centers on `萌化`.
- `萌化` means regression / de-evolution.
- After regression:
  - six-dimensional stats decrease
  - trait changes to the earlier-form trait
- Cute users can gain extra benefits from self-regression.
- The tutorial explicitly says some old beta/public-test tools are now gone or
  changed, and old one-turn wipe patterns are weaker now.
- Current framing is more:
  - targeted counterplay
  - utility support
  - buff-transfer support

Interpretation note:

- Cute is framed as controlled self-weakening with special compensation, not
  just raw stat loss.

### 幽

Explicit claims:

- Ghost targets energy.
- Ghost has many energy-reduction tools.
- Ghost has burst when the enemy energy is `0`, including a cited `20x` damage
  clause.
- Ghost has `降灵印记`.
- `降灵印记`: if the current on-field species leaves actively, the incoming
  replacement loses `1` energy per layer.
- The tutorial explicitly distinguishes active leave from replacement after
  death.

Interpretation note:

- Ghost is framed as energy denial plus active-switch punishment.

### 恶

Explicit claims:

- Evil has many lifesteal tools.
- Evil also centers on exchange:
  - swap buffs / debuffs
  - swap HP
  - even swap the two sides' entire move sets
- The tutorial says the family is still under development and does not explain
  much more.

Interpretation note:

- Evil is framed as drain plus exchange manipulation.

### 机械

Explicit claims:

- Machine centers on `传动`.
- Tutorial explanation of `传动`:
  - move downward / swap with the lower skill slot
- Machine skills have strong support value.
- `轴承支撑`: passively reduces the cost of adjacent skills by `1`.
- `啮合传递`: costs `1`, grants `+80` speed; if in slot `1` or `3`, it also
  grants `+60%` physical attack.
- `齿轮扭矩`: gains permanent power each time position changes.
- `钢铁洪流`: when in slot `1`, becomes a high-power efficient attack.

Interpretation note:

- Machine is framed as positional support, ramp, and slot-engine synergy.

### 幻

Explicit claims:

- Illusion centers on `星陨印记`.
- `星陨印记` is a detonation-style mark.
- When a non-illusion attacking move is used, it can detonate the target's
  starfall stacks.
- On detonation, damage is dealt and the consumed starfall stacks are cleared.
- Illusion also has moves such as `多维击打` that scale from starfall stacks
  without detonating them.
- Therefore illusion has two kill routes:
  - detonate marks
  - keep marks and use stack-scaling attacks

Interpretation note:

- Illusion is framed as stored burst or persistent stack-scaling.

## Gaps And Follow-Up Targets

The tutorial is very valuable for mechanism vocabulary, but several claims still
need formal review before they should become default doctrine.

High-priority review targets:

1. `迅捷`
2. `传动`
3. `迸发`
4. active leave vs death replacement wording
5. status vs mark persistence taxonomy
6. exact weather rules and timers
7. whether all same-type immunities described here remain stable

Suggested reviewed-page targets:

```text
wiki/pages/mechanics/speed_priority_and_swift.md
wiki/pages/mechanics/switch_persistence.md
wiki/pages/mechanics/weather_and_field_effects.md
wiki/pages/mechanics/type_bloodline_move_boundary.md
wiki/pages/mechanics/marks_and_persistence.md
wiki/pages/mechanics/response_counterplay.md
```

## PM / Review Warnings

- Do not quote this note as direct game truth without A-layer or PM review.
- Do not silently merge beta-history statements with current public mechanics.
- Do not let the agent explain `迅捷`, `传动`, `迸发`, or `萌化` as confirmed
  if no reviewed mechanism page exists.
- Do not import Pokemon assumptions into any of these type families.
