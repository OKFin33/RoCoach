# P14 S2 Patch Delta Gate v0

Date: 2026-05-23
Scope: Roco dataset pipeline planning and candidate ingestion only.

## Purpose

The 2026-05-21 S2 update changed existing species stats, abilities, move pools,
and move effects. Post-S2 PvP sources can still be collected, but any candidate
derived from them must carry an explicit game epoch and cannot be promoted into
runtime or A-layer truth until the S2 delta is reconciled.

This gate lets image/manual patch evidence reduce drift without pretending it is
runtime A-layer data. Official patch notes may upgrade source reliability, but
they still do not authorize direct DB overwrite or runtime graph promotion.

## Inputs

- Community or official-looking patch screenshots.
- User-supplied patch notes.
- Official patch-note text and images captured from the game's official site.
- Later official/runtime-confirmed A-layer exports.
- Post-S2 video/text sources.

## Required Fields

Every patch delta pack must record:

- `schema_version`
- `game_epoch`
- `patch_date`
- `source_type`
- `runtime_allowed: false`
- image/source path and hash
- source reliability
- extracted deltas by category
- extraction confidence
- `requires_pm_review`
- `requires_a_layer_reconciliation`

Every extracted delta must record:

- affected entity name
- affected field or skill
- old value/effect when visible
- new value/effect when visible
- source image id
- confidence
- review status

## Promotion Rules

Patch image evidence may be used for:

- source discovery priority
- drift warnings
- post-S2 candidate quarantine
- review packet preparation
- A-layer reconciliation checklist

Patch image evidence may not be used for:

- overwriting A-layer battle-dex values
- runtime answer generation
- reviewed KG promotion
- claiming runtime-observed S2 correctness

## Candidate Routing

For post-S2 sources:

1. If a source discusses an entity in the patch delta pack, attach
   `game_epoch: post_s2_candidate`.
2. If a candidate depends on changed stats, abilities, move pools, or effects,
   mark `blocked_by: s2_a_layer_reconciliation`.
3. If the source only provides team/set usage and does not depend on changed
   mechanics, it may enter candidate inventory with `runtime_allowed: false`.
4. Any promoted item after 2026-05-21 must cite a reconciled A-layer snapshot.

## Acceptance Before Production Resume

Before large-scale autorun resumes, the project needs:

1. One durable S2 patch delta pack.
2. A checked A-layer reconciliation plan for changed existing species and moves.
3. A source policy note saying how post-S2 sources are tagged.
4. A validator or dashboard check that reports unresolved S2 blockers.

New S2 species remain out of scope until their base A-layer records exist.

## Current Official Source Capture

As of 2026-05-23, the official article `S2赛季平衡性调整说明`
(`newsid=18788872`) has been captured from the official site after discovery
through the `S2赛季更新公告` article (`newsid=18788208`). This upgrades the S2
delta pack from community-reference evidence to official patch-note evidence.
It does not change the promotion rule: candidate overlays remain non-runtime
until PM/review gates and a versioned runtime/A-layer snapshot exist.

## Reusable Season Update Discovery Pattern

For later seasons, check official update pages before community screenshots:

```text
https://rocom.qq.com/web202507/sub/detail.html?newsid=<news_id>
https://apps.game.qq.com/wmp/v3.1/public/searchNews.php?p0=467&source=web_pc&id=<news_id>
```

The detail page can be image-heavy or JS-rendered, while `searchNews.php`
returns article metadata, HTML content, image URLs, and related-news links. For
S2, the main update article (`18788208`) pointed to the balance article
(`18788872`) through this metadata, and the balance article contained usable
structured HTML text. Future patch-delta ingestion should try this route before
OCR, then preserve the raw API response, HTML, text projection, image assets,
hashes, and source manifest under `data/knowledge_graph/v0/patch_deltas/`.
