# Data Source Strategy

## Purpose

Define the source strategy for P1a and later Phase 2 battle-data work.

This document does not approve ingestion yet.
It defines how source quality should be judged before ingestion starts.

## Current Scope

This strategy currently applies to battle-analysis data only:

- species
- move
- ability

It does not currently apply to:

- cosmetic assets
- lore
- acquisition guides
- general wiki enrichment

## Source Tiers

### Tier 1: Mechanic Verification Sources

Examples:

- official announcements
- official game pages
- in-game screenshots
- in-game recordings

Use:

- confirm battle mechanics
- confirm field existence when visible in-game
- resolve conflicts in high-impact battle semantics

### Tier 2: Primary Structured Sources

Examples:

- wiki index pages
- species detail pages
- move detail pages
- ability detail pages

Use:

- discover field structure
- collect structured dex data
- build initial battle database candidates

Current project judgement:

- wiki is the primary structured source for P1a field discovery

### Tier 3: Low-Confidence Supplementary Sources

Examples:

- community攻略
- self-media weekly reports
- ranking summaries
- forum / comment interpretations

Use:

- fill terminology gaps
- suggest candidate strategic tags
- surface questions worth verifying elsewhere

Restrictions:

- must not be treated as primary evidence for field existence
- must not override Tier 1 or Tier 2 evidence

## Discovery Order

The intended order is:

1. inspect structured wiki pages for entity fields
2. map recurring fields into the alignment matrix
3. verify battle-critical ambiguities against stronger mechanic sources
4. use community material only to flag missing concepts or low-confidence notes

## Conflict Resolution

If sources disagree:

1. prefer Tier 1 over Tier 2
2. prefer repeated Tier 2 consistency over isolated Tier 3 claims
3. downgrade disputed fields to `provisional`
4. mark unresolved imported assumptions as `forbidden_by_default`

## Current Strategic Decision

For P1a:

- wiki is the primary structured source
- official or in-game evidence is the mechanic verification source
- community content is only a supplementary reference

## Accepted Policy B

For battle-dex ingestion and later Agent reasoning, accept data-source policy B:

- `wiki canonical + manual verified supplement`

This means the project now has two formal input layers for battle data resolution:

### Layer 1: Wiki Canonical

Use:

- structured wiki crawl artifacts
- raw template snapshots
- normalized P1c/P1d candidate artifacts

Role:

- default canonical source for species, move, and embedded ability data
- provenance anchor for crawler and importer outputs

### Layer 2: Manual Verified Supplement

Use:

- PM-provided or human-verified battle corrections
- hidden-form exclusion decisions
- manual move records missing from current wiki artifacts
- mechanics notes that should inform later Agent reasoning

Role:

- patch known wiki omissions or battle-scope mismatches without overwriting raw wiki evidence
- provide resolver input when wiki artifacts are incomplete, conflicting, or out-of-scope

Current artifact:

- `docs/manual_battle_data_supplement_2026-04-14.md`
- `data/manual_supplements/manual_battle_data_supplement_2026-04-14.yaml`

Restrictions:

- manual supplement is not a replacement for raw wiki artifacts
- manual supplement must be explicit, versioned, and reviewable
- structured YAML/JSON supplement is the importer-facing source of truth; markdown remains the human briefing layer
- community summaries alone do not qualify; the supplement must be human-verified

## Immediate Next-Step Usage

This strategy should guide:

- `docs/combat_ontology.md`
- `specs/field_alignment_matrix.yaml`
- later Phase 2 schema design

No ingestion script should be considered authoritative until its mapped fields satisfy this strategy.

## Resolver / Importer Precedence

The future resolver/importer should apply precedence in this order:

1. explicit exclusion or review gate from the manual supplement
2. wiki canonical structured artifact
3. manual verified supplement for missing or conflicting battle-relevant fields
4. Tier 1 mechanic verification sources for high-impact rules

Rules:

- raw wiki artifacts must remain preserved even when supplement resolution changes the importer decision
- supplement resolution should annotate why a field or entity was overridden, excluded, or held for review
- no supplement should silently mutate the raw wiki layer

## Accepted Current Manual Decisions

Accepted for the current battle-dex target:

- exclude the current 10 hidden special plot forms from ingest
- treat future same-pattern forms as `human-review-before-ingest`
- accept manual supplement records for:
  - `湿润印记`
  - `溶解液`
  - `龙之舞`
  - `溶解扩散`
- accept baseline 印记 system rules into a later mechanics / Agent supplement layer, not into the raw wiki schema

## Importer Gate

Do not begin SQLite importer work until:

- policy B precedence is implemented clearly
- hidden-form exclusion/review logic is implemented
- manual supplement ingestion shape is explicit
- structured supplement export exists and is validator-friendly
- mechanic supplements are separated from raw wiki schema

Only after these are true should the main thread approve importer / SQLite next-step design.
