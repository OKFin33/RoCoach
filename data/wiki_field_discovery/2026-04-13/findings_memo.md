# Wiki Field Discovery Memo

## Status

- Scope: `P1a` reconnaissance only
- Database ingestion: not performed
- Run timestamp: `2026-04-13T15:56:07+00:00`
- API base: `https://wiki.biligame.com/rocom/api.php`

## Sample Coverage

| Entity | Page Type | Count |
| --- | --- | ---: |
| ability | ability_embedded_species_detail | 9 |
| move | move_detail | 8 |
| move | move_index | 2 |
| species | species_detail | 9 |
| species | species_index | 4 |

## Page-Structure Findings

- `species`: `分类:精灵` exists and sampled detail pages expose structured `{{精灵信息}}` template fields.
- `move`: `分类:技能` exists and sampled detail pages expose structured `{{技能信息}}` template fields.
- `ability`: no standalone `特性图鉴` / `特性列表` / `特性` page or `分类:特性` category was found in this pass; ability evidence is embedded in species `{{精灵信息}}` fields `特性` and `特性描述`.
- Index pages use structured SMW `#ask` projections and filter templates; these are useful for discovery but are not the primary detail-source layer.

## Candidate Field Recommendations

### confirmed

| Entity | Field | Coverage | Examples | Notes |
| --- | --- | ---: | --- | --- |
| ability | 特性 | 9/9 | 惊吓<br>茶多酚<br>助燃 | Repeated structured field with direct battle-analysis relevance. |
| ability | 特性描述 | 9/9 | 能量等于0的精灵，无法对自己造成伤害。<br>离场后，更换入场的精灵回复20%生命且免疫寄生。<br>使用火系技能后，获得双攻+20%。 | Repeated structured field with direct battle-analysis relevance. |
| move | 威力 | 8/8 + 2 index | 0<br>70<br>85 | Repeated structured field with direct battle-analysis relevance. |
| move | 属性 | 8/8 + 2 index | 草<br>幽<br>恶 | Repeated structured field with direct battle-analysis relevance. |
| move | 技能名称 | 8/8 + 2 index | 孢子<br>报复<br>暗突袭 | Repeated structured field with direct battle-analysis relevance. |
| move | 技能类别 | 8/8 + 2 index | 状态<br>防御<br>物攻 | Repeated structured field with direct battle-analysis relevance. |
| move | 效果 | 8/8 + 1 index | 敌方获得1层寄生。<br>减伤70%，应对攻击：敌方失去3能量。<br>造成物伤，吸血50%，应对状态：本次技能威力翻倍。 | Repeated structured field with direct battle-analysis relevance. |
| move | 耗能 | 8/8 + 2 index | 3<br>2<br>4 | Repeated structured field with direct battle-analysis relevance. |
| species | 2属性 | 9/9 + 3 index |  | Repeated structured field with direct battle-analysis relevance. |
| species | 主属性 | 9/9 + 3 index | 幽<br>水<br>火 | Repeated structured field with direct battle-analysis relevance. |
| species | 可学技能石 | 9/9 | 力量吞噬,吓退,引燃,掠夺,摇篮曲,操控,暗箱操作,流火,激怒,热身,穿膛,精神扰乱,贪婪,黑手<br>力量吞噬,吓退,引燃,掠夺,摇篮曲,操控,暗箱操作,栽赃,流火,激怒,热身,穿膛,精神扰乱,贪婪<br>力量增效,复写,天洪,水幕冲击,水炮,水环,突袭,蓄水,血气,许愿星,阻断,魔法增效 | Repeated structured field with direct battle-analysis relevance. |
| species | 技能 | 9/9 | 防御,鬼火,勾魂,许愿星,取念,幽灵爆发,聒噪,报复,背袭,嘲弄,恐吓,降灵,恶作剧<br>水弹,洗礼,防御,落星,泡沫,泡沫幻影,肥皂泡,潮涌,水刃<br>猛烈撞击,火苗,力量增效,火焰切割,防御,吹火,晒太阳,怒火,持续高温,火云车,热身,闪燃,山火 | Repeated structured field with direct battle-analysis relevance. |
| species | 技能解锁等级 | 9/9 | 1,1,5,10,11,16,21,27,34,35,39,40,45<br>1,1,1,6,9,16,27,32,36<br>1,1,6,8,10,12,17,21,29,30,36,42,48 | Repeated structured field with direct battle-analysis relevance. |
| species | 物攻 | 9/9 | 40<br>30<br>26 | Repeated structured field with direct battle-analysis relevance. |
| species | 物防 | 9/9 | 78<br>83<br>75 | Repeated structured field with direct battle-analysis relevance. |
| species | 特性 | 9/9 | 惊吓<br>茶多酚<br>助燃 | Repeated structured field with direct battle-analysis relevance. |
| species | 特性描述 | 9/9 | 能量等于0的精灵，无法对自己造成伤害。<br>离场后，更换入场的精灵回复20%生命且免疫寄生。<br>使用火系技能后，获得双攻+20%。 | Repeated structured field with direct battle-analysis relevance. |
| species | 生命 | 9/9 | 74<br>84<br>81 | Repeated structured field with direct battle-analysis relevance. |
| species | 精灵名称 | 9/9 + 3 index | 暗影灵面<br>果冻<br>火花 | Repeated structured field with direct battle-analysis relevance. |
| species | 精灵形态 | 9/9 + 3 index | 原始形态<br>地区形态 | Repeated structured field with direct battle-analysis relevance. |
| species | 精灵阶段 | 9/9 + 3 index | Ⅱ阶<br>Ⅰ阶<br>最终形态 | Repeated structured field with direct battle-analysis relevance. |
| species | 血脉技能 | 9/9 | 休息回复,诋毁,升龙咆哮,麻痹,化劲,火焰箭,灵媒,徒长,霜降,假寐,虹光冲击,啮合传递,甜心续航,超维投射,泥浆铠甲,毒孢子,蓄水,羽化加速<br>防反,等价交换,升龙咆哮,集中,反击拳,火焰护盾,虚化,蜡质膜,雪替身,掩护,虹光冲击,离子震荡,魅惑,冥想,淤泥表皮,毒沼,水弹枪,羽翼庇护<br>星星撞击,恶能量,升龙咆哮,球状闪电,缠丝劲,火焰箭,灵媒,花香,冰爪,噬心,透射,械斗,碰爪,星云漩涡,跺地,毒沼,泡沫,鹰爪 | Repeated structured field with direct battle-analysis relevance. |
| species | 速度 | 9/9 | 92<br>96<br>78 | Repeated structured field with direct battle-analysis relevance. |
| species | 魔攻 | 9/9 | 96<br>81<br>37 | Repeated structured field with direct battle-analysis relevance. |
| species | 魔防 | 9/9 | 108<br>88<br>78 | Repeated structured field with direct battle-analysis relevance. |

