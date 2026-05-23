# P13 Meta Graph Round 1 Set Input Plan

Status: draft for execution
Date: 2026-05-16
Owner: PM review + agent automation

## Objective

Build the first useful Meta Graph input batch at enough scale to make the
runtime Agent consider multiple team structures, not only the current 光合武队
sample.

Round 1 should produce:

- `40-80` candidate set mentions from community sources;
- `20-30` PM-reviewable species_set card candidates;
- `15-25` promoted `reviewed` cards for runtime v0.1;
- `10-15` D-layer candidate judgement moments linked to those cards.

The goal is not raw transcript volume. The goal is coverage across archetypes,
roles, resource mechanics, and matchup/counterplay situations.

## Source Funnel

Use `$roco-video-ingest` or the equivalent manual workflow:

1. Bilibili URL or local transcript enters a run directory.
2. Try Chrome-login subtitle capture.
3. If no usable subtitles, use third-party transcription.
4. Run `tools/transcript_ab_refine.py`.
5. Produce:
   - AB-refined transcript;
   - review questions;
   - source manifest.

Source files and transcripts are source substrate only. They do not enter
runtime prompts directly.

## First-Round Sampling

Do not sample only ranking/list videos. Use three source types:

| Source Type | Target Count | Why |
|---|---:|---|
| team explainer / full composition | 6-8 videos | Best for complete set and synergy extraction |
| matchup / counterplay explainer | 4-6 videos | Forces threat/counterplay edges, not only synergy |
| tier list / config overview | 2-4 videos | Adds coverage and mainstreamness signals |

Target archetype coverage:

| Bucket | Minimum |
|---|---:|
| 光合武队 / energy-window team | 1-2 sources |
| 毒队 / poison-stall or balance poison | 2 sources |
| 星陨队 / mark detonation team | 2 sources |
| 翼王 balance / fast balance | 2 sources |
| 地面 / 沙暴 / resource-control team | 1-2 sources |
| 电 / 冷门高结构队 such as 电球咩咩 | 1 source |

Stop Round 1 when at least four archetype buckets have promoted reviewed cards.
Do not call Round 1 healthy if it only has one archetype with many cards.

## Candidate Levels

Automation must output candidate levels, not pretend everything is a card.

| Level | Required Fields | Output |
|---|---|---|
| L0 mention | species or archetype mention only | coverage signal only |
| L1 partial set | species + role/archetype + source span | PM review queue |
| L2 card candidate | species + selected moves or explicit config + role + source span + A-layer validation | unreviewed card candidate |
| L3 relation candidate | two sets + relation type + causal phrase/source span | edge candidate |
| L4 reviewed | PM confirms source fidelity and unresolved terms | `review_status: reviewed` |

Only L4 can enter runtime. L2/L3 may be written under artifacts, not under
runtime-active `reviewed` state.

## Automation Boundaries

Automation may:

- segment AB-refined transcript into source spans;
- detect A-layer species, moves, and abilities;
- fuzzy-suggest ASR names against Battle Dex;
- group nearby species/move mentions into candidate set blocks;
- infer weak role labels from source words such as `首发`, `联防`, `收割`, `清强化`;
- generate review packets;
- generate unreviewed YAML drafts when L2 fields are present.

Automation must not:

- mark a card as `reviewed`;
- invent missing selected moves;
- treat A/B exact hits as proof of source strategy;
- trust third-party summaries;
- promote unclear ASR names;
- generate shadow graph runtime data in Round 1.

## Candidate Extraction Schema

Write first-round extraction under:

```text
artifacts/meta_graph_round1_set_input/
  source_queue.yaml
  source_runs/<source_id>/...
  extracted/<source_id>.candidate_sets.yaml
  extracted/<source_id>.candidate_edges.yaml
  review_packets/<source_id>.pm_review.md
  round1_coverage_report.md
```

Candidate set shape:

