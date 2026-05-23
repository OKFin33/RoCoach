# Wiki Field Discovery Review: 2026-04-13

## Purpose

Review the bounded wiki reconnaissance outputs and translate evidence into SSD decisions.

This document is a review bridge between:

- `specs/wiki_field_discovery_spec.md`
- `data/wiki_field_discovery/2026-04-13/candidate_field_aggregate.json`
- `specs/field_alignment_matrix.yaml`

It is not an ingestion spec and does not authorize production database construction.

## Reviewed Artifacts

- `tools/wiki_field_discovery_recon.py`
- `data/wiki_field_discovery/2026-04-13/raw_page_samples.json`
- `data/wiki_field_discovery/2026-04-13/candidate_field_aggregate.json`
- `data/wiki_field_discovery/2026-04-13/findings_memo.md`
- `data/wiki_field_discovery/2026-04-13/run_metadata.json`

## Recon Summary

Observed sample coverage:

- `species`: 4 index pages, 9 detail pages
- `move`: 2 index pages, 8 detail pages
- `ability`: 9 embedded species-detail samples

Candidate field recommendations:

- `25` confirmed
- `10` provisional
- `12` forbidden_by_default

Page structure:

- `species` detail pages expose structured `{{精灵信息}}`
- `move` detail pages expose structured `{{技能信息}}`
- no standalone ability page or category was found in this pass
- ability evidence currently comes from species fields `特性` and `特性描述`

## Accepted Matrix Updates

Accepted as confirmed:

- species raw identity and combat fields: `精灵名称`, `精灵形态`, `精灵阶段`, `主属性`, `2属性`
- species stat dimensions: `生命`, `物攻`, `魔攻`, `物防`, `魔防`, `速度`
- species embedded ability fields: `特性`, `特性描述`
- species move access fields: `技能`, `技能解锁等级`, `可学技能石`, `血脉技能`
- move fields: `技能名称`, `属性`, `技能类别`, `威力`, `耗能`, `效果`

Kept or changed to provisional:

- `species.dex_no`: only seen in sampled index projections, not detail templates
- `species.initial_species_name`: useful for family grouping but not yet a battle schema requirement
- `species.regional_form_name`: source label is separate from `精灵形态`
- `species.ability_ids`: wiki exposes names and descriptions, not standalone ability IDs
- `species.move_ids`: species pages expose move names, not canonical move IDs
- `ability.ability_id`: local ID only if ability is promoted to a derived entity
- `move.description_text`: observed but empty in current examples
- `move.source_version`: provenance candidate, not battle logic

Kept forbidden by default:

- `move.accuracy`
- `move.pp`
- `move.cooldown` as a raw wiki field
- `ability.numeric_modifier`
- encyclopedia/cosmetic species fields such as body size, weight, lore description, distribution, shiny flag, collection tasks, and evolution conditions

Additional PM-provided mechanism note:

- defense skills may have a default reuse-lock / cooldown rule
- this does not promote `move.cooldown` as a wiki source field
- model it later as a provisional combat rule after effect-text or in-game verification

## Schema Implications

The next schema should be source-traceable and raw-first:

- `species` can be ingested from `{{精灵信息}}`
- `move` can be ingested from `{{技能信息}}`
- `ability` should not be crawled as an independent wiki page type unless a stronger source is found
- derived ability records can be built from species `特性` / `特性描述`, but must retain source species references
- move references from species must be normalized by name against move records
- learnset fields that are parallel lists must be length-validated before import
- defense-skill reuse restrictions belong in mechanics modeling or derived features, not in raw wiki field ingestion unless a stable source field appears

## Non-Actions

Do not do these yet:

- full wiki ingestion
- production database construction
- role taxonomy extraction
- move/ability tag derivation as hard facts
- meta popularity inference from community content

## Open Decisions Before P1b

The PM and implementation agent still need to decide:

- whether Phase 2 MVP materializes `ability` as a derived table or keeps ability fields embedded on species records
- how to model `form_name`, `regional_form_name`, and `initial_species_name`
- whether skill-stone and bloodline moves are separate access channels in the schema
- what minimum normalization rules are acceptable for matching species move names to move records