### provisional

| Entity | Field | Coverage | Examples | Notes |
| --- | --- | ---: | --- | --- |
| move | 技能序号 | 0/8 + 2 index |  | Observed field without enough current policy to promote or forbid. |
| move | 技能版本 | 8/8 + 1 index | 0.1 | Observed as structured data, but semantic mapping or optionality needs review. |
| move | 描述 | 8/8 |  | Observed as structured data, but semantic mapping or optionality needs review. |
| move | 筛选项 | 0/8 + 2 index | 查看全部, 物攻, 魔攻, 防御, 状态 | Index filter metadata; useful for page-structure discovery, not a domain field by itself. |
| species | 地区形态名称 | 9/9 + 3 index | 睁眼的样子<br>闭眼的样子 | Observed as structured data, but semantic mapping or optionality needs review. |
| species | 属性 | 0/9 + 3 index |  | Observed field without enough current policy to promote or forbid. |
| species | 序号 | 0/9 + 3 index |  | Observed field without enough current policy to promote or forbid. |
| species | 筛选项 | 0/9 + 1 index | 查看全部, Ⅰ阶, Ⅱ阶, 最终形态, 地区形态 | Index filter metadata; useful for page-structure discovery, not a domain field by itself. |
| species | 精灵初阶名称 | 9/9 | 小灵面<br>果冻<br>火花 | Observed as structured data, but semantic mapping or optionality needs review. |
| species | 精灵编号 | 0/9 + 3 index |  | Observed field without enough current policy to promote or forbid. |

