# Change Policy Specification

## Purpose

Define how specification changes must be introduced, reviewed, and propagated in the Roco battle-analysis project.

The goal is to prevent silent drift between:

- architecture documents
- schema specs
- Python contracts
- Engine implementations
- tests
- Agent prompts or orchestration logic

## Scope

This policy applies to changes in:

- taxonomies
- data schemas
- tool contracts
- scoring rules
- report formats
- source ingestion assumptions

## Non-goals

This policy does not define:

- git branching strategy
- release packaging
- deployment automation

## Change Classes

### Patch Change

Definition:
Clarifies wording or fixes an obvious inconsistency without changing behavior.

Examples:

- typo fixes
- clearer field descriptions
- non-behavioral comment updates

Required actions:

- update the affected doc
- update examples if needed

### Minor Change

Definition:
Extends the system in a backward-compatible way.

Examples:

- adding a new optional field
- adding a new evidence line
- refining a score explanation without changing output shape

Required actions:

- update relevant spec documents
- update Python contracts if exposed
- update tests
- record the rationale

### Major Change

Definition:
Changes behavior, semantics, required fields, or output contracts in a way that can break downstream logic.

Examples:

- renaming report fields
- changing canonical role labels
- changing archetype definitions
- changing scoring semantics
- changing primary keys or species identity rules

Required actions:

- create a change spec before implementation
- update all affected specs
- update contracts
- update tests
- update any consuming prompts or workflows
- write a migration note

## Required Artifact Mapping

When a change is made, the author must check whether it affects any of these artifacts:

- `docs/battle_analysis_architecture.md`
- `specs/battle_data_model.yaml`
- `specs/agent_tool_contracts.yaml`
- `specs/role_taxonomy.md`
- `specs/archetype_taxonomy.md`
- `specs/scoring_system.md`
- `battle_engine/contracts.py`
- tests

No behavioral change is complete until all affected artifacts are aligned.

## Change Workflow

1. Identify the change class.
2. List impacted artifacts.
3. If the change is major, write a short change spec before coding.
4. Update source specs first.
5. Update executable contracts second.
6. Update tests third.
7. Only then update implementation logic.
8. Run verification.

## Compatibility Rules

### Schema Compatibility

- optional field additions are preferred over destructive renames
- destructive field removal requires a major change
- field meaning changes count as breaking changes even if the field name stays the same

### Taxonomy Compatibility

- canonical labels should change rarely
- aliasing is preferred over immediate replacement when possible
- if a canonical label changes, all affected reports and prompts must be updated together

### Scoring Compatibility

- changing weight values is a behavioral change
- changing thresholds is a behavioral change
- changing evidence requirements is a behavioral change

## Verification Requirements

Every non-patch change must include:

- updated tests
- updated examples or fixtures where relevant
- a note describing expected downstream impact

Every major change must also include:

- explicit migration notes
- confirmation that contracts and docs remain aligned

## Failure Handling

If a proposed change cannot be propagated safely in one pass:

- stop before partial implementation
- document the blocker
- split the change into smaller phases

Bad example:

- updating role labels in the code but leaving the taxonomy spec and tests stale

Good example:

- updating the taxonomy spec first, then contracts, then tests, then implementation

## Evaluation Checklist

- Is the change class correctly identified?
- Are all affected artifacts listed?
- Were specs updated before code?
- Were tests updated for every behavioral change?
- If the change is breaking, is there a migration note?
