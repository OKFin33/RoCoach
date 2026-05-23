# P14 Dataset Provenance and Sample Schema Contract v0

Status: planning contract
Date: 2026-05-22
Scope: field-level provenance for Evidence KB, KG, and Gold/Eval samples
Runtime effect: none

This document is the DP-03 output for the dataset pipeline planning package.
It defines sample shapes future production lanes must satisfy. It does not
modify source, evidence, candidate, reviewed, Gold, or runtime data.

## 1. Core Rule

Roco dataset facts are not valid because an Agent produced a plausible summary.
They are valid only when each promoted or reviewed field can point to:

- source span;
- transform lineage;
- canonicalization decision;
- reviewer identity;
- confidence and risk state.

Item-level source refs are not enough. Reviewed structured fields need
field-level provenance.

## 2. Shared Identifiers

All sample units use stable ids.

```yaml
ids:
  source_id: "bilibili/BV..."
  source_span_id: "span/source_id/0001"
  claim_atom_id: "claim/source_id/0001"
  kg_item_id: "kg/set_family/..."
  gold_id: "gold/..."
```

Rules:

- ids are stable within one snapshot;
- if a later snapshot changes an id, it must record supersession;
- a display name is never a stable id by itself.

## 3. Evidence KB Sample

Sample unit: `evidence_segment`.

```yaml
schema_version: p14.evidence_segment.v0
segment_id: ""
source_id: ""
source_url: ""
platform: bilibili | official | wiki | other
uploader: ""
published_at: ""
processed_at: ""
start_ms: 0
end_ms: 0
raw_transcript_ref: ""
transcript_text: ""
repair_status: clean | repaired | partial | unresolved
asr_method: subtitle | bailian_asr | other
ab_refinement_version: ""
source_quality: good | usable | poor
rights:
  distribution_state: internal_only | source_metadata_only | shareable_derived
runtime_allowed: false
```

Evidence segments preserve context. They are not reviewed KG facts by
themselves.

## 4. Claim Atom Sample

Sample unit: `claim_atom`.

```yaml
schema_version: p14.claim_atom.v0
claim_atom_id: ""
source_id: ""
source_span_ids: []
claim_text: ""
claim_type: set_skeleton | build_configuration | tactical_context | mechanism_claim | relation_claim | negative_case
extracted_entities:
  species: []
  moves: []
  abilities: []
  mechanisms: []
canonicalization:
  resolved: []
  unresolved: []
  rejected_surface_forms: []
transform_lineage:
  extractor_version: ""
  normalization_version: ""
  repair_log_refs: []
quality:
  confidence: high | medium | low
  asr_risk: none | low | medium | high
runtime_allowed: false
```

Claim atoms can be wrong or incomplete. Their job is to make future structured
decisions traceable.

## 5. KG Candidate Sample

Sample units:

- `set_skeleton`
- `set_family`
- `alter_variant`
- `relation_claim`
- `mechanism_rule`
- `review_ledger_entry`

```yaml
schema_version: p14.kg_item.v0
kg_item_id: ""
kg_item_type: set_family
meta_snapshot: "2026-s1"
source_ids: []
source_span_ids: []
claim_atom_ids: []
canonical_entities:
  species: []
  moves: []
  abilities: []
a_layer_resolution:
  species:
    - name: ""
      status: resolved | unresolved | rejected
      resolver_version: ""
  moves:
    - name: ""
      status: resolved | unresolved | rejected
      legality: legal | illegal | not_checked
      reason: ""
  abilities: []
field_provenance:
  species:
    - field_path: "canonical_entities.species[0]"
      source_span_ids: []
      claim_atom_ids: []
      support_type: explicit | inferred_from_bundle | rejected | not_applicable
      notes: ""
  moves: []
  nature: []
  iv: []
  bloodline: []
  role: []
  teammate_relations: []
  counter_relations: []
  mechanism_dependencies: []
transform_lineage:
  transcript_repair_ids: []
  extractor_version: ""
  normalization_version: ""
  consolidation_batch: ""
review:
  status: candidate | agent_checked | review_packeted | pm_reviewed | runtime_promoted | deferred | rejected
  extractor_role: ""
  extractor_agent_id: ""
  extractor_run_id: ""
  reviewer_role: ""
  reviewer_agent_id: ""
  reviewer_run_id: ""
  review_packet: ""
quality:
  confidence: high | medium | low
  asr_risk: none | low | medium | high
  source_diversity: single_source | multi_source | independent_sources
  contradiction_state: none | open | resolved
runtime_allowed: false
```

Field-provenance rules:

- every promoted species, move, role, relation, and mechanism dependency must
  have a `field_provenance` entry;
- support type `inferred_from_bundle` is allowed for set intent, but the bundle
  must list its source spans;
- unresolved or not-applicable fields must be explicit;
- illegal species-move assignments are preserved as rejected evidence, not
  silently removed.

## 6. Gold/Eval Item Sample

```yaml
schema_version: p14.gold_item.v0
gold_id: ""
gold_type: gold_set_family | gold_split_case | gold_mechanism_boundary | gold_stateful_form_boundary | gold_negative_case
meta_snapshot: "2026-s1"
review_status: draft | pm_accepted | pm_deferred | rejected | superseded
decision:
  label: ""
  expected_behavior: ""
input_fixture_refs: []
expected_output:
  allowed: []
  forbidden: []
field_provenance:
  decision_label: []
  expected_behavior: []
  forbidden_behavior: []
review:
  pm_decision_packet: ""
  pm_decider: ""
  reviewer_role: ""
  reviewer_agent_id: ""
  reviewer_run_id: ""
quality:
  confidence: high | medium | low
  reviewer_agreement: single_pm | double_reviewed | disputed | superseded
regression_tasks: []
runtime_allowed: false
```

Gold acceptance calibrates extraction and regression. It does not imply runtime
promotion or graph materialization.

## 7. Repair History

Any ASR/canonicalization repair that affects a structured field must be
traceable.

```yaml
repair_history:
  - repair_id: ""
    surface_form: ""
    canonical_form: ""
    repair_type: asr_fix | alias | typed_skill_surface | rejection
    evidence:
      source_span_ids: []
      a_layer_refs: []
    reviewer:
      role: ""
      agent_id: ""
      run_or_context_id: ""
    status: candidate | accepted | rejected | unresolved
```

Example policy:

- typed skill surfaces such as `electric_willpower_impact` normalize to
  canonical `willpower_impact` plus attribute only when mechanism evidence
  supports the typed surface.

## 8. Reviewer Identity

Review artifacts must record:

```yaml
review_identity:
  extractor:
    role: ""
    agent_id: ""
    run_or_context_id: ""
  reviewer:
    role: ""
    agent_id: ""
    run_or_context_id: ""
  pm:
    decision_packet: ""
    decision_id: ""
```

Role labels alone do not prove independence. The run/context id is required so
a later audit can detect same-context self-review.

## 9. Migration-Needed Field List

Existing artifacts may lack fields required by this contract. Planning tasks
must not edit them in place. They must produce migration requirements.

Minimum migration-needed list:

- add `field_provenance` to reviewed/promoted KG fields;
- add extractor/reviewer agent and run/context ids to review artifacts;
- add repair history refs for accepted canonicalization fixes;
- add explicit unresolved/not-applicable reasons for missing reviewed fields;
- add rights/distribution state to evidence source records;
- add regression task refs to Gold/Eval items.

Migration work is a future production task and must be validator-backed.
