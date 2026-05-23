# P14 S2 A-layer Overlay Snapshot PM Packet

## 结论
- 已冻结 S1 Battle Dex，并生成 S2 candidate-only A-layer overlay。
- 没有修改 `data/runtime/battle_dex.sqlite`，没有 runtime promotion、Gold auto-accept、reviewed graph materialization。
- runtime DB 前后 hash 一致：True。
- S2 reconciliation unresolved/non-dex items：0。
- `水刃` 已按应对状态附加效果处理：True; 不是 base energy_cost 变更。

## Decision Table
| Decision | Recommendation | Why | Forbidden Follow-through |
|---|---|---|---|
| Accept S1 freeze | Accept | runtime DB 与冻结副本 hash 一致：True | 不代表切换 runtime DB |
| Accept S2 overlay as reference surface | Accept candidate-only | unresolved/non-dex=0，且 official/patch/reconciliation/base refs 都 hashable | 不得写回 `data/runtime/battle_dex.sqlite` |
| Let Phase48/Phase49 candidates cite overlay | Accept with blocker | can_reference=True，只作为 versioned A-layer reference | 不得解除 runtime/Gold/review blocker |
| Promote S2 A-layer to production | Reject for this run | 本包没有构建 runtime DB，也没有 PM promotion audit | 不得 runtime promotion |
| Auto-accept Gold/reviewed graph | Reject | 本包只处理 A-layer candidate overlay，不处理 Gold 或 graph card review | 不得 Gold auto-accept / graph materialization |

## 文件
- S1 snapshot manifest: `data/runtime/snapshots/s1_2026-05-20/manifest.yaml`
- S1 frozen DB copy: `data/runtime/snapshots/s1_2026-05-20/battle_dex.sqlite`
- S2 overlay: `data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/overlay.yaml`
- S2 overlay manifest: `data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/manifest.yaml`
- Reconciliation summary: `data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/reconciliation_summary.yaml`
- Dashboard: `data/knowledge_graph/v0/eval/quality_dashboard_s2_a_layer_overlay_snapshot_2026-05-23.yaml`
- Validation evidence: `data/knowledge_graph/v0/a_layer_overlays/s2_2026-05-21/validation_evidence.yaml`

## S1 Freeze 证明了什么
- 当前 runtime DB hash：`76976d3f22f3fba8e55408bd098bbc0a5f8f9b9a81c7338706bd5cff60eb8543`。
- 冻结副本 hash：`76976d3f22f3fba8e55408bd098bbc0a5f8f9b9a81c7338706bd5cff60eb8543`。
- 两者 byte-identical；S1 作为历史 baseline 保留，不代表切换 runtime。

## S2 Overlay 包含什么
- stat overlays：25。
- ability overlays：10。
- move-pool additions：26。
- move-effect overlays：30。
- wording updates：7。
- B-layer mechanism concept routes：1。

## 仍然禁止
- 禁止把 overlay 写回 `data/runtime/battle_dex.sqlite`。
- 禁止把 overlay 当作 production A-layer truth。
- 禁止由此自动放行 Gold、reviewed graph card、runtime answer。
- 先手/先手度这类被路由到 B-layer 的概念仍需要机制规则复审。

## PM 判断
- Phase48/Phase49 candidate-only items 可以引用这个 S2 overlay surface：True。
- 它们只能用来解释为什么 S2 受影响候选继续 blocked，不能据此进入 reviewed/runtime。
- 真正 S2 runtime DB promotion 之前，还需要 PM review、版本化 runtime/A-layer DB 构建、回归测试和 promotion audit。

## Validation
- status: `p14_validator_tests_hash_checks_passed`
- note: Required S2 reconciliation rerun passed with unresolved_or_non_dex_items=0; P14 strict validator passed; required Battle Dex/P14/focused tests passed; runtime DB and S1 snapshot hashes are byte-identical; graph validator intentionally not run because no graph materialization.
