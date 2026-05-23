# Managed Persona Creation Pipeline Spec

## Purpose

Define the end-to-end managed persona creation pipeline for the product.

This pipeline is the long-term user-facing feature. The user should not need to
manually understand source adapters, doctrine schemas, or ingestion mechanics.

## Product Goal

The desired UX is eventually:

1. the user describes what kind of persona they want, or names an existing
   subject to distill
2. the system selects an appropriate persona-source adapter
3. the system creates a doctrine artifact bundle
4. the system validates and reviews the artifact
5. the system registers a persona that can be used by synthesis and rendering

## Core Stages

### Stage 1. Source Selection

The pipeline selects one source-adapter mode:

- `distill_from_existing_subject`
- `design_from_zero`

Current approved first source-adapter:

- `nuwa_distillation_adapter`

Future approved candidate:

- `nexus_original_design_adapter`

### Stage 2. Persona Source Adapter Execution

The source adapter generates:

- memo
- doctrine draft
- mapping note
- provenance metadata

This stage is governed by:

- `specs/persona_source_adapter_contract.yaml`

### Stage 3. Artifact Ingestion

The generated artifact bundle must pass through ingestion:

- schema validation
- provenance checks
- reasoning/rendering split checks
- honesty boundary checks
- IP safety checks
- registry admission status assignment

This stage is governed by:

- `specs/persona_artifact_ingestion_contract.yaml`

### Stage 4. Registry Admission

Only admitted artifacts may become selectable personas.

Registry entry states should include:

- `internal_only`
- `review_ready`
- `public_safe`

### Stage 5. Runtime Use

At runtime, the admitted persona should split into:

- synthesis-facing doctrine inputs
- rendering-facing style inputs
- metadata/policy-only controls

It must not enter runtime as one undifferentiated prompt blob.

## Internal Engineering Rule

Even if the final product UX is "one button", the internal system must remain a
pipeline:

`source adapter -> artifact bundle -> ingestion -> registry -> runtime`

Do not collapse these into:

`user request -> persona directly injected into runtime`

## Current Sequencing

Recommended sequencing:

1. finalize source adapter contract
2. finalize artifact ingestion contract
3. implement `nuwa_distillation_adapter`
4. implement registry admission and review states
5. later add `nexus_original_design_adapter`

## Non-Goals

- no requirement to expose manual BYO persona upload in the user-facing product
- no requirement to ship public persona creation immediately
- no requirement to support arbitrary prompt-defined personas without review

