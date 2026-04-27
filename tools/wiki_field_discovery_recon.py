#!/usr/bin/env python3
"""Bounded P1a wiki field discovery for the rocom Biligame wiki.

This script performs reconnaissance only. It fetches index pages, samples detail
pages, extracts candidate fields from wikitext templates / SMW ask blocks, and
emits evidence artifacts. It does not build or mutate a database.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import mwparserfromhell
import requests


API_BASE_URL = "https://wiki.biligame.com/rocom/api.php"
PAGE_BASE_URL = "https://wiki.biligame.com/rocom/"
DEFAULT_USER_AGENT = "RocoP1aFieldDiscovery/0.1 (bounded recon; no database ingestion)"
DEFAULT_OUTPUT_DIR = Path("data/wiki_field_discovery/2026-04-13")
REQUEST_RETRIES = 3
REQUEST_BACKOFF_SECONDS = 1.5
TITLE_BATCH_SIZE = 40
EXAMPLE_LIMIT = 5


ENTITY_CONFIGS: dict[str, dict[str, Any]] = {
    "species": {
        "category": "分类:精灵",
        "index_pages": ["精灵图鉴", "精灵图鉴/原始形态", "精灵图鉴/地区形态", "精灵图鉴/首领形态"],
        "detail_template": "精灵信息",
        "preferred_titles": ["迪莫", "阿布", "火花", "果冻"],
        "variation_keywords": ["（", "首领", "地区"],
    },
    "move": {
        "category": "分类:技能",
        "index_pages": ["技能图鉴", "技能筛选"],
        "detail_template": "技能信息",
        "preferred_titles": ["暴风眼", "暗突袭", "孢子"],
        "variation_keywords": [],
    },
    "ability": {
        "category": None,
        "index_pages": ["特性图鉴", "特性列表", "特性"],
        "detail_template": None,
        "embedded_source_entity": "species",
        "embedded_fields": ["特性", "特性描述"],
        "category_candidates": ["分类:特性", "分类:能力"],
        "search_prefixes": ["特性"],
    },
}


CONFIRMED_FIELDS: dict[str, set[str]] = {
    "species": {
        "精灵名称",
        "精灵形态",
        "精灵阶段",
        "主属性",
        "2属性",
        "特性",
        "特性描述",
        "生命",
        "物攻",
        "魔攻",
        "物防",
        "魔防",
        "速度",
        "技能",
        "技能解锁等级",
        "血脉技能",
        "可学技能石",
    },
    "move": {"技能名称", "属性", "技能类别", "耗能", "威力", "效果"},
    "ability": {"特性", "特性描述"},
}


PROVISIONAL_FIELDS: dict[str, set[str]] = {
    "species": {"地区形态名称", "精灵初阶名称"},
    "move": {"描述", "技能版本"},
    "ability": set(),
}


FORBIDDEN_FIELDS: dict[str, set[str]] = {
    "species": {
        "是否有异色",
        "精灵类型",
        "精灵描述",
        "体型",
        "重量",
        "分布地区",
        "图鉴课题",
        "课题技能石",
        "是否有错别字",
        "宠物立绘形态",
        "进化条件",
        "更新版本",
    },
    "move": set(),
    "ability": set(),
}


NEGATIVE_ASSUMPTIONS: dict[str, list[dict[str, str]]] = {
    "move": [
        {
            "field": "accuracy",
            "recommendation": "forbidden_by_default",
            "reason": "No sampled `技能信息` template exposed accuracy / 命中 fields.",
        },
        {
            "field": "pp",
            "recommendation": "forbidden_by_default",
            "reason": "No sampled `技能信息` template exposed PP / usage-count fields.",
        },
        {
            "field": "cooldown",
            "recommendation": "forbidden_by_default",
            "reason": "No sampled `技能信息` template exposed a stable cooldown field.",
        },
    ],
    "ability": [
        {
            "field": "numeric_modifier",
            "recommendation": "forbidden_by_default",
            "reason": "Numeric modifiers appear only inside raw effect text in this pass, not as a stable structured ability field.",
        }
    ],
}


INDEX_ASK_FIELD_PATTERN = re.compile(r"^\|\?([^|\n=]+)", re.MULTILINE)


@dataclass(frozen=True)
class PageRevision:
    title: str
    pageid: int | None
    fullurl: str
    revid: int | None
    timestamp: str | None
    content: str
    missing: bool = False


class MediaWikiClient:
    def __init__(self, api_base_url: str, user_agent: str, sleep_seconds: float, timeout_seconds: float) -> None:
        self.api_base_url = api_base_url
        self.sleep_seconds = sleep_seconds
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def get(self, params: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(REQUEST_RETRIES):
            try:
                response = self.session.get(self.api_base_url, params=params, timeout=self.timeout_seconds)
                response.raise_for_status()
                if self.sleep_seconds > 0:
                    time.sleep(self.sleep_seconds)
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt < REQUEST_RETRIES - 1:
                    time.sleep(REQUEST_BACKOFF_SECONDS * (attempt + 1))
        raise RuntimeError(f"MediaWiki API request failed after {REQUEST_RETRIES} attempts: {last_error}") from last_error

    def get_category_info(self, category_title: str) -> dict[str, Any]:
        data = self.get(
            {
                "action": "query",
                "titles": category_title,
                "prop": "categoryinfo",
                "format": "json",
            }
        )
        pages = data.get("query", {}).get("pages", {})
        return next(iter(pages.values()), {})

    def get_category_members(self, category_title: str, limit: int | None = None) -> list[dict[str, Any]]:
        members: list[dict[str, Any]] = []
        params: dict[str, Any] = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category_title,
            "cmlimit": "max",
            "format": "json",
        }
        while True:
            data = self.get(params)
            batch = data.get("query", {}).get("categorymembers", [])
            members.extend(batch)
            if limit is not None and len(members) >= limit:
                return members[:limit]
            continuation = data.get("continue")
            if not continuation:
                return members
            params.update(continuation)

    def get_allpages_by_prefix(self, prefix: str, limit: int = 20) -> list[dict[str, Any]]:
        data = self.get(
            {
                "action": "query",
                "list": "allpages",
                "apprefix": prefix,
                "apnamespace": 0,
                "aplimit": limit,
                "format": "json",
            }
        )
        return data.get("query", {}).get("allpages", [])

    def get_pages(self, titles: Iterable[str]) -> list[PageRevision]:
        title_list = list(dict.fromkeys(titles))
        pages: list[PageRevision] = []
        for start in range(0, len(title_list), TITLE_BATCH_SIZE):
            batch = title_list[start : start + TITLE_BATCH_SIZE]
            data = self.get(
                {
                    "action": "query",
                    "titles": "|".join(batch),
                    "prop": "revisions|info",
                    "inprop": "url",
                    "rvprop": "content|timestamp|ids",
                    "rvslots": "main",
                    "format": "json",
                }
            )
            for page in data.get("query", {}).get("pages", {}).values():
                revision = (page.get("revisions") or [{}])[0]
                content = revision.get("slots", {}).get("main", {}).get("*") or revision.get("*") or ""
                title = page.get("title", "")
                pages.append(
                    PageRevision(
                        title=title,
                        pageid=page.get("pageid"),
                        fullurl=page.get("fullurl") or page_url(title),
                        revid=revision.get("revid"),
                        timestamp=revision.get("timestamp"),
                        content=content,
                        missing="missing" in page,
                    )
                )
        return pages


def page_url(title: str) -> str:
    return f"{PAGE_BASE_URL}{quote(title.replace(' ', '_'), safe='/')}"


def clean_value(value: str) -> str:
    collapsed = re.sub(r"\s+", " ", value.replace("\u200e", "")).strip()
    return collapsed


def template_name(template: Any) -> str:
    return clean_value(str(template.name).strip())


def extract_named_template_fields(content: str, target_template: str) -> tuple[list[dict[str, Any]], list[str]]:
    wikicode = mwparserfromhell.parse(content)
    fields: list[dict[str, Any]] = []
    templates_seen: list[str] = []
    for template in wikicode.filter_templates(recursive=True):
        name = template_name(template)
        templates_seen.append(name)
        if name != target_template:
            continue
        for param in template.params:
            if not param.showkey:
                continue
            raw_label = clean_value(str(param.name))
            value = clean_value(str(param.value))
            fields.append(
                {
                    "raw_label": raw_label,
                    "normalized_label": normalize_label(raw_label),
                    "source": f"template:{target_template}",
                    "example_value": value,
                }
            )
    return fields, sorted(set(templates_seen))


def extract_index_fields(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    fields: list[dict[str, Any]] = []
    ask_labels = [clean_value(match.group(1)) for match in INDEX_ASK_FIELD_PATTERN.finditer(content)]
    for label in ask_labels:
        if not label:
            continue
        fields.append(
            {
                "raw_label": label,
                "normalized_label": normalize_label(label),
                "source": "smw_ask_projection",
                "example_value": "",
            }
        )

    filter_values: list[str] = []
    wikicode = mwparserfromhell.parse(content)
    for template in wikicode.filter_templates(recursive=True):
        if template_name(template) != "筛选项":
            continue
        params = [clean_value(str(param.value)) for param in template.params]
        if len(params) >= 3:
            filter_values.append(params[2])

    if filter_values:
        fields.append(
            {
                "raw_label": "筛选项",
                "normalized_label": "筛选项",
                "source": "filter_template",
                "example_value": ", ".join(filter_values[:EXAMPLE_LIMIT]),
            }
        )

    templates_seen = sorted({template_name(template) for template in wikicode.filter_templates(recursive=True)})
    return fields, templates_seen


def normalize_label(raw_label: str) -> str:
    return raw_label.strip().replace("　", " ")


def example_values(fields: list[dict[str, Any]]) -> dict[str, list[str]]:
    values: dict[str, list[str]] = defaultdict(list)
    for field in fields:
        label = field["raw_label"]
        value = field.get("example_value", "")
        if value and value not in values[label]:
            values[label].append(value)
    return {label: vals[:EXAMPLE_LIMIT] for label, vals in values.items()}


def field_source_mode(fields: list[dict[str, Any]]) -> str:
    sources = {field["source"].split(":", 1)[0] for field in fields}
    if not fields:
        return "free_text_only"
    if sources <= {"template", "smw_ask_projection", "filter_template"}:
        return "structured_block"
    if "template" in sources or "smw_ask_projection" in sources:
        return "mixed"
    return "label_value_pair"


def make_page_sample(
    *,
    entity_type: str,
    page_type: str,
    page: PageRevision,
    fields: list[dict[str, Any]],
    templates_seen: list[str],
) -> dict[str, Any]:
    return {
        "entity_type": entity_type,
        "page_type": page_type,
        "source_url": page.fullurl,
        "page_title": page.title,
        "pageid": page.pageid,
        "revid": page.revid,
        "revision_timestamp": page.timestamp,
        "field_source_mode": field_source_mode(fields),
        "candidate_fields": fields,
        "example_values": example_values(fields),
        "templates_seen": templates_seen,
        "missing": page.missing,
    }


def select_sample_titles(
    members: list[dict[str, Any]],
    preferred_titles: list[str],
    variation_keywords: list[str],
    detail_limit: int,
) -> list[str]:
    member_titles = [member["title"] for member in members if member.get("ns") == 0]
    member_title_set = set(member_titles)
    selected: list[str] = []

    for title in preferred_titles:
        if title in member_title_set and title not in selected:
            selected.append(title)

    for title in member_titles:
        if len(selected) >= detail_limit:
            break
        if title not in selected:
            selected.append(title)

    for keyword in variation_keywords:
        for title in member_titles:
            if keyword in title and title not in selected:
                selected.append(title)
                break
        if len(selected) >= detail_limit + max(1, len(variation_keywords)):
            break

    return selected[: max(detail_limit, len(selected))]


def recommend_confidence(entity_type: str, raw_label: str, page_coverage_count: int, detail_sample_count: int) -> tuple[str, str]:
    if raw_label in FORBIDDEN_FIELDS.get(entity_type, set()):
        return "forbidden_by_default", "Observed but outside current battle-analysis scope or cosmetic/provenance-only."
    if raw_label in PROVISIONAL_FIELDS.get(entity_type, set()):
        return "provisional", "Observed as structured data, but semantic mapping or optionality needs review."
    if raw_label in CONFIRMED_FIELDS.get(entity_type, set()):
        if detail_sample_count == 0 or page_coverage_count >= max(2, min(5, detail_sample_count)):
            return "confirmed", "Repeated structured field with direct battle-analysis relevance."
        return "provisional", "Battle-relevant field, but sample coverage is too small for confirmation."
    if raw_label == "筛选项":
        return "provisional", "Index filter metadata; useful for page-structure discovery, not a domain field by itself."
    return "provisional", "Observed field without enough current policy to promote or forbid."


def aggregate_samples(samples: list[dict[str, Any]]) -> dict[str, Any]:
    entity_page_counts = Counter(sample["entity_type"] for sample in samples if sample["page_type"].endswith("_detail"))
    buckets: dict[tuple[str, str], dict[str, Any]] = {}

    for sample in samples:
        seen_in_page: set[tuple[str, str]] = set()
        is_detail_page = sample["page_type"].endswith("_detail")
        for field in sample["candidate_fields"]:
            entity = sample["entity_type"]
            normalized = field["normalized_label"]
            key = (entity, normalized)
            bucket = buckets.setdefault(
                key,
                {
                    "entity_type": entity,
                    "normalized_label": normalized,
                    "raw_labels": set(),
                    "field_sources": set(),
                    "source_page_types": set(),
                    "page_titles": set(),
                    "detail_page_titles": set(),
                    "index_page_titles": set(),
                    "occurrence_count": 0,
                    "page_coverage_count": 0,
                    "detail_page_coverage_count": 0,
                    "index_page_coverage_count": 0,
                    "example_values": [],
                },
            )
            bucket["occurrence_count"] += 1
            bucket["raw_labels"].add(field["raw_label"])
            bucket["field_sources"].add(field["source"])
            bucket["source_page_types"].add(sample["page_type"])
            if (entity, normalized) not in seen_in_page:
                bucket["page_titles"].add(sample["page_title"])
                bucket["page_coverage_count"] += 1
                if is_detail_page:
                    bucket["detail_page_titles"].add(sample["page_title"])
                    bucket["detail_page_coverage_count"] += 1
                else:
                    bucket["index_page_titles"].add(sample["page_title"])
                    bucket["index_page_coverage_count"] += 1
                seen_in_page.add((entity, normalized))
            example = field.get("example_value")
            if example and example not in bucket["example_values"]:
                bucket["example_values"].append(example)

    aggregate_fields = []
    for bucket in buckets.values():
        raw_labels = sorted(bucket["raw_labels"])
        primary_label = raw_labels[0]
        recommendation, notes = recommend_confidence(
            bucket["entity_type"],
            primary_label,
            bucket["detail_page_coverage_count"],
            entity_page_counts[bucket["entity_type"]],
        )
        detail_sample_count = entity_page_counts[bucket["entity_type"]]
        coverage_ratio = None
        if detail_sample_count:
            coverage_ratio = round(bucket["detail_page_coverage_count"] / detail_sample_count, 3)
        aggregate_fields.append(
            {
                "entity_type": bucket["entity_type"],
                "normalized_label": bucket["normalized_label"],
                "raw_labels": raw_labels,
                "occurrence_count": bucket["occurrence_count"],
                "page_coverage_count": bucket["page_coverage_count"],
                "detail_page_coverage_count": bucket["detail_page_coverage_count"],
                "index_page_coverage_count": bucket["index_page_coverage_count"],
                "detail_sample_count_for_entity": detail_sample_count,
                "detail_page_coverage_ratio": coverage_ratio,
                "source_page_types": sorted(bucket["source_page_types"]),
                "field_sources": sorted(bucket["field_sources"]),
                "example_values": bucket["example_values"][:EXAMPLE_LIMIT],
                "confidence_recommendation": recommendation,
                "recommendation_notes": notes,
            }
        )

    aggregate_fields.sort(key=lambda item: (item["entity_type"], item["confidence_recommendation"], item["normalized_label"]))
    return {
        "summary": {
            "sample_count": len(samples),
            "detail_sample_counts": dict(entity_page_counts),
        },
        "fields": aggregate_fields,
        "negative_assumptions": NEGATIVE_ASSUMPTIONS,
    }


def build_memo(run_metadata: dict[str, Any], samples: list[dict[str, Any]], aggregate: dict[str, Any]) -> str:
    sample_counts = Counter((sample["entity_type"], sample["page_type"]) for sample in samples)
    fields_by_status: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for field in aggregate["fields"]:
        fields_by_status[field["confidence_recommendation"]].append(field)

    lines = [
        "# Wiki Field Discovery Memo",
        "",
        "## Status",
        "",
        "- Scope: `P1a` reconnaissance only",
        "- Database ingestion: not performed",
        f"- Run timestamp: `{run_metadata['run_timestamp']}`",
        f"- API base: `{run_metadata['api_base_url']}`",
        "",
        "## Sample Coverage",
        "",
        "| Entity | Page Type | Count |",
        "| --- | --- | ---: |",
    ]

    for (entity, page_type), count in sorted(sample_counts.items()):
        lines.append(f"| {entity} | {page_type} | {count} |")

    lines.extend(
        [
            "",
            "## Page-Structure Findings",
            "",
            "- `species`: `分类:精灵` exists and sampled detail pages expose structured `{{精灵信息}}` template fields.",
            "- `move`: `分类:技能` exists and sampled detail pages expose structured `{{技能信息}}` template fields.",
            "- `ability`: no standalone `特性图鉴` / `特性列表` / `特性` page or `分类:特性` category was found in this pass; ability evidence is embedded in species `{{精灵信息}}` fields `特性` and `特性描述`.",
            "- Index pages use structured SMW `#ask` projections and filter templates; these are useful for discovery but are not the primary detail-source layer.",
            "",
            "## Candidate Field Recommendations",
            "",
        ]
    )

    for status in ["confirmed", "provisional", "forbidden_by_default"]:
        lines.extend([f"### {status}", "", "| Entity | Field | Coverage | Examples | Notes |", "| --- | --- | ---: | --- | --- |"])
        for field in sorted(fields_by_status.get(status, []), key=lambda item: (item["entity_type"], item["normalized_label"])):
            examples = "<br>".join(field["example_values"][:3]) if field["example_values"] else ""
            if field["detail_sample_count_for_entity"]:
                coverage = f"{field['detail_page_coverage_count']}/{field['detail_sample_count_for_entity']}"
                if field["index_page_coverage_count"]:
                    coverage = f"{coverage} + {field['index_page_coverage_count']} index"
            else:
                coverage = f"{field['page_coverage_count']} source"
            lines.append(
                f"| {field['entity_type']} | {field['normalized_label']} | {coverage} | {examples} | {field['recommendation_notes']} |"
            )
        if not fields_by_status.get(status):
            lines.append("| - | - | - | - | - |")
        lines.append("")

    lines.extend(["## Negative Assumption Guardrails", ""])
    for entity, items in aggregate["negative_assumptions"].items():
        for item in items:
            lines.append(f"- `{entity}.{item['field']}`: `{item['recommendation']}`. {item['reason']}")

    lines.extend(
        [
            "",
            "## Ingestion Risks",
            "",
            "- `ability` is not currently a standalone page type; treating it as an entity requires deriving ability records from species fields unless a stronger source is found.",
            "- `species` form semantics need review: `精灵形态` and `地区形态名称` are separate raw labels and should not be merged blindly.",
            "- `move` has stable `耗能` and `威力`, but no sampled field supports imported assumptions like accuracy or PP.",
            "- Cosmetic and encyclopedia fields are visible in structured species pages; they must remain excluded from the battle schema unless a battle use case is proven.",
            "",
            "## Proposed Next Step",
            "",
            "Use the aggregate artifact to update `specs/field_alignment_matrix.yaml` only where recommendations are evidence-backed. Do not start production ingestion until move/ability entity modeling is explicitly approved.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_recon(args: argparse.Namespace) -> dict[str, Path]:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    client = MediaWikiClient(
        api_base_url=args.api_base_url,
        user_agent=args.user_agent,
        sleep_seconds=args.sleep_seconds,
        timeout_seconds=args.timeout_seconds,
    )
    run_timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    run_metadata: dict[str, Any] = {
        "run_timestamp": run_timestamp,
        "api_base_url": args.api_base_url,
        "detail_limit": args.detail_limit,
        "output_dir": str(output_dir),
        "scope": "P1a field discovery only; no database ingestion",
    }

    samples: list[dict[str, Any]] = []
    discovery_notes: dict[str, Any] = {}
    detail_pages_by_entity: dict[str, list[PageRevision]] = {}

    for entity_type in ["species", "move"]:
        config = ENTITY_CONFIGS[entity_type]
        category = config["category"]
        category_info = client.get_category_info(category)
        members = client.get_category_members(category)
        selected_titles = select_sample_titles(
            members=members,
            preferred_titles=config["preferred_titles"],
            variation_keywords=config["variation_keywords"],
            detail_limit=args.detail_limit,
        )
        discovery_notes[entity_type] = {
            "category": category,
            "category_size": category_info.get("categoryinfo", {}).get("size"),
            "category_pages": category_info.get("categoryinfo", {}).get("pages"),
            "selected_detail_titles": selected_titles,
        }

        for page in client.get_pages(config["index_pages"]):
            if page.missing:
                continue
            fields, templates_seen = extract_index_fields(page.content)
            samples.append(
                make_page_sample(
                    entity_type=entity_type,
                    page_type=f"{entity_type}_index",
                    page=page,
                    fields=fields,
                    templates_seen=templates_seen,
                )
            )

        detail_pages = [page for page in client.get_pages(selected_titles) if not page.missing]
        detail_pages_by_entity[entity_type] = detail_pages
        for page in detail_pages:
            fields, templates_seen = extract_named_template_fields(page.content, config["detail_template"])
            samples.append(
                make_page_sample(
                    entity_type=entity_type,
                    page_type=f"{entity_type}_detail",
                    page=page,
                    fields=fields,
                    templates_seen=templates_seen,
                )
            )

    ability_config = ENTITY_CONFIGS["ability"]
    missing_index_titles: list[str] = []
    existing_index_titles: list[str] = []
    for page in client.get_pages(ability_config["index_pages"]):
        if page.missing:
            missing_index_titles.append(page.title)
            continue
        existing_index_titles.append(page.title)
        fields, templates_seen = extract_index_fields(page.content)
        samples.append(
            make_page_sample(
                entity_type="ability",
                page_type="ability_index",
                page=page,
                fields=fields,
                templates_seen=templates_seen,
            )
        )

    category_candidates = {}
    for category in ability_config["category_candidates"]:
        info = client.get_category_info(category)
        category_candidates[category] = {
            "missing": "missing" in info,
            "categoryinfo": info.get("categoryinfo"),
        }

    prefix_results = {}
    for prefix in ability_config["search_prefixes"]:
        prefix_results[prefix] = client.get_allpages_by_prefix(prefix, limit=20)

    ability_pages: list[PageRevision] = []
    for page in detail_pages_by_entity.get(ability_config["embedded_source_entity"], []):
        fields, _templates_seen = extract_named_template_fields(page.content, ENTITY_CONFIGS["species"]["detail_template"])
        ability_fields = [field for field in fields if field["raw_label"] in ability_config["embedded_fields"] and field.get("example_value")]
        if not ability_fields:
            continue
        ability_pages.append(page)
        samples.append(
            make_page_sample(
                entity_type="ability",
                page_type="ability_embedded_species_detail",
                page=page,
                fields=ability_fields,
                templates_seen=[ENTITY_CONFIGS["species"]["detail_template"]],
            )
        )

    discovery_notes["ability"] = {
        "standalone_index_pages_found": existing_index_titles,
        "missing_index_page_candidates": missing_index_titles,
        "category_candidates": category_candidates,
        "allpages_prefix_results": prefix_results,
        "embedded_source": "species.精灵信息",
        "embedded_sample_titles": [page.title for page in ability_pages],
    }

    aggregate = aggregate_samples(samples)
    run_metadata["discovery_notes"] = discovery_notes

    raw_samples_path = output_dir / "raw_page_samples.json"
    aggregate_path = output_dir / "candidate_field_aggregate.json"
    memo_path = output_dir / "findings_memo.md"
    metadata_path = output_dir / "run_metadata.json"

    write_json(raw_samples_path, {"metadata": run_metadata, "samples": samples})
    write_json(aggregate_path, aggregate)
    write_json(metadata_path, run_metadata)
    memo_path.write_text(build_memo(run_metadata, samples, aggregate), encoding="utf-8")

    return {
        "raw_samples": raw_samples_path,
        "aggregate": aggregate_path,
        "memo": memo_path,
        "metadata": metadata_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run bounded P1a field discovery against the rocom Biligame wiki.")
    parser.add_argument("--api-base-url", default=API_BASE_URL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--detail-limit", type=int, default=8)
    parser.add_argument("--sleep-seconds", type=float, default=0.2)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.detail_limit < 5:
        raise SystemExit("--detail-limit must be at least 5 to satisfy wiki_field_discovery_spec sampling rules.")
    paths = run_recon(args)
    print("Wrote field discovery artifacts:")
    for name, path in paths.items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
