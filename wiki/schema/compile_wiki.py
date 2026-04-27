#!/usr/bin/env python3
"""Compile reviewed Battle Wiki pages into LLM-readable exports."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WIKI = ROOT / "wiki"
PAGES = WIKI / "pages"
COMPILED = WIKI / "compiled"
COMPILER_VERSION = "battle-wiki-compiler-v0.1"


def _parse_scalar(value: str):
    value = value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].splitlines()
    body = text[end + 5 :]
    meta: dict[str, object] = {}
    current_key: str | None = None
    for line in raw:
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            meta.setdefault(current_key, [])
            assert isinstance(meta[current_key], list)
            meta[current_key].append(_parse_scalar(line[4:]))
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            meta[key] = [] if value == "" else _parse_scalar(value)
    return meta, body


def page_id(path: Path) -> str:
    return path.relative_to(WIKI).as_posix()


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(path: Path, meta: dict, body: str) -> list[dict]:
    chunks = []
    sections = []
    current_title = "Front"
    current_lines: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line[3:].strip()
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    for idx, (section, text) in enumerate(sections):
        if text:
            chunks.append(
                {
                    "chunk_id": f"{page_id(path)}#{idx}",
                    "page": page_id(path),
                    "title": meta.get("title", path.stem),
                    "content_class": meta.get("content_class", ""),
                    "confidence": meta.get("confidence", ""),
                    "section": section,
                    "text": text,
                    "sources": meta.get("sources", []),
                    "a_layer_refs": meta.get("a_layer_refs", []),
                }
            )
    return chunks


def lint_page(path: Path, meta: dict, body: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    required = ["title", "content_class", "status", "confidence", "sources", "last_reviewed", "persona_free"]
    if meta.get("status") == "reviewed":
        for key in required:
            if key not in meta or meta.get(key) in ("", []):
                errors.append(f"{page_id(path)} missing reviewed metadata: {key}")
    if meta.get("persona_free") is not True:
        errors.append(f"{page_id(path)} is not persona_free")
    body_lower = body.lower()
    for token in ["enzo", "persona voice", "roleplay"]:
        if token in body_lower:
            errors.append(f"{page_id(path)} possible persona contamination: {token}")
    for token in ["pokemon", "宝可梦"]:
        has_boundary = any(
            phrase in body_lower
            for phrase in [
                "do not import",
                "not import",
                "cannot import",
                "without explicit",
                "cross-game analogies cannot",
            ]
        )
        if token in body_lower and not has_boundary:
            errors.append(f"{page_id(path)} cross-game term needs explicit boundary: {token}")
    required_sections = [
        "## Claim",
        "## Strategic Use",
        "## Evidence",
        "## Confidence",
        "## A-Layer Boundary",
        "## Known Failure Modes",
    ]
    if meta.get("status") == "reviewed" and meta.get("content_class") != "casebank":
        for section in required_sections:
            if section not in body:
                errors.append(f"{page_id(path)} missing required section: {section}")
    return errors, warnings


def lint_directory_readmes(reviewed_pages_by_dir: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    inventory_pattern = re.compile(r"^- `([^/`]+\.md)`$", re.MULTILINE)

    for directory in sorted(reviewed_pages_by_dir):
        readme_path = PAGES / directory / "README.md"
        if not readme_path.exists():
            continue
        text = readme_path.read_text(encoding="utf-8")
        if "Current reviewed pages:" not in text:
            continue

        documented = sorted(set(inventory_pattern.findall(text)))
        actual = sorted(reviewed_pages_by_dir[directory])

        missing = [name for name in actual if name not in documented]
        extra = [name for name in documented if name not in actual]
        if missing or extra:
            detail_parts = []
            if missing:
                detail_parts.append(f"missing={missing}")
            if extra:
                detail_parts.append(f"extra={extra}")
            errors.append(
                f"pages/{directory}/README.md reviewed inventory drift: "
                + ", ".join(detail_parts)
            )

    return errors, warnings


def main() -> int:
    COMPILED.mkdir(parents=True, exist_ok=True)
    pages = []
    excluded = []
    errors = []
    warnings = []
    chunks = []
    page_hashes = {}
    reviewed_pages_by_dir: dict[str, list[str]] = {}

    for path in sorted(PAGES.glob("*/*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        rel = page_id(path)
        page_hashes[rel] = sha256(text)
        status = meta.get("status")
        if status != "reviewed":
            excluded.append({"page": rel, "reason": f"status={status or 'missing'}"})
            continue
        page_errors, page_warnings = lint_page(path, meta, body)
        errors.extend(page_errors)
        warnings.extend(page_warnings)
        if meta.get("confidence") != "confirmed":
            warnings.append(f"{rel} confidence={meta.get('confidence')}")
        pages.append({"path": rel, "meta": meta, "body": body})
        directory = path.parent.relative_to(PAGES).as_posix()
        reviewed_pages_by_dir.setdefault(directory, []).append(path.name)
        chunks.extend(chunk_text(path, meta, body))

    readme_errors, readme_warnings = lint_directory_readmes(reviewed_pages_by_dir)
    errors.extend(readme_errors)
    warnings.extend(readme_warnings)

    built_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
    llms_lines = [
        "# Roco Battle Wiki LLM Context",
        "",
        f"Built at: {built_at}",
        f"Compiler: {COMPILER_VERSION}",
        "",
        "## Runtime Rules",
        "",
        "- This is B-layer doctrine, not A-layer fact authority.",
        "- Exact species, move, ability, type-chart, stat, and formula facts must be checked against A-layer references.",
        "- Roco is not Pokemon; cross-game analogies cannot import mechanics.",
        "- Persona/style overlays must not alter default B doctrine.",
        "- Provisional pages can guide soft reasoning but must preserve uncertainty.",
        "",
        "## Reviewed Pages",
    ]
    for p in pages:
        meta = p["meta"]
        llms_lines.append(f"- {p['path']} | {meta.get('content_class')} | {meta.get('confidence')} | {meta.get('title')}")

    llms_full = list(llms_lines)
    for p in pages:
        meta = p["meta"]
        a_refs = meta.get("a_layer_refs", [])
        if not isinstance(a_refs, list):
            a_refs = []
        llms_full.extend(
            [
                "",
                "---",
                "",
                f"# {meta.get('title', p['path'])}",
                "",
                f"Path: {p['path']}",
                f"Class: {meta.get('content_class', '')}",
                f"Confidence: {meta.get('confidence', '')}",
                f"A-layer refs: {', '.join(a_refs)}",
                "",
                p["body"].strip(),
            ]
        )

    graph_edges = []
    for p in pages:
        meta = p["meta"]
        refs = []
        for key in ("a_layer_refs", "sources"):
            value = meta.get(key, [])
            if isinstance(value, list):
                refs.extend((key, item) for item in value)
        for key, ref in refs:
            graph_edges.append(
                {
                    "from": p["path"],
                    "to": ref,
                    "type": "a_layer_ref" if key == "a_layer_refs" else "source_ref",
                }
            )

    graph = {
        "nodes": [
            {
                "id": p["path"],
                "title": p["meta"].get("title", ""),
                "content_class": p["meta"].get("content_class", ""),
                "confidence": p["meta"].get("confidence", ""),
                "sources": p["meta"].get("sources", []),
                "a_layer_refs": p["meta"].get("a_layer_refs", []),
            }
            for p in pages
        ],
        "edges": graph_edges,
    }

    manifest = {
        "built_at": built_at,
        "compiler_version": COMPILER_VERSION,
        "source_pages": [p["path"] for p in pages],
        "excluded_pages": excluded,
        "page_hashes": page_hashes,
        "a_layer_snapshots": sorted(
            {
                ref
                for p in pages
                for ref in (p["meta"].get("a_layer_refs", []) if isinstance(p["meta"].get("a_layer_refs", []), list) else [])
            }
        ),
        "warnings": warnings,
    }

    if errors:
        print(f"errors {len(errors)}")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    (COMPILED / "llms.txt").write_text("\n".join(llms_lines) + "\n", encoding="utf-8")
    (COMPILED / "llms-full.txt").write_text("\n".join(llms_full) + "\n", encoding="utf-8")
    (COMPILED / "chunks.jsonl").write_text(
        "".join(json.dumps(chunk, ensure_ascii=False) + "\n" for chunk in chunks), encoding="utf-8"
    )
    (COMPILED / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Keep this as JSON-valid YAML so lightweight consumers can parse it
    # without requiring a YAML dependency.
    (COMPILED / "manifest.yaml").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"compiled {len(pages)} reviewed pages")
    print(f"excluded {len(excluded)} pages")
    print(f"warnings {len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