```yaml
source_id: ""
source_ref: ""
candidate_sets:
  - candidate_id: "cand/<source_id>/set/001"
    level: "L2"
    source_span_ids: ["P003", "P004"]
    archetype_tags: ["蓄势印记队"]
    source_names:
      species: ["十菠萝", "立灯鱼", "雪影娃娃"]
      moves: ["蓄势待发", "赤子之心"]
    resolved:
      species:
        - raw: "十菠萝"
          canonical_species_name: ""
          canonical_species_id: ""
          resolution_status: "review_required"
      moves:
        - raw: "蓄势待发"
          canonical_move_name: "蓄势待发"
          resolution_status: "exact"
    inferred_roles:
      - species_name: ""
        role_labels: ["setup_core"]
        source_phrase: "首发"
    selected_moves:
      - species_name: ""
        moves: []
        completeness: "partial"
    unresolved_terms: []
    promotion_blockers:
      - "species_name_review_required"
```

Candidate edge shape:

```yaml
source_id: ""
candidate_edges:
  - candidate_id: "cand/<source_id>/edge/001"
    level: "L3"
    source_span_ids: ["P004", "P005"]
    source_species_or_sets: ["雪影娃娃", "古龙"]
    target_species_or_sets: ["音速犬"]
    edge_type: "synergy"
    source_claim: "把这个效果给古龙或者是音速犬"
    reasoning_quality: "partial_chain"
    unresolved_terms: []
```

## Promotion Gates

A candidate can become a Meta Graph card only if:

1. `canonical_species_id` resolves to Battle Dex.
2. Ability is read from A-layer, not the transcript.
3. Selected moves are either source-explicit or PM-filled.
4. Every selected move exists in Battle Dex.
5. Role label has a source phrase or PM confirmation.
6. Source span is traceable to an AB-refined transcript.
7. PM has reviewed unresolved ASR names.

Default card state after automated drafting:

```yaml
confidence: "observed"      # only if source explicitly states it
review_status: "unreviewed"
graph_origin: "human"
```

The PM promotion action changes only `review_status` and `review_date`; it
should not silently rewrite source claims.

## First Batch Recommendation

Start with `8-10` sources:

- `2` full team explainers from existing cache or new Bilibili links;
- `2` poison/starfall matchup sources from existing P10h transcripts;
- `2` wingking/balance sources from existing P10h transcripts;
- `2-4` newly ingested Bilibili sources via `$roco-video-ingest`.

This should yield enough diversity for:

- synergy edges;
- counterplay edges;
- resource-race edges;
- speed/lead/pivot cases;
- at least one unreliable/ASR-heavy source to test review workflow.

## Execution Phases

### Phase 1: Candidate Queue

Create `source_queue.yaml` with fields:

- `source_id`
- `url_or_path`
- `source_type`
- `target_archetype`
- `priority`
- `ingest_status`
- `expected_value`

### Phase 2: Ingest and Refine

For each source:

1. Run video ingest.
2. Resolve review questions.
3. Mark transcript quality:
   - `good`: can extract sets;
   - `usable`: can extract only partial sets;
   - `poor`: coverage only.

### Phase 3: Candidate Extraction

Use automation to draft candidate YAML. Keep every uncertain name as
`review_required`.

### Phase 4: PM Review Packet

Generate a short markdown packet per source:

- likely cards to promote;
- unresolved terms;
- source-span excerpts;
- expected product value;
- recommended accept/reject/fill decisions.

### Phase 5: Draft Unreviewed Cards

Only for L2 candidates. Draft cards into artifacts first:

```text
artifacts/meta_graph_round1_set_input/card_drafts/
```

After PM approval, copy/promote to:

```text
data/meta_graph/v0/species_sets/
```

Then rebuild:

```bash
PYTHONPATH=.:src .venv/bin/python -m tools.v2_generate_edge_index
PYTHONPATH=.:src .venv/bin/python -m tools.v2_generate_speed_index
PYTHONPATH=.:src .venv/bin/python -m tools.v2_validate_graph --strict
```

## V1 Sufficiency Bar

Round 1 is enough for V1 v0.1 only if:

- at least `15` reviewed cards exist;
- at least `4` archetype buckets are represented;
- at least `20` reviewed edges or relation claims exist;
- at least `10` D-layer candidate examples are linked to graph cards;
- Agent smoke answers improve on questions outside 光合武队.

If these are not met, the graph is still a pipeline proof, not a V1-ready
knowledge layer.
