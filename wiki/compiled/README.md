# Battle Wiki Compiled Exports

This directory is reserved for AI-readable exports generated from reviewed wiki
pages.

Planned artifacts:

```text
llms.txt
llms-full.txt
chunks.jsonl
graph.json
manifest.yaml
```

Compiled files must be reproducible and must include source page hashes,
confidence metadata, stale-page warnings, and excluded-page reasons.

## Current Compiler

Regenerate from repository root:

```bash
python3 wiki/schema/compile_wiki.py
```

Current outputs:

- `llms.txt`: short runtime index and hard rules
- `llms-full.txt`: full reviewed-page context
- `chunks.jsonl`: section-level retrieval chunks
- `graph.json`: page/source/A-layer reference graph
- `manifest.yaml`: build metadata, hashes, exclusions, warnings
