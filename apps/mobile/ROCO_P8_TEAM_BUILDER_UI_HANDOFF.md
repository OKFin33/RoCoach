# Roco P8 Team Builder UI Handoff

Date: 2026-04-28

This handoff records the current Team Builder UI state after the latest RN
optimization pass. It is intended for backend/app implementers who need to
continue from the current Expo RN implementation without reconstructing product
decisions from chat history.

## Product Boundary

`队伍设置` is an authorized Settings drawer entry. It is a roster/context setup
surface for the single Agent Chat product, not a separate Team Analyze tool, Dex,
Calculator, Species page, or multi-function app route.

The Chat main screen should not show an active team chip. The saved team context
is sent silently with chat requests through `context_attachments`.

## Active Files

- `mobile/src/components/roco/TeamContextBuilder.tsx`
- `mobile/src/components/roco/SettingsDrawer.tsx`
- `mobile/src/screens/ChatScreen.tsx`
- `mobile/src/api/types.ts`
- `api/contracts.py`
- `advisor/contracts.py`
- `advisor/battle_dex.py`
- `tests/test_api.py`

The Team Builder component currently lives under `mobile/src/components/roco`.
If this file appears untracked in git status, it still is the active component
imported by the current Settings drawer implementation.

## Current UX

Settings drawer home exposes `队伍设置`.

Inside Team Builder:

- Header title: `默认编队`.
- Description: `教练可以直接根据你的编队提供建议`.
- Team slots render as a stable `2 x 3` grid.
- Each slot is selected from database search results only; no free structured
  species entry.
- Search opens from a small feather pen button next to the selected slot/species.
- Search input auto-runs after a short debounce. There is no manual Search
  button.
- Search rule copy under the input:
  `搜索规则：精灵名或其初始形态带有搜索关键词`
- Search remains name-based. It does not filter by type/attribute.

Species result display:

- If `regional_form_name` exists, display `display_name（regional_form_name）`.
- Otherwise display `display_name`.
- Result metadata shows initial species, form name, and type line.
- Selected slot stores this public display label, but backend identity remains
  `species_id`.

Example:

```text
皇家狮鹫（崖间地的样子）
初始形态 小狮鹫(崖间地的样子) · 原始形态 · 翼

皇家狮鹫（高山地的样子）
初始形态 小狮鹫(高山地的样子) · 地区形态 · 翼
```

## Species Search Contract

Mobile calls:

```text
GET /species/search?q=<query>&limit=12
```

Backend search source:

```text
data/runtime/battle_dex.sqlite
table: species_form
```

Search fields:

- `species_id = query`
- `display_name = query`
- `initial_species_name = query`
- `display_name LIKE %query%`
- `initial_species_name LIKE %query%`

Current search does not include:

- `primary_type = query`
- `secondary_type = query`

Required search result fields:

```ts
type SpeciesSearchItem = {
  species_id: string;
  display_name: string;
  initial_species_name?: string | null;
  form_name?: string | null;
  regional_form_name?: string | null;
  primary_type: string;
  secondary_type?: string | null;
};
```

Reason: same-name species can differ by region/form, stats, type, or appearance.
The UI must let the user distinguish them before selection.

## Team Slot Rules

Each selected species slot stores:

- `species_id`: backend structured identity.
- `display_name`: public UI label, potentially disambiguated with region.
- `primary_type`, `secondary_type`: copied from backend result/profile.
- `fixed_ability`: copied from backend profile; user does not manually choose it.
- `nature`: selected through constrained nature UI.
- `individual_value_bonuses`: up to 3 rows.
- `selected_moves`: up to 4 moves from that species' backend move pool.

Backend revalidates selected species and moves when chat context is submitted.

## Nature UI

The nature selector is mobile-game style, not a free text input.

Visible layout:

```text
[ + 属性 ] [ 性格名 ] [ - 属性 ]
```

Any of the three fields can drive the selection:

- Selecting a nature name updates plus/minus attributes.
- Selecting plus or minus attribute resolves to a valid mobile-game nature
  combination.
- There is no `无` nature option. Mobile Roco World does not use the old web-game
  neutral nature model.

Current nature database is static in `TeamContextBuilder.tsx`. It matches the
provided Roco World mobile nature chart and includes the 30 current natures.
If backend later stores natures, replace the local constant with API data while
preserving the same UI contract.

Current stat labels:

```text
hp      -> 生命
atk     -> 物攻
spa     -> 魔攻
defense -> 物防
spd     -> 魔防
spe     -> 速度
```

Do not show `HP`, `精力`, or `体力` in UI.

## Individual Value UI

The IV bonus editor has exactly three visible rows. Each row has:

- Left field: stat selector.
- Right small numeric field: value selector.

The stat selector may choose `无`, because Team Builder supports 0..3 IV bonus
rows. This is not the same as neutral nature.

Value selector options:

```text
7, 8, 9, 10
```

Value selector subtitle:

```text
填入初始个体即可，PvP 系统会自动调整数值
```

## Move UI

Moves render as a `2 x 2` list.

One feather pen button opens the move editor. The move editor shows a larger
centered `2 x 2` grid. Tapping a cell chooses which slot to edit. Search filters
the selected species' backend move pool. Moves must come from:

```text
GET /species/{species_id}/moves?limit=200
```

Do not allow free structured move entry.

## Copy And Visual Rules

Keep these copy decisions:

- `默认编队`
- `教练可以直接根据你的编队提供建议`
- `搜索规则：精灵名或其初始形态带有搜索关键词`
- `填入初始个体即可，PvP 系统会自动调整数值`

Current visual pattern:

- Cream paper/card surfaces.
- Black ink border.
- Yellow highlight for active slot/selected row.
- Small black circular feather pen buttons.
- Compact mobile density; no large explanatory paragraphs.

## Validation Performed

Commands run after this optimization pass:

```bash
cd mobile && npm run typecheck
.venv/bin/python -m unittest tests.test_api
```

Results:

- Mobile typecheck passed.
- API tests passed, including regression coverage that `/species/search?q=皇家狮鹫`
  exposes both `崖间地的样子` and `高山地的样子`.

## Known Open Items

- Android visual QA remains open.
- iOS visual QA should re-check the Team Builder after the latest nature/search
  refinements.
- Nature data is currently local static UI data. If backend adds a nature table,
  migrate it behind the same UI behavior.
- Species search deliberately remains name/initial-name based. Attribute search
  is a future product decision, not part of this pass.
