# Phase 1 Dual-Type Rule Change Specification

## Title

Phase 1 双属性承伤规则变更执行规范

## Purpose

本规范用于指导对 Phase 1 队伍联防结构分析系统进行一次 breaking change：将当前双属性承伤计算从“标准乘算假设”切换为当前项目暂时接受的 `洛克王国世界` 规则基线。

该变更的目标是让 Phase 1 的结构分析与当前内部领域认知保持一致，并避免在错误的双属性规则上继续实现 CLI 与评分逻辑。

## Executor / Intended User

执行者：本项目的实现负责人（Codex / 工程执行者）。

假设能力：

- 可读写本仓库文件
- 可修改 Python 实现与测试
- 可更新内部 specs、contracts 与 log
- 可运行本地测试

## Scope

本变更覆盖：

1. 将双属性承伤规则改为：
   - 双重克制 `×3`
   - 双重抵抗 `÷3`
   - 克制与抵抗相消 `×1`
2. 更新与该规则相关的内部文档
3. 更新运行时数据和实现逻辑
4. 更新测试与样例

## Non-goals

本变更不包括：

- 重新验证全部 PvP 机制
- 引入精灵数据库
- 引入 Meta 数据
- 实现 Phase 2 或 Phase 3 能力
- 重新设计 role/archetype taxonomies

## Definitions and Assumptions

### Definitions

- `旧规则`：当前本地实现中对双属性承伤采用逐属性乘算的规则
- `新规则`：当前项目暂时接受的双属性承伤规则：
  - `2x + 2x => 3.0`
  - `0.5x + 0.5x => 0.333...`
  - `2x + 0.5x => 1.0`
- `Phase 1`：仅基于属性关系的队伍联防结构分析

### Assumptions

1. 新规则当前来源于已审查的外部研究与 `v2` 外部数据，已被内部 `domain_primer` 接受为 `Provisional mechanism`
2. 虽然该规则仍可能在未来被更高可信证据推翻，但在当前项目阶段必须优先保证内部一致性
3. 本变更应被视为 breaking change，而不是普通修补

## Inputs / Preconditions

### Mandatory Inputs

- [docs/domain_primer.md](/Users/okfin3/project/GitHub/OKFin33/Roco/docs/domain_primer.md)
- [specs/scoring_system.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/scoring_system.md)
- [specs/change_policy.md](/Users/okfin3/project/GitHub/OKFin33/Roco/specs/change_policy.md)
- [data/roco_world_type_chart.json](/Users/okfin3/project/GitHub/OKFin33/Roco/data/roco_world_type_chart.json)
- [data/reference/luoke_world_type_database_v2.json](/Users/okfin3/project/GitHub/OKFin33/Roco/data/reference/luoke_world_type_database_v2.json)
- [roco_world_model.py](/Users/okfin3/project/GitHub/OKFin33/Roco/roco_world_model.py)
- existing tests under [tests](/Users/okfin3/project/GitHub/OKFin33/Roco/tests)

### If Inputs Conflict

- Internal canonical docs take priority over raw external research
- The external `v2` database may be used to justify the new rule, but the internal adopted statement in `docs/domain_primer.md` is the actual project baseline

## Workflow / Required Process

### Stage 1: Update Internal Specs

Objective:

Make the rule change explicit at the spec layer before code changes.

Actions:

1. Update `specs/scoring_system.md` so Phase 1 no longer assumes multiplicative dual-type combination
2. If needed, update any spec text that implies multiplicative combination
3. Ensure examples match the new rule

Intermediate Outputs:

- updated scoring spec

Quality Criteria:

- no Phase 1 text may imply `×4` or `×0.25`
- the rule must be stated in exact terms, not vague prose

### Stage 2: Update Runtime Data and Model Contract

Objective:

Align the executable model with the new accepted rule.

Actions:

1. Update or replace local type data usage as needed
2. Update runtime calculation logic in `roco_world_model.py`
3. If required, add a dedicated helper for dual-type combination rather than reusing multiplication directly

Intermediate Outputs:

- updated runtime logic

Quality Criteria:

- single-type logic must remain unchanged
- dual-type outputs must reflect the new rule

Good example:

- `火` attacking `草/机械` yields `3.0`

Bad example:

- leaving dual-type logic as `2.0 * 2.0 = 4.0`
  - failure: the Engine would remain inconsistent with the current internal domain baseline

### Stage 3: Update Tests and Fixtures

Objective:

Prevent regression and prove the new rule is active.

Actions:

1. Update existing dual-type tests
2. Add explicit tests for:
   - double super effective
   - double resisted
   - super effective + resisted cancellation
3. Update any labels or expected outputs affected by the score change

Intermediate Outputs:

- updated passing tests

Quality Criteria:

- at least one test for each dual-type rule case
- no remaining test should encode the old multiplicative assumption

### Stage 4: Update Project Log

Objective:

Record the breaking change for future sessions and reviews.

Actions:

1. Append a note to the project log that the provisional dual-type rule was operationalized
2. Record which files changed
3. Record any remaining uncertainties

Intermediate Outputs:

- updated log entry

Quality Criteria:

- future readers can understand when the runtime stopped using multiplicative dual-type logic

## Tool / Resource Policy

- Use local repo files as the main evidence base
- Do not re-open broad external research unless a specific contradiction blocks execution
- Use tests as the conformance check, not as the source of truth

## Output Contract

Execution of this change is complete only if the following are all true:

1. Internal specs reflect the new rule
2. Runtime logic reflects the new rule
3. Tests reflect and verify the new rule
4. The project log records the transition
5. The final implementation note clearly states:
   - what changed
   - why it changed
   - what still remains provisional

## Quality Bar / Success Criteria

- The project is internally consistent after the change
- Phase 1 calculations no longer depend on the old multiplicative assumption
- The change remains isolated to Phase 1 concerns
- Remaining uncertainty is documented instead of hidden

## Failure Modes and Recovery

### External Failures

- If future evidence disproves the `×3 / ÷3` rule:
  - treat that as a new breaking change
  - do not silently hotfix runtime logic

### Judgement Dilemmas

- If the runtime API needs to preserve old method names while changing semantics:
  - preserve names when possible
  - document the semantic change clearly

### Structural Failures

- If specs are updated but runtime still computes multiplicatively:
  - the change is incomplete
- If runtime changes but tests still encode old expectations:
  - the change is incomplete

## Escalation / Handoff Rules

- Stop and escalate only if internal specs materially contradict each other after the update
- If implementation can proceed but evidence confidence remains provisional, proceed and document the risk rather than blocking the project

## Evaluation Checklist

- Was the change treated as breaking?
- Were specs updated before implementation?
- Does runtime now produce `×3 / ÷3 / ×1` for the relevant dual-type cases?
- Were tests updated and passed?
- Was the change recorded in the project log?
