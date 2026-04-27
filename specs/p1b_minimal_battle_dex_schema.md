# P1b Minimal Battle Dex Schema Spec

## Purpose

Define the minimum database schema for the first battle-relevant dex ingestion.

This spec converts `P1a` field discovery into a storage contract. It does not authorize a full crawl by itself; it defines what a future crawler is allowed to output and what the importer is allowed to persist.

## Position In The Workflow

`P1` is the pre-ingestion preparation phase.

- `P1a`: discover source page structures and candidate fields
- `P1b`: define the minimal battle dex schema
- `P1c`: define crawler output and cleaning contracts
- `P1d`: run a bounded ingestion dry-run before full ingestion

## Source Basis

Authoritative inputs:

- `specs/field_alignment_matrix.yaml` version `2`
- `docs/wiki_field_discovery_review_2026-04-13.md`
- `docs/combat_ontology.md`
- `docs/domain_primer.md`

Key source facts:

- species detail pages expose `{{精灵信息}}`
- move detail pages expose `{{技能信息}}`
- ability currently has no confirmed standalone wiki page type
- ability evidence is embedded in species fields `特性` and `特性描述`

## Design Principles

Raw-first:

- persist game-native source labels before semantic reinterpretation
- avoid renaming source stats into foreign-game abbreviations in stored raw fields

Source-traceable:

- every persisted record must retain page-level provenance
- derived records must retain their source record references

Engine-friendly:

- storage may preserve source channels, but Engine-facing views should expose simple battle concepts
- the first Engine-facing move pool should be the union of all theoretically available moves

Assumption-hostile:

- no `accuracy`
- no `PP`
- no raw `cooldown`
- no Pokemon-style category enum
- no standalone ability source unless later evidence proves one exists

## Entity Model

### `source_page`

Purpose:

- record where extracted data came from

Fields:

- `source_page_id`: local stable ID
- `entity_hint`: `species|move|ability_embedded|unknown`
- `page_title`: wiki page title
- `page_url`: wiki page URL
- `revision_id`: wiki revision ID if available
- `fetched_at`: crawl timestamp
- `content_sha256`: hash of fetched source content
- `parser_version`: local parser version

Notes:

- this table is required for diffing and trust review
- never overwrite source trace during cleaning

### `raw_template_snapshot`

Purpose:

- preserve the raw structured template fields used for extraction

Fields:

- `snapshot_id`: local stable ID
- `source_page_id`: FK to `source_page`
- `template_name`: `精灵信息|技能信息|unknown`
- `raw_fields`: JSON object preserving original field labels and values
- `extraction_warnings`: string array

Notes:

- this is the escape hatch when normalized schema is wrong
- storing raw fields avoids repeating expensive wiki fetches during schema refinement

### `species_form`

Purpose:

- represent a battle-usable species/form record

Fields:

- `species_id`: local stable ID
- `display_name`: from `精灵名称`
- `initial_species_name`: from `精灵初阶名称`, nullable
- `form_name`: from `精灵形态`, nullable
- `regional_form_name`: from `地区形态名称`, nullable
- `evolution_stage`: from `精灵阶段`, nullable
- `primary_type`: from `主属性`
- `secondary_type`: from `2属性`, nullable
- `base_stats`: object with game-native dimensions:
  - `生命`
  - `物攻`
  - `魔攻`
  - `物防`
  - `魔防`
  - `速度`
- `ability_name`: from `特性`, nullable
- `ability_effect_text`: from `特性描述`, nullable
- `source_page_id`: FK to `source_page`
- `confidence`: `confirmed|provisional`

Identity rule:

- `species_id` must distinguish forms when type, stats, ability, or move pool can differ
- do not collapse `精灵名称`, `精灵形态`, `地区形态名称`, and `精灵初阶名称` into one field

### `move`

Purpose:

- represent a battle action record
- keep the canonical move entity separate from acquisition evidence such as skill-stone pages

Fields:

- `move_id`: local stable ID
- `move_name`: from `技能名称`
- `move_type`: from `属性`
- `category_raw`: from `技能类别`
- `power`: from `威力`, nullable integer
- `energy_cost`: from `耗能`, nullable integer
- `effect_text`: from `效果`
- `description_text`: from `描述`, nullable
- `source_version`: from `技能版本`, nullable
- `source_page_id`: FK to `source_page`
- `confidence`: `confirmed|provisional`

Allowed `category_raw` values observed so far:

- `状态`
- `防御`
- `物攻`
- `魔攻`

Forbidden raw fields:

- `accuracy`
- `pp`
- `cooldown`

Mechanics note:

- defense skill reuse/cooldown behavior is a mechanics rule, not a confirmed raw wiki field
- a page title such as `技能石/光刃` is not a separate battle move entity; it is evidence for learning canonical move `光刃`
- when available, canonical move semantics must come from `{{技能信息}}`

### `derived_ability`

Purpose:

- optional local table derived from embedded species ability fields

Fields:

- `ability_id`: local generated ID
- `ability_name`: from species `特性`
- `effect_text`: from species `特性描述`
- `source_species_ids`: species records that exposed this ability
- `derivation_status`: `single_source|merged_consistent|conflict_review_required`
- `confidence`: `confirmed|provisional`

Rules:

- this table is derived, not source-native
- identical ability names with conflicting descriptions must not be silently merged
- if conflicts appear, keep all source species refs and mark `conflict_review_required`

### `species_move_pool`

Purpose:

- preserve species-to-move access while allowing Engine to treat all channels as a unified theoretical move pool

Fields:

- `species_id`: FK to `species_form`
- `move_name_raw`: source move name
- `move_id`: FK to `move`, nullable until name normalization succeeds
- `access_channel`: `level_up|skill_stone|bloodline|unknown`
- `unlock_level`: integer, nullable
- `source_field`: `技能|技能解锁等级|可学技能石|血脉技能`
- `confidence`: `confirmed|provisional`

Rules:

- `技能` and `技能解锁等级` are parallel source lists and must be length-validated
- `可学技能石` and `血脉技能` are separate access channels in storage
- skill-stone entries are acquisition evidence for canonical moves, not standalone battle moves
- Engine-facing analysis should initially use the union of `level_up`, `skill_stone`, and `bloodline`
- bloodline mutual-exclusion and acquisition legality are deferred to a later legality layer
- unresolved `move_name_raw` values must be retained instead of dropped

### `mechanic_rule`

Purpose:

- record mechanics not exposed as stable raw wiki fields

Fields:

- `rule_id`: local stable ID
- `rule_name`: human-readable name
- `status`: `confirmed|provisional`
- `applies_to`: entity selector or rule condition
- `description`: rule text
- `evidence`: source notes

Initial provisional rule:

- `defense_move_reuse_lock`
- defense skills default to a reuse-lock / cooldown that prevents consecutive use
- at least one ground-type defense skill appears to reduce damage by `90%` and reduce cooldown by `1` when responding to an attack

## Engine-Facing Views

### `species_available_moves`

Purpose:

- provide a simple theoretical move pool for role analysis

Fields:

- `species_id`
- `move_ids`: matched move IDs from all access channels
- `unresolved_move_names`: raw names that did not match a move record
- `access_channels_present`: source channels observed for this species

Rule:

- Phase 2 role analysis reads this view by default, not raw channel-specific lists
- this view unions level-up, skill-stone, and bloodline move access by default
- later legality filters may narrow this theoretical pool, but legality is not part of the first-pass role model

### `species_combat_profile`

Purpose:

- provide a compact species profile for role analysis

Fields:

- `species_id`
- `display_name`
- `primary_type`
- `secondary_type`
- `base_stats`
- `ability_name`
- `ability_effect_text`
- `available_move_ids`
- `unresolved_move_names`

Rule:

- no role labels are stored here; role labels are Engine outputs, not dex facts

## Validation Rules

Required validation:

- `primary_type`, `secondary_type`, and `move_type` must map to the canonical type chart
- numeric stat fields must parse as non-negative integers
- `power` and `energy_cost` must parse as integers when present
- `category_raw` must remain game-native
- source records must retain `source_page_id`
- parallel `技能` / `技能解锁等级` arrays must either align or emit a review warning
- duplicate move names across channels should be deduplicated in Engine-facing views, not deleted from raw storage

Warning conditions:

- species page has no `特性` or no `特性描述`
- ability name appears with multiple effect texts
- move referenced by a species cannot be matched to a move page
- detail page lacks the expected template
- observed source field is not in `field_alignment_matrix.yaml`

Hard rejects:

- imported `accuracy`
- imported `PP`
- imported raw `cooldown`
- Pokemon-style move category normalization without explicit mapping
- species records without source trace
- move records without source trace

## P1c Contract Requirements

The crawler/cleaner contract must emit:

- `source_page` records
- `raw_template_snapshot` records
- normalized `species_form` candidates
- normalized `move` candidates
- optional `derived_ability` candidates
- `species_move_pool` candidates
- validation warnings
- rejected fields with reasons

The importer must be able to run in dry-run mode and produce a diff report before writing to any persistent database.

## Open Decisions For PM

These are not blockers for writing the P1c spec, but they matter before production ingestion:

- whether `derived_ability` is materialized in the first SQLite schema or generated as a view
- whether `source_version` is kept in the main `move` table or source metadata only
- whether `bloodline` moves should be enabled by default in theoretical enemy move pools
- whether any PvP rule limits skill-stone or bloodline move availability

## Accepted Default For Now

Unless the PM overrides:

- materialize `derived_ability` because it improves role analysis and deduplication
- keep skill-stone and bloodline moves in the theoretical available move pool
- preserve access channels only for traceability and future filters
- keep defense cooldown as a provisional mechanics rule, not a raw move field
