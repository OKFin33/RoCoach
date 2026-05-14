# 爬取 Session Handoff Spec

## Purpose

Provide a self-sufficient handoff artifact so a completely new thread can resume the wiki discovery work without relying on hidden chat context.

This document is a continuation contract for the crawl / discovery track.

It captures:

- current crawl-related project state
- accepted crawl decisions
- verified wiki findings
- immediate next crawl actions
- explicit non-goals and risks

## Snapshot

As of `2026-04-13`, the project is in:

- `Phase 1.5` implemented for report generation
- `P1a` specified for wiki field discovery and ontology alignment

Current crawl-related direction remains:

- API-first
- evidence-backed field discovery
- no uncontrolled schema expansion
- no production ingestion yet

## Current Objective

The immediate continuity target is:

- continue `P1a` wiki field discovery with evidence-backed crawling strategy

This session did **not** implement a crawler yet.
It validated the target wiki structure and narrowed the correct discovery route.

## Source-of-Truth Artifacts

New thread should treat the following as primary internal references:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/combat_ontology.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/data_source_strategy.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/field_alignment_matrix.yaml`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/wiki_field_discovery_spec.md`

Secondary architectural context:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/docs/battle_analysis_architecture.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/report_layer.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/report_schema.yaml`

## Verified Findings From This Session

### 1. Target Wiki Is Technically Easy To Crawl

Target page inspected:

- `https://wiki.biligame.com/rocom/精灵图鉴`

Verified facts:

- the site is standard `MediaWiki`
- `api.php` is live and anonymous requests work
- page source can be fetched through `prop=revisions`
- category membership enumeration works

This means the crawl is a structured API job, not a browser automation problem.

### 2. `精灵图鉴` Is A Rendered Shell, Not The True Data Source

The `精灵图鉴` page source delegates to:

- `精灵图鉴/原始形态`
- `精灵图鉴/地区形态`
- `精灵图鉴/首领形态`

Those pages use `#ask` queries over `[[分类:精灵]]` to render cards.

Implication:

- do **not** treat the index page DOM as the primary data source
- do **not** build selectors against rendered card HTML unless debugging

### 3. Species Detail Pages Carry Structured Template Data

Example validated page:

- `迪莫`

Observed structure:

- `{{精灵信息 ... }}` template

Observed stable-looking parameters include:

- `精灵名称`
- `精灵形态`
- `地区形态名称`
- `精灵阶段`
- `主属性`
- `2属性`
- `特性`
- `特性描述`
- `生命`
- `物攻`
- `魔攻`
- `物防`
- `魔防`
- `速度`
- `技能`
- `技能解锁等级`
- `血脉技能`
- `可学技能石`
- `更新版本`
- `进化条件`

Implication:

- species extraction should parse template parameters from page wikitext
- this is far more stable than scraping rendered presentation blocks

### 4. Category Enumeration Is Enough For Initial Species Discovery

Verified API route:

- `action=query&list=categorymembers&cmtitle=分类:精灵&cmlimit=max`

Verified category size during this session:

- approximately `591` pages

Verified anonymous page batch behavior:

- `cmlimit=max` returned `500` entries with continuation
- `generator=categorymembers` with `prop=revisions` also returned `500` pages per batch

Implication:

- full species page acquisition is a small batch job
- no complicated discovery layer is required

### 5. Recommended Crawl Path Is API-First

Recommended primary route:

1. enumerate titles from `分类:精灵`
2. fetch wikitext in batches via `api.php`
3. parse `{{精灵信息}}`
4. write evidence artifacts for `P1a`

Recommended API form:

- `action=query`
- `generator=categorymembers`
- `gcmtitle=分类:精灵`
- `gcmlimit=max`
- `prop=revisions`
- `rvprop=content|timestamp|ids`
- `rvslots=main`
- `format=json`

### 6. Robots Constraints Exist

Verified `robots.txt` disallows patterns including:

- `/*index.php?*`
- `/*特殊:*`

Implication:

- primary crawl path should use `api.php`
- `index.php?action=raw` should be used only for manual inspection, not bulk crawl design

## Accepted Strategic Decision

For species pages on this wiki:

- use `MediaWiki API`
- parse wikitext templates
- avoid HTML-first scraping
- avoid browser automation

This is now the default technical plan unless a later page type proves structurally different.

## Current Crawl-Track State

The crawl track has advanced beyond this handoff's original starting point.

Completed:

- a bounded `P1a` recon script exists at `tools/wiki_field_discovery_recon.py`
- a bounded `P1d` dry-run crawler/cleaner exists at `tools/wiki_battle_dex_dry_run.py`
- a P1c/P1d artifact validator exists at `tools/validate_p1c_artifacts.py`
- raw sample artifacts exist under `data/wiki_field_discovery/2026-04-13/`
- P1d dry-run artifacts exist under `data/wiki_ingestion_runs/2026-04-14T000000Z_p1d_dry_run/`
- aggregated candidate-field summary exists
- `specs/field_alignment_matrix.yaml` has been updated to version `2`
- species and move detail pages were validated as structured template sources
- ability was validated only as embedded species fields, not as standalone wiki pages
- `P1b` minimal battle dex schema has been drafted
- `P1c` crawler/cleaner output contract has been drafted

