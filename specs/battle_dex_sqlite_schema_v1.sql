PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS import_run (
  import_run_id TEXT PRIMARY KEY,
  upstream_importer_run_id TEXT NOT NULL,
  policy_mode TEXT NOT NULL CHECK (policy_mode IN ('policy_b')),
  canonical_artifact_dir TEXT NOT NULL,
  canonical_run_id TEXT NOT NULL,
  supplement_artifact_path TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT NOT NULL,
  write_mode TEXT NOT NULL CHECK (write_mode IN ('write')),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_page (
  source_page_id TEXT PRIMARY KEY,
  entity_hint TEXT NOT NULL CHECK (entity_hint IN ('species', 'move', 'ability_embedded', 'unknown')),
  page_title TEXT NOT NULL,
  page_url TEXT NOT NULL,
  revision_id TEXT,
  fetched_at TEXT NOT NULL,
  content_sha256 TEXT NOT NULL,
  parser_version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw_template_snapshot (
  snapshot_id TEXT PRIMARY KEY,
  source_page_id TEXT NOT NULL REFERENCES source_page(source_page_id),
  template_name TEXT NOT NULL CHECK (template_name IN ('精灵信息', '技能信息', 'unknown')),
  raw_fields_json TEXT NOT NULL,
  extraction_warnings_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS species_form (
  species_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  initial_species_name TEXT,
  form_name TEXT,
  regional_form_name TEXT,
  evolution_stage TEXT,
  primary_type TEXT NOT NULL,
  secondary_type TEXT,
  base_stats_json TEXT NOT NULL,
  ability_name TEXT,
  ability_effect_text TEXT,
  source_page_id TEXT NOT NULL REFERENCES source_page(source_page_id),
  raw_snapshot_id TEXT,
  confidence TEXT NOT NULL CHECK (confidence IN ('confirmed', 'provisional')),
  canonical_source_layer TEXT NOT NULL CHECK (canonical_source_layer IN ('wiki', 'manual_supplement')),
  wiki_source_refs_json TEXT NOT NULL,
  supplement_refs_json TEXT NOT NULL,
  resolution_reason TEXT NOT NULL,
  import_run_id TEXT NOT NULL REFERENCES import_run(import_run_id),
  last_resolved_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS move (
  move_id TEXT PRIMARY KEY,
  move_name TEXT NOT NULL,
  move_type TEXT,
  category_raw TEXT CHECK (category_raw IN ('状态', '防御', '物攻', '魔攻')),
  power INTEGER,
  energy_cost INTEGER,
  effect_text TEXT,
  description_text TEXT,
  source_version TEXT,
  source_page_id TEXT,
  raw_snapshot_id TEXT,
  confidence TEXT NOT NULL CHECK (confidence IN ('confirmed', 'provisional')),
  canonical_source_layer TEXT NOT NULL CHECK (canonical_source_layer IN ('wiki', 'manual_supplement')),
  wiki_source_refs_json TEXT NOT NULL,
  supplement_refs_json TEXT NOT NULL,
  resolution_reason TEXT NOT NULL,
  import_run_id TEXT NOT NULL REFERENCES import_run(import_run_id),
  last_resolved_at TEXT NOT NULL,
  FOREIGN KEY (source_page_id) REFERENCES source_page(source_page_id)
);

CREATE TABLE IF NOT EXISTS derived_ability (
  ability_id TEXT PRIMARY KEY,
  ability_name TEXT NOT NULL,
  effect_text TEXT NOT NULL,
  source_species_ids_json TEXT NOT NULL,
  source_page_ids_json TEXT NOT NULL,
  derivation_status TEXT NOT NULL CHECK (derivation_status IN ('single_source', 'merged_consistent', 'conflict_review_required', 'supplement_backed')),
  confidence TEXT NOT NULL CHECK (confidence IN ('confirmed', 'provisional')),
  canonical_source_layer TEXT NOT NULL CHECK (canonical_source_layer IN ('wiki', 'manual_supplement')),
  wiki_source_refs_json TEXT NOT NULL,
  supplement_refs_json TEXT NOT NULL,
  resolution_reason TEXT NOT NULL,
  import_run_id TEXT NOT NULL REFERENCES import_run(import_run_id),
  last_resolved_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS species_move_pool (
  species_id TEXT NOT NULL REFERENCES species_form(species_id),
  move_name_raw TEXT NOT NULL,
  move_id TEXT REFERENCES move(move_id),
  access_channel TEXT NOT NULL CHECK (access_channel IN ('level_up', 'skill_stone', 'bloodline', 'unknown')),
  unlock_level INTEGER,
  source_field TEXT NOT NULL CHECK (source_field IN ('技能', '技能解锁等级', '可学技能石', '血脉技能')),
  confidence TEXT NOT NULL CHECK (confidence IN ('confirmed', 'provisional')),
  source_page_id TEXT NOT NULL REFERENCES source_page(source_page_id),
  import_run_id TEXT NOT NULL REFERENCES import_run(import_run_id),
  last_resolved_at TEXT NOT NULL,
  PRIMARY KEY (species_id, move_name_raw, access_channel)
);

CREATE TABLE IF NOT EXISTS import_entity_resolution (
  entity_type TEXT NOT NULL,
  entity_key TEXT NOT NULL,
  resolution_status TEXT NOT NULL CHECK (resolution_status IN ('included', 'excluded', 'review_required', 'supplement_backed', 'unresolved')),
  canonical_source_layer TEXT NOT NULL CHECK (canonical_source_layer IN ('wiki', 'manual_supplement')),
  wiki_source_refs_json TEXT NOT NULL,
  supplement_refs_json TEXT NOT NULL,
  resolution_reason TEXT NOT NULL,
  import_run_id TEXT NOT NULL REFERENCES import_run(import_run_id),
  created_at TEXT NOT NULL,
  PRIMARY KEY (entity_type, entity_key, import_run_id)
);

CREATE VIEW IF NOT EXISTS species_available_moves AS
SELECT
  smp.species_id,
  smp.move_id,
  m.move_name,
  smp.access_channel,
  smp.unlock_level
FROM species_move_pool AS smp
JOIN move AS m ON m.move_id = smp.move_id;

CREATE VIEW IF NOT EXISTS species_combat_profile AS
SELECT
  sf.species_id,
  sf.display_name,
  sf.primary_type,
  sf.secondary_type,
  sf.base_stats_json,
  sf.ability_name,
  sf.ability_effect_text,
  json_group_array(DISTINCT sam.move_id) AS available_move_ids
FROM species_form AS sf
LEFT JOIN species_available_moves AS sam ON sam.species_id = sf.species_id
GROUP BY
  sf.species_id,
  sf.display_name,
  sf.primary_type,
  sf.secondary_type,
  sf.base_stats_json,
  sf.ability_name,
  sf.ability_effect_text;
