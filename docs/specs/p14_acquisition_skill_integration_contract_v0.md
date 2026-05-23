# P14 Acquisition Skill Integration Contract v0

Status: planning contract
Date: 2026-05-22
Scope: source acquisition skill boundary and Roco import contract
Runtime effect: none

This document is the DP-10 output for the dataset pipeline planning package.
It defines how an upgraded `social-media-reader` / Scribe-style acquisition
skill may feed Roco. It does not ingest sources, produce KG candidates, accept
Gold, materialize graph assets, or change runtime behavior.

## 1. Boundary

The acquisition skill layer is capability infrastructure, not the dataset.

It may:

- find or receive social/video source links;
- route each source to a platform-specific transcript path;
- preserve source metadata, transcript artifacts, and acquisition logs;
- emit a `source_transcript_bundle`;
- report acquisition quality and unresolved access/transcript issues.

It must not:

- produce reviewed KG facts;
- produce Gold/Eval items;
- promote source claims into Set Graph, mechanism rules, or D-layer cases;
- bypass Roco provenance, A/B refinement, quality gates, or review;
- store or expose cookies, provider keys, or platform credentials.

Product consequence: Roco can become faster at collecting readable source
material without letting a broad scraper/transcriber become an ungoverned
knowledge pipeline.

## 2. Skill Roles

| Layer | Owner | Output | Dataset authority |
|---|---|---|---|
| `social-media-reader` v2 | cross-platform acquisition skill | `source_transcript_bundle` | none |
| Scribe or local/video tool | optional transcript producer/import source | transcript files and segments | none |
| Roco ingest adapter | Roco project tooling | AB-refined transcript and evidence manifest | substrate only |
| Roco dataset pipeline | P14 contracts | KG/Gold/Eval candidates and review state | governed candidates |

The same media source can pass through multiple acquisition tools. The Roco
import side records the transform lineage instead of treating the newest text
as inherently better.

## 3. Platform Router v0

| Source class | Preferred first path | Fallback path | Roco import note |
|---|---|---|---|
| Bilibili video | `roco-video-ingest` subtitle-first with Chrome cookies when needed | third-party ASR or Scribe/local Whisper for no-subtitle cases | run AB refinement before extraction |
| Douyin video | CDP/Doubao transcript path if it returns full transcript | Scribe/yt-dlp/local or cloud ASR where legal and available | reject summaries as transcript substitutes |
| Xiaohongshu post/video | DOM extraction plus optional OCR for image text | manual/Scribe transcript if video carries unique speech | separate post text, comments, OCR, and transcript spans |
| WeChat Channels/local video | Scribe desktop workflow when available | manual transcript import | keep file paths internal-only |
| Generic supported URL | Scribe/yt-dlp-style download and transcript | manual transcript import | platform metadata may be incomplete |
| Roco official season/update article | Official site detail page plus `searchNews.php` article endpoint | Chrome page inspection if endpoint shape changes | preferred source for season patch deltas; still candidate-only until Roco gates pass |

Fallback order is quality-sensitive, not convenience-sensitive. A clean platform
subtitle beats a low-quality ASR transcript. A third-party transcript beats local
Whisper only when it is complete, source-faithful, and not a summary.

### Roco Official Update Channel

Future season updates should first check the official news detail route:

```text
https://rocom.qq.com/web202507/sub/detail.html?newsid=<news_id>
```

The rendered page may not expose the article body as normal DOM text. The current
official data endpoint pattern is:

```text
https://apps.game.qq.com/wmp/v3.1/public/searchNews.php?p0=467&source=web_pc&id=<news_id>
```

For S2, `newsid=18788208` (`S2赛季更新公告`) linked to `newsid=18788872`
(`S2赛季平衡性调整说明`) through the article metadata. Agents should inspect
`linkList` / related news before falling back to screenshots or OCR.

## 4. `source_transcript_bundle` Schema

The acquisition skill emits one bundle per source or source segment group:

