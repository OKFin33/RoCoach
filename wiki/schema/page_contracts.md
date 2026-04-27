# Battle Wiki Page Contracts

Every reviewed wiki page must include a structured metadata block:

```yaml
title: ""
content_class: ""
status: draft
confidence: provisional
sources: []
a_layer_refs: []
last_reviewed: ""
reviewed_by: ""
persona_free: true
```

Allowed `content_class` values:

- `mechanics`
- `team_building`
- `role_methodology`
- `archetype_methodology`
- `recommendation_taste`
- `counterexample`
- `casebank`
- `glossary`

Allowed `status` values:

- `draft`
- `reviewed`
- `deprecated`

Page body minimum sections:

```text
## Claim
## Strategic Use
## Evidence
## Confidence
## A-Layer Boundary
## Known Failure Modes
```

Casebank pages may use the case fields from `specs/tactical_casebank_spec.md`
instead, but must still preserve confidence and provenance.
