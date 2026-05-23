# Roco Project Brief (Zero-Context Temporary Spec)

## Purpose

This document is a temporary external-facing brief for readers with zero prior
context.

It explains:

- what this project is
- how it works
- what it is trying to become
- what has already been completed

It is intentionally high-signal and does not assume the reader has followed the
project's internal SSD, thread history, or implementation timeline.

As of: `2026-04-20`

## 1. What This Project Is

`Roco` is an unofficial battle-advisor product for `洛克王国世界`.

Its job is not to act like a general chatbot. Its job is to help a player ask
questions such as:

- Is this team structurally sound?
- What defensive holes does this team have?
- What kind of patch direction does this team need?
- What does this species look like on paper?
- In this team, is this species acting more like a core attacker, a pivot, or a
  support piece?

The intended product form is:

- a conversational tactical coach
- backed by deterministic battle logic, structured species data, and approved
  domain knowledge
- with visible evidence and confidence boundaries when needed

In short:

`Roco` is trying to become a grounded battle coach, not a freeform roleplay bot
and not a raw spreadsheet viewer.

## 2. What Problem It Is Solving

There are two common failure modes in this space:

1. pure calculators are correct but hard to use
2. pure LLM chatbots sound smart but invent facts

This project is trying to avoid both.

The product goal is:

- keep factual substrate grounded and inspectable
- let users interact through natural language
- eventually make the surface feel like talking to a sharp tactical coach
  instead of reading a report dump

## 3. How It Works

The current architecture separates truth, reasoning, and expression.

### 3.1 Grounded Fact Layer

This layer owns battle truth.

It includes:

- deterministic type / team-structure analysis
- SQLite battle-dex facts
- approved bounded retrieval from local docs

This layer is responsible for:

- structural team conclusions
- species fact lookup
- evidence attribution
- confidence boundaries
- refusal boundaries

LLM output is **not** allowed to override this layer.

### 3.2 Reasoning / Synthesis Direction

The project's approved post-P0 direction is:

- LLM should become the core analysis unit
- but it must not become the source-of-truth unit

The target shape is:

- `A` = grounded analytical substrate
- `B` = doctrine pack
  - approved mechanics and methodology
  - role/archetype taxonomy
  - persona doctrine inputs
- `LLM synthesis` = product-facing advisory reasoning

This means the model should eventually be responsible for:

- combining grounded facts into a real advisory judgement
- explaining tradeoffs
- deciding how to answer the user's actual question

But it must still stay inside grounded boundaries.

### 3.3 Presentation Layer

The product should not expose raw structured payloads as the default user
experience.

The target front-stage output is:

- `Reply`
- `Why`

Where:

- `Reply` = the main coach-style answer
- `Why` = the compact explanation most users actually need

Evidence, confidence, and tool traces remain important, but they belong in a
secondary inspectable layer by default.

### 3.4 Persona Layer

Persona is not supposed to own truth.

Persona should influence:

- how the system speaks
- how it frames pressure, caution, and recommendation style
- how it sounds like a coherent tactical coach

Persona should not be allowed to change:

- facts
- evidence
- confidence tier
- refusal decisions

The project has already defined a deeper future direction for persona:

- persona doctrine should include style plus reasoning-facing traits
- a Nuwa-style five-layer doctrine model is being prepared:
  - expression DNA
  - mental models
  - decision heuristics
  - anti-patterns
  - honesty boundaries

## 4. Current Product Shape

Today the repo is no longer just a CLI script collection.

It already contains:

- a deterministic team/type engine
- a SQLite battle-dex repository
- a bounded local doc retrieval layer
- an advisor runtime with deterministic and native-LLM paths
- a pure app/API-facing response contract
- a FastAPI backend
- a mobile Expo/React Native scaffold
- persona and IP guard foundations
- public-release hardening for local operation

The current system can already support:

- team structure analysis
- species lookup
- session-local follow-up questions
- bounded fallback behavior when native runtime fails

However, the current default experience is still closer to:

- `structured analytical payload + rendering`

than to the intended final experience:

- `grounded coach-like conversation`

That gap is the main post-P0 work.

## 5. What Has Been Completed

### P0 Status

P0 is complete.

Completed and audited:

- App-facing contract normalization
- Minimal agent-core extraction
- FastAPI backend
- Persona V1 + IP guard
- Mobile MVP scaffold
- Public-release hardening

The current project state is:

- `P0 fully complete`
- `ready for post-P0 planning / implementation`

### Data / Runtime Reality

Currently available:

- SQL-first structured retrieval through the battle-dex repository
- curated keyword-bounded local doc retrieval
- deterministic engine for team/type analysis

Currently **not** part of the live product path:

- embeddings
- case retrieval
- web-in-loop retrieval
- long-term cross-session memory

## 6. What It Is Trying To Become Next

The next major target is not "more infrastructure". The next target is better
product intelligence and better presentation.

The approved post-P0 sequence is:

1. `P1a Reasoning / Synthesis Layer`
2. `P1b Conversational Presentation Layer`
3. `P1c Pluggable Persona Contract`

In practical terms, this means:

- move from analytical payload formatting to true grounded advisory synthesis
- make the default user-facing answer feel like chatting with a coach
- make persona deeper than a thin style wrapper
- keep the truth layer deterministic and inspectable

## 7. What This Project Is Not

This project is currently **not**:

- a general-purpose chatbot
- an official Tencent / 洛克王国 product
- a pure roleplay character app
- a web-search-powered meta predictor
- a long-memory autonomous agent

It also does **not** currently promise:

- authoritative live meta analysis
- future balance prediction
- full species-set optimization
- unrestricted persona generation in the shipped product

## 8. Short External Summary

If a zero-context external reader only remembers one paragraph, it should be
this:

`Roco` is an unofficial `洛克王国世界` battle-advisor project. It already has a
working deterministic analysis core, structured species data access, API
boundary, and mobile scaffold. The next step is to upgrade it from
"correct-but-structured analysis output" into a product that feels like talking
to a grounded tactical coach, using LLM reasoning on top of deterministic facts
without letting the model invent truth.