```yaml
schema_version: p14.source_transcript_bundle.v0
bundle_id: ""
created_at: ""
created_by:
  skill: social-media-reader
  skill_version: ""
  tool: ""
  tool_version: ""
source:
  platform: bilibili | douyin | xiaohongshu | wechat_channels | local_video | generic_url | unknown
  source_url: ""
  canonical_url: ""
  platform_source_id: ""
  uploader: ""
  title: ""
  published_at: ""
  discovered_by: ""
  source_type: team_explainer | mechanism_tutorial | matchup_explainer | gameplay | ranking_overview | post | unknown
  rights_state: internal_reference_only | source_metadata_only | unknown
acquisition:
  method: platform_subtitle | cdp_transcript | dom_text | ocr | scribe_local_whisper | cloud_asr | manual_transcript | other
  authenticated_session_used: false
  cookies_exported: false
  transcript_format: srt | vtt | txt | md | json | mixed
  asr_provider: none | bailian | local_whisper | scribe_whisper | other
  asr_model: ""
  hotword_vocab_id: ""
  llm_proofread_used: false
  glossary_used: false
artifacts:
  raw_subtitle_path: ""
  transcript_path: ""
  transcript_srt_path: ""
  transcript_json_path: ""
  acquisition_log_path: ""
  artifact_hashes: {}
segments:
  - segment_id: ""
    start_ms: 0
    end_ms: 0
    text: ""
    confidence: high | medium | low | unknown
    repair_status: clean | repaired | partial | unresolved
quality:
  transcript_status: clean | usable | partial | summary_like | missing
  asr_risk: none | low | medium | high
  unresolved_terms: []
  completeness_note: ""
  needs_audio_review: false
roco_import:
  roco_import_required: true
  ab_refinement_required: true
  extraction_allowed_before_import: false
  target_import_adapter: roco_external_transcript_import
runtime_allowed: false
```

Required invariants:

- `cookies_exported` must remain false.
- `rights_state` defaults to `internal_reference_only` or `unknown`.
- `extraction_allowed_before_import` must remain false.
- `runtime_allowed` must remain false.

## 5. Scribe Import Boundary

Scribe is useful as a local/video transcript producer because it can download or
receive media, run Whisper-style transcription, preserve segments/timestamps,
apply glossary/proofread passes, and export readable transcript artifacts.

Roco must integrate it by file boundary only:

- import exported transcript files or segment JSON;
- record Scribe version, transcript method, glossary/proofread use, and paths;
- treat Scribe output as transcript substrate, not structured Roco knowledge;
- do not vendor Scribe code into Roco planning/runtime without a license review;
- do not let Scribe glossary entries mutate Roco A/B canonical terms directly.

If Scribe output and platform subtitle disagree, both surfaces are preserved and
the Roco import adapter marks the affected spans for review.

## 6. Roco Import Adapter Requirements

Future Roco import work should convert `source_transcript_bundle` into the
existing Roco source substrate shape:

```text
source_transcript_bundle
-> source manifest
-> transcript artifact
-> AB refinement
-> evidence span manifest
-> review questions / unresolved terms
-> candidate extraction only after quality gate
```

Required behavior:

- preserve source URL, platform id, uploader, title, publish date, and method;
- preserve segment timestamps when available;
- run A-layer/B-layer term refinement before any set extraction;
- record every term repair as transform lineage;
- mark summaries and incomplete transcripts as `coverage_only` or reject;
- require source-quality status before extraction;
- keep all outputs internal-only unless a later rights policy changes this.

## 7. Quality Gates

An acquired bundle may enter Roco ingest only if:

- source metadata is sufficient to trace back to the original material;
- transcript is full enough for the intended source type;
- acquisition method is explicit;
- transcript artifacts are addressable by path or manifest;
- no credentials or cookies are stored;
- rights state is recorded.

It may enter candidate extraction only after:

- AB refinement completes or records why it cannot complete;
- unresolved terms are not on core promoted fields;
- source-quality prior is at least usable for the task;
- evidence spans exist for candidate claims.

## 8. Failure Modes

| Failure | Required action |
|---|---|
| platform tool returns summary, not transcript | reject for extraction; may remain coverage-only |
| transcript lacks timestamps | allowed for coarse evidence only; mark lower trace quality |
| source metadata incomplete | keep as raw research material, not dataset candidate |
| ASR uncertainty touches species/move/mechanism | mark unresolved; block extraction of that field |
| platform auth/cookie issue | report access blocker; do not export or inspect cookies |
| Scribe/local tool version unknown | mark transform lineage incomplete |
| rights state ambiguous | internal-only, no public dataset claim |

## 9. Acceptance Checklist

- acquisition outputs stop at `source_transcript_bundle`;
- bundle schema preserves source, acquisition method, artifacts, segments,
  quality, and rights;
- Roco AB refinement and provenance gates remain mandatory;
- Scribe integration is file-boundary import, not vendoring;
- no acquisition step can create KG, Gold, D-layer, or runtime data;
- credential leakage is explicitly forbidden.

## 10. Handoff

Future implementation should first upgrade `social-media-reader` into a
platform router that can emit the bundle schema above. Only after that should
Roco add a small import adapter that turns bundles into normal Roco ingest
substrate and runs the existing AB/provenance/quality gates.