### forbidden_by_default

| Entity | Field | Coverage | Examples | Notes |
| --- | --- | ---: | --- | --- |
| species | 体型 | 9/9 | 0.75~0.86<br>0.3~0.36<br>0.53~0.71 | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |
| species | 分布地区 | 9/9 | 常见于城镇周边<br>行踪神秘<br>岚语峰西侧 / 乌黑巷 / 叽叽喳喳台地 / 商店街周边 / 奥贝斯坦湖 / 学院驻地 / 岚语峰 / 挽风屏障 / 月牙湖岸 / 月牙镇 / 皇家办事处 / 聆风塔地 / 聆风镇 / 轻风山 / 风眠圣所 | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |
| species | 图鉴课题 | 9/9 | 捕捉1只精灵,捕捉1只了不起天分的精灵,使精灵成功进化1次,确认2种不同样子的暗影灵面<br>捕捉1只精灵,捕捉1只了不起天分的精灵,使精灵成功进化1次<br>捕捉1只精灵,捕捉1只了不起天分的精灵,使迪莫的亲密度等级达到5级,获得「命定勇者」奖牌,使用1次闪光,使用1次光刃 | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |
| species | 宠物立绘形态 | 9/9 + 3 index |  | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |
| species | 是否有异色 | 9/9 + 3 index | 否 | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |
| species | 是否有错别字 | 1/9 |  | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |
| species | 更新版本 | 8/9 | 0.6 | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |
| species | 精灵描述 | 9/9 | 被两团冷火环绕着，从头到脚都充满了谜团。进食之后重量也毫不增加，被它面具下的嘴吞下的食物仿佛消失了一样。<br>常在空中徘徊，来去几乎无声，靠近它时会明显感觉变冷，像是体表的温度不断地被抽走。它们不进食也不说话，面具上闭着的眼睛图案似乎代表着什么。<br>透明而不起眼的精灵，经常在干净的水源被发现。研究发现，果冻精灵可以维护森林、湖泊和山脉的生态平衡，似乎是因为它们能让水变得清澈。 | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |
| species | 精灵类型 | 9/9 | 假面精灵<br>凝胶精灵<br>火元素精灵 | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |
| species | 课题技能石 | 9/9 | -<br>光刃,闪光<br>龙血 | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |
| species | 进化条件 | 8/9 | 时间为夜晚进化<br>时间为中午进化<br>无法进化 | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |
| species | 重量 | 9/9 | 0.12~1.16<br>4.35~5.6<br>7.6~8.5 | Observed but outside current battle-analysis scope or cosmetic/provenance-only. |

## Negative Assumption Guardrails

- `move.accuracy`: `forbidden_by_default`. No sampled `技能信息` template exposed accuracy / 命中 fields.
- `move.pp`: `forbidden_by_default`. No sampled `技能信息` template exposed PP / usage-count fields.
- `move.cooldown`: `forbidden_by_default`. No sampled `技能信息` template exposed a stable cooldown field.
- `ability.numeric_modifier`: `forbidden_by_default`. Numeric modifiers appear only inside raw effect text in this pass, not as a stable structured ability field.

## Ingestion Risks

- `ability` is not currently a standalone page type; treating it as an entity requires deriving ability records from species fields unless a stronger source is found.
- `species` form semantics need review: `精灵形态` and `地区形态名称` are separate raw labels and should not be merged blindly.
- `move` has stable `耗能` and `威力`, but no sampled field supports imported assumptions like accuracy or PP.
- Cosmetic and encyclopedia fields are visible in structured species pages; they must remain excluded from the battle schema unless a battle use case is proven.

## Proposed Next Step

Use the aggregate artifact to update `specs/field_alignment_matrix.yaml` only where recommendations are evidence-backed. Do not start production ingestion until move/ability entity modeling is explicitly approved.
