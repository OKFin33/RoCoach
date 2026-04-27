# Report Confidence Policy

## Purpose

Define what the report / advisor layer may state with each confidence level.

This policy exists to prevent the LLM layer from turning bounded analysis into unsupported strategic claims.

## Confidence Tiers

### Confirmed

Use when the statement is directly grounded in deterministic Engine output or approved project baseline documents.

Examples:

- the team has a critical weakness to `水`
- the team has no resistance to `幽`
- the top single-type patch directions are `X`, `Y`, `Z`

Allowed language:

- `clearly`
- `directly`
- `the current structure shows`
- `the Engine identifies`

### Provisional

Use when the statement depends on project-adopted but not yet fully verified mechanics or on bounded interpretive synthesis.

Examples:

- interpretation that a given structure is likely to have limited switch-in space
- discussion that dual-type recommendations may better cover distributed weaknesses
- interpretation using currently adopted project baseline mechanics such as the `×3 / ÷3` dual-type rule

Allowed language:

- `likely`
- `suggests`
- `under the current project baseline`
- `provisionally`

### Low Confidence

Use when the statement depends on community observations, weak environment signals, or incomplete strategic evidence.

Examples:

- current ladder trend comments
- claims about popular teams or common anti-meta patterns
- speculative statements about specific team archetype prevalence

Allowed language:

- `some community observations suggest`
- `as a low-confidence reference`
- `this should not be treated as a hard meta conclusion`

## Forbidden Claims For Phase 1.5

The report layer must not:

- recommend specific species
- claim exact role assignments for species without Phase 2 data
- state current meta prevalence as fact
- assert battle outcomes or matchup percentages
- override Engine conclusions with retrieval snippets

## Grounding Rules

1. Every high-severity risk must reference Engine evidence.
2. Any statement derived from provisional mechanics must mention the provisional baseline if relevant.
3. Any meta or community statement must be explicitly labeled low confidence.
4. Persona styling must not change confidence tier.

## Language Discipline

Preferred:

- `the current structure shows`
- `the Engine output indicates`
- `this suggests`
- `if an appropriate dual-type species exists`

Avoid:

- `this team definitely beats`
- `the ladder is dominated by`
- `this is the standard best build`
- `you must replace X with Y`

## Enforcement

The report validator should reject outputs that:

- include unsupported species-level recommendations
- include unlabeled meta claims
- contradict deterministic Engine facts
- escalate provisional or low-confidence material into confirmed wording
