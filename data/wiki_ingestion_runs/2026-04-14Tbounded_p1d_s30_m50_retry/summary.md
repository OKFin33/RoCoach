# P1d Wiki Battle Dex Dry-Run Summary

- Run ID: `2026-04-14Tbounded_p1d_s30_m50_retry`
- Output directory: `/Users/okfin3/project/GitHub/OKFin33/Roco/data/wiki_ingestion_runs/2026-04-14Tbounded_p1d_s30_m50_retry`
- Status: `completed_with_warnings`
- Database mutation: not performed

## Artifact Counts

- `ability_conflicts`: 0
- `derived_ability_candidates`: 15
- `move_candidates`: 50
- `raw_template_snapshots`: 80
- `rejected_fields`: 326
- `source_pages`: 80
- `species_form_candidates`: 30
- `species_move_pool_candidates`: 1288
- `unresolved_move_names`: 285
- `validation_events`: 1281

## Validation Summary

- `hard_reject`: 0
- `warning`: 1281
- `info`: 0

### By Code

- `empty_description_text`: 50
- `missing_ability_text`: 3
- `missing_optional_field`: 3
- `move_name_unresolved`: 1225

## Unresolved Move Names

- 一拳
- 三连破
- 主场优势
- 二律背反
- 仙人掌刺击
- 以重制重
- 休息回复
- 伪造账单
- 伺机而动
- 俯冲猛击
- 借用
- 倾泻
- 假寐
- 偷袭
- 充分燃烧
- 先发制人
- 光刃
- 光合作用
- 光能聚集
- 冥想
- 冲撞
- 冷风
- 击鼓传花
- 刺盾
- 刺藤
- 剧毒
- 力量吞噬
- 力量增效
- 加固
- 勾魂
- 化劲
- 升龙咆哮
- 午夜噪音
- 压扁
- 反击拳
- 取念
- 叠势
- 叶绿光束
- 后发制人
- 吓退
- 吞噬
- 啮合传递
- 噬心
- 四维降解
- 回旋踢
- 回旋风暴
- 地刺
- 地陷
- 地震
- 垂死反击

## Ability Conflicts

- None

## Failure Reason

- None

## Recommended Next Action

- Parse-validate all artifacts.
- Review unresolved move names before any SQLite ingestion.
- Keep this run bounded until P1d acceptance criteria are met.
