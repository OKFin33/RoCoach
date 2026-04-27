# Battle Wiki Compile Protocol

Compiled exports turn reviewed pages into AI-readable context.

Planned outputs:

```text
wiki/compiled/llms.txt
wiki/compiled/llms-full.txt
wiki/compiled/chunks.jsonl
wiki/compiled/graph.json
wiki/compiled/manifest.yaml
```

## Required Manifest Fields

```yaml
built_at: ""
compiler_version: ""
source_pages: []
excluded_pages: []
page_hashes: {}
a_layer_snapshots: []
warnings: []
```

## Compile Rules

- exclude `draft` pages by default
- exclude `deprecated` pages from default runtime context
- warn on missing review date
- warn on low-confidence pages
- fail on persona contamination
- fail on unapproved cross-game mechanic migration
- record page hashes
- record A-layer snapshot references when used

Runtime consumers should read compiled exports, not traverse raw wiki pages
directly.

## Current Compiler

Run from the repository root:

```bash
python3 wiki/schema/compile_wiki.py
```

The current compiler includes `reviewed` pages, excludes draft/deprecated pages,
records page hashes, and emits provisional-confidence warnings into
`wiki/compiled/manifest.yaml`.
