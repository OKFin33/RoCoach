# Semantic Role Policy

## Purpose

Define what species-level and team-level semantic role judgements are allowed in
the current advisor product stage.

## Core Rule

Semantic role judgement is allowed, but it is not hard truth.

Unless a later deterministic scorer is approved, role judgements should be
treated as:

- evidence-backed
- team-conditional
- set-conditional when relevant
- uncertainty-bearing

## Approved Output Types

Allowed now:

- `role_hypothesis`
- `semantic_roles`
- `tactical_tags`
- `reasoning_summary`
- `uncertainty_notes`

Allowed language:

- `更像`
- `倾向于`
- `在当前队伍里更可能是`
- `如果按这类配置理解`
- `更接近`

## Required Downgrade Cases

The advisor must downgrade confidence when:

- selected moves are missing
- selected ability is missing
- the team context is incomplete
- mechanics evidence is only partial
- the judgement depends mainly on analogical reasoning

## Required Refusal Cases

The advisor should refuse or sharply narrow the claim when:

- the user asks for canonical “唯一正确定位”
- the user asks for exact best build without approved set evidence
- the user asks for meta-authoritative role ranking
- the evidence base is too thin even for a provisional role hypothesis

## Forbidden Claims

Do not output as confirmed:

- exact canonical role for a species
- exact standard build for a species
- exact team archetype without sufficient evidence
- current meta prevalence as fact

## Evidence Hierarchy

Use this order:

1. deterministic Engine / SQL facts
2. approved mechanics docs
3. approved tactical cases
4. bounded semantic synthesis

Lower layers may not override higher layers.

## Team-Conditional Rule

The same species may occupy different roles in different teams.

The same species may also occupy different roles under different set choices.

Therefore the advisor should prefer:

- `in this team`
- `under this assumed set`
- `with current known evidence`

over species-global role declarations.

