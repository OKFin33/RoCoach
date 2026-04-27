# Wiki Field Discovery Spec

## Purpose

Define the execution rules for `P1a` wiki reconnaissance and field discovery.

This spec exists to ensure that wiki inspection produces:

- evidence-backed candidate fields
- page-structure understanding
- aligned input for later schema design

It does **not** authorize full ingestion or database construction.

## Scope

This discovery pass covers only battle-analysis relevant entities:

- `species`
- `move`
- `ability`

It does not cover:

- art assets
- lore
- acquisition methods
- cosmetic metadata
- general encyclopedia enrichment

## Goal

The goal is to answer:

1. what page types exist for battle-relevant entities
2. what recurring fields appear on those page types
3. which fields look structurally stable
4. which fields are textual only
5. which candidate fields should be marked:
   - `confirmed`
   - `provisional`
   - `forbidden_by_default`

## Discovery Targets

The discovery pass should inspect:

1. species index pages
2. species detail pages
3. move listing and move detail pages
4. ability listing and ability detail pages

## Sampling Rules

The reconnaissance script should not begin with a full crawl.

Initial target:

- at least `1` relevant index page per entity type if it exists
- at least `5` detail pages per entity type when available
- include pages with visible structural variation when possible

The purpose of the sample is:

- field discovery
- template comparison
- structure stability testing

Not:

- completeness
- production ingestion

## Output Requirements

The discovery output must contain, for each inspected page:

- `page_type`
- `source_url`
- `page_title`
- `candidate_fields`
- `example_values`
- `field_source_mode`
  - `structured_block`
  - `label_value_pair`
  - `free_text_only`
  - `mixed`

And for aggregated analysis:

- field occurrence count
- page coverage count
- example values
- confidence recommendation
- notes on ambiguity or instability

## Candidate Field Rules

Each candidate field discovered from the wiki must be mapped to one of:

- `confirmed`
- `provisional`
- `forbidden_by_default`

### Mark as `confirmed` when:

- the field appears repeatedly across the same page type
- the meaning is stable
- it is clearly battle-relevant
- the representation is not just inferred from prose

### Mark as `provisional` when:

- the field appears inconsistent across pages
- the meaning is partially implicit
- the field may be useful but still needs alignment
- the field likely exists but the exact representation is unclear

### Mark as `forbidden_by_default` when:

- the field is not directly evidenced
- the field appears imported from another game model
- the field is encyclopedia-only and not relevant to current battle analysis
- the field is being guessed from community assumptions instead of source structure

## Discovery Method

The script should perform these steps:

1. fetch the target page
2. extract title and candidate content blocks
3. detect likely label-value structures
4. collect repeating field labels
5. capture a small number of example values per field
6. aggregate field recurrence across sampled pages
7. emit a machine-readable summary for matrix review

## Evidence Discipline

Rules:

- store source URLs for every sampled page
- preserve raw observed labels before normalization
- do not normalize directly into final schema field names without review
- keep evidence traceable from aggregated field back to page sample

## Normalization Discipline

During discovery:

- normalize only enough to group obvious duplicates
- preserve original field labels alongside normalized candidates
- prefer game-native terminology
- do not silently translate into Pokemon-like jargon

## Non-Goals

This discovery pass must not:

- perform final schema design
- insert records into a production database
- infer missing fields from analogy
- derive strategic tags as hard facts
- use community content as primary proof of field existence

## Deliverables

The discovery execution should produce:

1. a raw page-sample artifact
2. an aggregated candidate-field summary
3. a proposed update set for `specs/field_alignment_matrix.yaml`
4. a short findings memo describing:
   - stable page structures
   - unstable fields
   - obvious ingestion risks

## Exit Criteria

This spec is considered successfully executed when:

- entity pages for `species`, `move`, and `ability` have been sampled
- recurring wiki fields have been enumerated
- major battle-relevant candidate fields are mapped to confidence states
- the project can proceed to schema design without relying on genre assumptions