Still not approved:

- full production crawl
- SQLite ingestion
- standalone ability page crawling
- meta/community data ingestion

Current P1d dry-run result:

- `source_pages`: 10
- `species_form_candidates`: 5
- `move_candidates`: 5
- `derived_ability_candidates`: 5
- `species_move_pool_candidates`: 226
- `hard_reject`: 0
- `warning`: 229
- `unresolved_move_names`: 154
- `ability_conflicts`: 0

Known crawl risk:

- Biligame API returned intermittent `567` server errors during a rerun
- the dry-run tool now falls back from category enumeration to preferred titles when category listing fails
- repeated immediate reruns should be avoided; use bounded retries and sleep intervals
- a later broader bounded run from session `019d8685-2728-7c50-b102-59a5ee5f43ef` also failed on direct species page fetch with `567`
- do not retry broader crawl until API stability improves or a more polite/resumable strategy is specified

## Hard Constraints For The Next Thread

### Scope Constraints

New thread must stay inside the approved pre-ingestion track unless the user explicitly widens scope.

That means:

- bounded field discovery or bounded dry-run artifact generation
- page-structure verification
- evidence capture
- P1c-compliant artifact output

Not:

- full production ingestion
- database design freeze
- frontend work
- meta snapshot work

### Ontology Constraints

Do not import foreign assumptions.

In particular:

- do not assume `accuracy`
- do not assume `PP`
- do not assume canonical Pokemon-like move schema
- do not merge species and form semantics without evidence

### Evidence Constraints

For every discovered field:

- preserve raw source label
- preserve source page title
- preserve source URL or API identity
- preserve `pageid` and `revid` when available

### Parser Constraints

Preferred parser:

- `mwparserfromhell`

Reason:

- template values include multiline text, commas, Chinese punctuation, and optional blanks
- regex-only parsing is brittle garbage

## Recommended Next Execution Plan

### Step 1

Implement a species discovery script for `P1a`.

Expected responsibilities:

- pull category members from `分类:精灵`
- fetch page wikitext in API batches
- identify presence or absence of `精灵信息` template
- extract raw template parameters
- save raw evidence artifact

### Step 2

Generate an aggregated species field summary.

Expected output:

- field occurrence counts
- sample values
- pages containing each field
- fields that appear sparse or unstable

### Step 3

Map live species evidence back into:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/field_alignment_matrix.yaml`

Required behavior:

- promote fields only when evidence justifies it
- downgrade uncertain fields to `provisional`
- keep non-battle or weakly evidenced fields out of scope

### Step 4

Use the current P1c contract to generate bounded dry-run artifacts.

Required references:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1c_crawler_cleaner_contract.md`
- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/wiki_crawler_cleaner_contract.yaml`

Do not assume ability pages exist independently.

## Deliverables Expected From The Next Thread

The next crawl-focused thread should aim to produce:

1. no immediate broader crawl while API `567` persists
2. a polite/resumable fetch strategy if online execution is still required
3. a broader but still bounded P1d dry-run only when API is stable
4. JSON/JSONL parse validation
5. unresolved move-name reduction by crawling a larger move page sample
6. review of any ability conflicts
7. only then a SQLite ingestion dry-run design

Optional but useful:

- a short crawl-risk memo
- parser edge-case notes

## Open Questions

The next thread should explicitly resolve these questions:

1. Is `精灵编号` stable across all forms, or only base forms?
2. Should `精灵形态` and `地区形态名称` map to one `form_name` concept or two separate concepts?
3. Do any stronger sources for standalone ability entities exist, or should ability remain derived from species fields?
4. Which species fields are battle-relevant but should still remain `forbidden_by_default`?
5. Is there any template variation across region / boss / original forms that changes parser assumptions?

## Do-Not-Do List

New thread must not:

- switch to browser automation
- scrape rendered HTML cards as the primary data source
- perform full ingestion into a battle database
- silently assume move schema from another game
- widen scope into Phase 2 implementation

## Suggested Opening Prompt For The New Crawl Thread

> Read `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/爬session.md`, `/Users/okfin3/project/GitHub/OKFin33/Roco/log/project_log.md`, `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1c_crawler_cleaner_contract.md`, `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/wiki_crawler_cleaner_contract.yaml`, `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/battle_dex_schema.yaml`, and `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/field_alignment_matrix.yaml`. Then continue from the existing P1d dry-run tool at `/Users/okfin3/project/GitHub/OKFin33/Roco/tools/wiki_battle_dex_dry_run.py`. Run only bounded dry-runs, validate with `/Users/okfin3/project/GitHub/OKFin33/Roco/tools/validate_p1c_artifacts.py`, and do not mutate SQLite.

## Current Approved Crawl Request

The current approved next crawl action is move-first, not species expansion:

- `/Users/okfin3/project/GitHub/OKFin33/Roco/specs/p1d_move_full_bounded_dry_run_request.md`

Goal:

- build fuller `move` dictionary artifacts from `分类:技能` / `{{技能信息}}`
- reduce later `species_move_pool` unresolved noise

Hard boundary:

- do not expand species crawl for this task
- do not mutate SQLite
- do not crawl standalone ability pages
