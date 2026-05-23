#!/usr/bin/env python3
"""Conservative A/B-layer assisted transcript refinement.

This tool is for raw Bilibili/ASR transcripts. It uses local Roco A-layer
Battle Dex terms and B-layer mechanism terms to:

- apply small PM-confirmed ASR corrections;
- annotate exact A/B term hits;
- emit review questions for unresolved or fuzzy domain terms.

It does not create Meta Graph cards or D-layer gold cases.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import yaml

from advisor.battle_dex import DEFAULT_RUNTIME_DB, ensure_battle_dex_sqlite
from tools.transcript_quality import transcript_quality_flags, transcript_quality_label


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORRECTIONS_PATH = REPO_ROOT / "data" / "transcript_refinement" / "known_asr_corrections.yaml"
DEFAULT_OUT_ROOT = REPO_ROOT / "artifacts" / "transcript_ab_refinement"
MECHANICS_ROOT = REPO_ROOT / "wiki" / "pages" / "mechanics"

CHINESE_RE = re.compile(r"[\u4e00-\u9fff]+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])")
SRT_INDEX_RE = re.compile(r"^\d+$")
SRT_TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}[,.]\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}[,.]\d{3}")
INLINE_CODE_RE = re.compile(r"`([^`\n]{2,32})`")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
GENERIC_DOMAIN_WORDS = {
    "体系", "印记", "技能", "特性", "天气", "精灵", "能量", "收割", "联防",
    "首发", "队伍", "配置", "机制", "节奏", "资源", "速度", "回合",
}


@dataclass(frozen=True)
class TermRecord:
    term: str
    layer: str
    kind: str
    detail: str = ""


@dataclass(frozen=True)
class CorrectionRule:
    raw: str
    canonical: str
    status: str
    require_ab_term: bool = True
    note: str = ""


@dataclass(frozen=True)
class RepairCandidate:
    raw: str
    term: str
    score: float
    layer: str
    kind: str
    evidence: str
    action: str


@dataclass(frozen=True)
class SourceAliasRule:
    raw: str
    canonical: str
    confidence: float
    evidence: str
    require_profile_term: bool = True
    context_any: tuple[str, ...] = ()


SOURCE_PROFILE_ALIAS_RULES = (
    SourceAliasRule(
        raw="水人一王",
        canonical="水刃翼王",
        confidence=0.98,
        evidence="source_profile_asr_phrase+pm_confirmed_neighbor",
        require_profile_term=False,
    ),
    SourceAliasRule(
        raw="水刃一王",
        canonical="水刃翼王",
        confidence=0.98,
        evidence="source_profile_asr_phrase+pm_confirmed_neighbor",
        require_profile_term=False,
    ),
    SourceAliasRule(
        raw="一王",
        canonical="翼王",
        confidence=0.91,
        evidence="source_profile_short_alias",
        require_profile_term=True,
        context_any=("水人一王", "水刃", "电愿力", "后排有", "翼王"),
    ),
    SourceAliasRule(
        raw="韩英雄",
        canonical="寒音蛇",
        confidence=0.94,
        evidence="source_profile_asr_phrase+move_context",
        context_any=("示弱", "对面", "首发", "开"),
    ),
    SourceAliasRule(
        raw="韩一蛇",
        canonical="寒音蛇",
        confidence=0.96,
        evidence="source_profile_asr_phrase",
    ),
    SourceAliasRule(
        raw="韩医蛇",
        canonical="寒音蛇",
        confidence=0.96,
        evidence="source_profile_asr_phrase",
    ),
    SourceAliasRule(
        raw="韩一生",
        canonical="寒音蛇",
        confidence=0.94,
        evidence="source_profile_asr_phrase",
    ),
    SourceAliasRule(
        raw="韩一球",
        canonical="寒音蛇",
        confidence=0.9,
        evidence="source_profile_asr_phrase",
        context_any=("示弱", "对面", "首发", "应对", "拿下"),
    ),
    SourceAliasRule(
        raw="水母",
        canonical="琉璃水母",
        confidence=0.9,
        evidence="source_profile_short_alias+poison_team_context",
    ),
    SourceAliasRule(
        raw="古龙",
        canonical="寂灭骨龙",
        confidence=0.9,
        evidence="source_profile_short_alias+poison_team_context",
        context_any=("偷袭", "电弧", "不朽", "毒", "后排", "古龙"),
    ),
    SourceAliasRule(
        raw="五龙",
        canonical="寂灭骨龙",
        confidence=0.88,
        evidence="source_profile_asr_phrase+poison_team_context",
        context_any=("偷袭", "电弧", "不朽", "毒", "后排", "五龙"),
    ),
    SourceAliasRule(
        raw="修罗",
        canonical="厉毒修萝",
        confidence=0.9,
        evidence="source_profile_short_alias+poison_team_context",
    ),
    SourceAliasRule(
        raw="贝伍斯",
        canonical="贝古斯",
        confidence=0.93,
        evidence="source_profile_asr_phrase+same_source_exact_hit",
    ),
    SourceAliasRule(
        raw="被古斯",
        canonical="贝古斯",
        confidence=0.88,
        evidence="source_profile_asr_phrase+same_source_exact_hit",
        context_any=("上场", "防御", "斩杀线", "三维", "贝古斯", "后排", "对面"),
    ),
)


def _slugify(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9一-鿿_-]+", "_", value).strip("_")
    return stem or "transcript"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_subtitle_markup(text: str) -> str:
    """Remove SRT/VTT cue indexes and timestamps while preserving transcript lines."""
    cleaned: list[str] = []
    for raw_line in text.replace("\ufeff", "").splitlines():
        line = raw_line.strip()
        if not line or line == "WEBVTT":
            continue
        if SRT_INDEX_RE.match(line) or SRT_TIME_RE.match(line):
            continue
        line = re.sub(r"<[^>]+>", "", line).strip()
        if line:
            cleaned.append(line)
    return "\n".join(cleaned)


def split_paragraphs(text: str) -> list[str]:
    text = strip_subtitle_markup(text)
    text = _normalize_text(text)
    blocks = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(blocks) > 1:
        return blocks

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) >= 6:
        paragraphs: list[str] = []
        buf: list[str] = []
        size = 0
        for line in lines:
            buf.append(line)
            size += len(line)
            if len(buf) >= 8 or size >= 280:
                paragraphs.append("\n".join(buf))
                buf = []
                size = 0
        if buf:
            paragraphs.append("\n".join(buf))
        return paragraphs

    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]
    paragraphs: list[str] = []
    buf: list[str] = []
    size = 0
    for sentence in sentences:
        buf.append(sentence)
        size += len(sentence)
        if size >= 260 or len(buf) >= 3:
            paragraphs.append("".join(buf))
            buf = []
            size = 0
    if buf:
        paragraphs.append("".join(buf))
    return paragraphs or ([text] if text else [])


def _fetch_column(conn: sqlite3.Connection, sql: str) -> list[str]:
    return [str(row[0]).strip() for row in conn.execute(sql).fetchall() if row[0]]


def load_a_layer_terms(db_path: Path) -> dict[str, TermRecord]:
    db_path = ensure_battle_dex_sqlite(db_path)
    terms: dict[str, TermRecord] = {}
    with sqlite3.connect(db_path) as conn:
        for term in _fetch_column(conn, "SELECT DISTINCT display_name FROM species_form"):
            terms.setdefault(term, TermRecord(term, "A", "species"))
        for term in _fetch_column(conn, "SELECT DISTINCT initial_species_name FROM species_form WHERE initial_species_name IS NOT NULL"):
            terms.setdefault(term, TermRecord(term, "A", "species_initial"))
        for term in _fetch_column(conn, "SELECT DISTINCT move_name FROM move"):
            terms.setdefault(term, TermRecord(term, "A", "move"))
        for term in _fetch_column(conn, "SELECT DISTINCT ability_name FROM derived_ability"):
            terms.setdefault(term, TermRecord(term, "A", "ability"))
        for term in _fetch_column(conn, "SELECT DISTINCT ability_name FROM species_form WHERE ability_name IS NOT NULL"):
            terms.setdefault(term, TermRecord(term, "A", "ability"))
    return {term: rec for term, rec in terms.items() if len(term) >= 2}


def load_b_layer_terms(root: Path = MECHANICS_ROOT) -> dict[str, TermRecord]:
    terms: dict[str, TermRecord] = {}
    if not root.exists():
        return terms

    for path in sorted(root.glob("*.md")):
        text = _read_text(path)
        source = str(path.relative_to(REPO_ROOT))
        for match in INLINE_CODE_RE.finditer(text):
            term = match.group(1).strip()
            if _looks_like_domain_term(term):
                terms.setdefault(term, TermRecord(term, "B", "mechanism", source))
        for match in HEADING_RE.finditer(text):
            heading = re.sub(r"[*_`#]", "", match.group(1)).strip()
            for chunk in CHINESE_RE.findall(heading):
                if 2 <= len(chunk) <= 12:
                    terms.setdefault(chunk, TermRecord(chunk, "B", "mechanism_heading", source))
    return terms


def _looks_like_domain_term(term: str) -> bool:
    if len(term) < 2 or len(term) > 24:
        return False
    if "/" in term and not CHINESE_RE.search(term):
        return False
    return bool(CHINESE_RE.search(term))


def load_corrections(path: Path | None) -> list[CorrectionRule]:
    if not path or not path.exists():
        return []
    payload = yaml.safe_load(_read_text(path)) or {}
    rules: list[CorrectionRule] = []
    for entry in payload.get("corrections", []):
        raw = str(entry.get("raw", "")).strip()
        canonical = str(entry.get("canonical", "")).strip()
        if not raw or not canonical or raw == canonical:
            continue
        rules.append(
            CorrectionRule(
                raw=raw,
                canonical=canonical,
                status=str(entry.get("status", "unreviewed")).strip(),
                require_ab_term=bool(entry.get("require_ab_term", True)),
                note=str(entry.get("note", "")).strip(),
            )
        )
    return sorted(rules, key=lambda rule: len(rule.raw), reverse=True)


def apply_corrections(
    text: str,
    rules: list[CorrectionRule],
    lexicon: dict[str, TermRecord],
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    corrected = text
    applied: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for rule in rules:
        count = corrected.count(rule.raw)
        if count == 0:
            continue
        target_known = rule.canonical in lexicon
        allowed = rule.status == "pm_confirmed" and (target_known or not rule.require_ab_term)
        event = {
            "raw": rule.raw,
            "canonical": rule.canonical,
            "count": count,
            "status": rule.status,
            "target_known_in_ab": target_known,
            "note": rule.note,
        }
        if allowed:
            corrected = corrected.replace(rule.raw, rule.canonical)
            applied.append(event)
        else:
            event["reason"] = "target_not_in_ab_lexicon_or_not_pm_confirmed"
            blocked.append(event)
    return corrected, applied, blocked


def exact_term_hits(text: str, lexicon: dict[str, TermRecord], *, max_hits: int = 40) -> list[dict[str, str]]:
    matches: list[tuple[int, int, TermRecord]] = []
    for term, record in lexicon.items():
        if len(term) < 2:
            continue
        start = text.find(term)
        while start != -1:
            matches.append((start, start + len(term), record))
            start = text.find(term, start + 1)
    matches.sort(key=lambda item: (-(item[1] - item[0]), item[0], item[2].layer, item[2].kind, item[2].term))

    accepted_spans: list[tuple[int, int]] = []
    accepted: dict[str, TermRecord] = {}
    for start, end, record in matches:
        if any(start < accepted_end and accepted_start < end for accepted_start, accepted_end in accepted_spans):
            continue
        accepted_spans.append((start, end))
        accepted.setdefault(record.term, record)

    hits = sorted(accepted.values(), key=lambda rec: (-len(rec.term), rec.layer, rec.kind, rec.term))
    compact: list[dict[str, str]] = []
    for rec in hits:
        compact.append({"term": rec.term, "layer": rec.layer, "kind": rec.kind})
        if len(compact) >= max_hits:
            break
    return compact


def build_source_profile(text: str, lexicon: dict[str, TermRecord]) -> dict[str, Any]:
    """Build source-local evidence for repeated ASR aliases.

    The profile is deliberately small. It is not a global synonym dictionary;
    it only enables phrase repairs that are supported by this source's local
    context and the local A/B lexicon.
    """
    cleaned = strip_subtitle_markup(text)
    exact_terms = {hit["term"] for hit in exact_term_hits(cleaned, lexicon, max_hits=240)}
    profile_terms: set[str] = set(exact_terms)
    triggers: dict[str, list[str]] = defaultdict(list)

    def add(term: str, trigger: str) -> None:
        if _canonical_supported(term, lexicon):
            profile_terms.add(term)
            triggers[term].append(trigger)

    if any(raw in cleaned for raw in ("水人一王", "水刃一王", "水人遗王", "水人翼王")):
        add("水刃翼王", "wingking_waterblade_asr_phrase")
        add("翼王", "wingking_short_alias")
    if "水刃翼王" in cleaned or "圣羽翼王" in exact_terms:
        add("翼王", "wingking_exact_or_composite_hit")

    if any(raw in cleaned for raw in ("韩一蛇", "韩医蛇", "韩一生", "韩英雄", "韩一球")):
        if any(marker in cleaned for marker in ("示弱", "首发", "对面", "应对", "拿下", "蛇")):
            add("寒音蛇", "hanyinshe_asr_cluster")

    poison_markers = ("毒", "叠毒", "厉毒", "修萝", "水刃翼王", "水人一王", "电愿力", "球卡", "裘卡")
    if "水母" in cleaned and ("琉璃水母" in exact_terms or any(marker in cleaned for marker in poison_markers)):
        add("琉璃水母", "jellyfish_short_alias_in_poison_context")
    if any(raw in cleaned for raw in ("古龙", "五龙")) and (
        "寂灭骨龙" in exact_terms or any(marker in cleaned for marker in ("偷袭", "电弧", "不朽", "毒", "后排"))
    ):
        add("寂灭骨龙", "gulong_short_alias_in_poison_context")
    if "修罗" in cleaned and ("厉毒修萝" in exact_terms or any(marker in cleaned for marker in poison_markers)):
        add("厉毒修萝", "xiuluo_short_alias_in_poison_context")
    if any(raw in cleaned for raw in ("贝伍斯", "被古斯", "古斯")) and (
        "贝古斯" in exact_terms or "贝古斯" in cleaned
    ):
        add("贝古斯", "beigusi_asr_cluster")

    return {
        "exact_terms": sorted(exact_terms),
        "profile_terms": sorted(profile_terms),
        "triggers": {term: sorted(set(values)) for term, values in triggers.items()},
    }


def apply_source_profile_repairs(
    text: str,
    lexicon: dict[str, TermRecord],
    source_profile: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    repaired = text
    applied: list[dict[str, Any]] = []
    profile_terms = set(source_profile.get("profile_terms") or [])

    for rule in sorted(SOURCE_PROFILE_ALIAS_RULES, key=lambda item: len(item.raw), reverse=True):
        if rule.raw not in repaired:
            continue
        if not _canonical_supported(rule.canonical, lexicon):
            continue
        if rule.require_profile_term and rule.canonical not in profile_terms:
            continue
        repaired, count = _replace_alias_occurrences(repaired, rule, profile_terms)
        if count == 0:
            continue
        applied.append(
            {
                "raw": rule.raw,
                "canonical": rule.canonical,
                "count": count,
                "status": "source_profile_auto",
                "score": rule.confidence,
                "evidence": rule.evidence,
                "layer": "A",
                "kind": "source_profile_alias",
            }
        )
    return repaired, applied


def _canonical_supported(canonical: str, lexicon: dict[str, TermRecord]) -> bool:
    if canonical in lexicon:
        return True
    if canonical == "翼王":
        return any(term.endswith("翼王") for term in lexicon)
    if canonical == "水刃翼王":
        return "水刃" in lexicon and any(term.endswith("翼王") for term in lexicon)
    return False


def _replace_alias_occurrences(
    text: str,
    rule: SourceAliasRule,
    profile_terms: set[str],
) -> tuple[str, int]:
    chunks: list[str] = []
    last = 0
    count = 0
    start = 0
    while True:
        idx = text.find(rule.raw, start)
        if idx < 0:
            break
        end = idx + len(rule.raw)
        if _is_inside_existing_canonical(text, idx, end, rule.canonical):
            start = end
            continue
        if not _alias_context_allows(text, idx, end, rule, profile_terms):
            start = end
            continue
        chunks.append(text[last:idx])
        chunks.append(rule.canonical)
        last = end
        start = end
        count += 1
    if count == 0:
        return text, 0
    chunks.append(text[last:])
    return "".join(chunks), count


def _is_inside_existing_canonical(text: str, start: int, end: int, canonical: str) -> bool:
    raw_len = end - start
    for offset in range(0, max(len(canonical) - raw_len + 1, 1)):
        candidate_start = start - offset
        candidate_end = candidate_start + len(canonical)
        if candidate_start < 0 or candidate_end > len(text):
            continue
        if text[candidate_start:candidate_end] == canonical:
            return True
    return False


def _alias_context_allows(
    text: str,
    start: int,
    end: int,
    rule: SourceAliasRule,
    profile_terms: set[str],
) -> bool:
    if not rule.context_any:
        return True
    window = text[max(0, start - 24): min(len(text), end + 24)]
    return any(marker in window or marker in profile_terms for marker in rule.context_any)


def _candidate_substrings(text: str) -> set[str]:
    candidates: set[str] = set()
    for chunk in CHINESE_RE.findall(text):
        if len(chunk) < 2:
            continue
        if len(chunk) <= 8:
            candidates.add(chunk)
        upper = min(8, len(chunk))
        for size in range(2, upper + 1):
            for idx in range(0, len(chunk) - size + 1):
                sub = chunk[idx : idx + size]
                if _is_reviewable_substring(sub):
                    candidates.add(sub)
    return candidates


def _is_reviewable_substring(value: str) -> bool:
    if len(value) < 2:
        return False
    stopwords = {
        "这个", "那个", "我们", "他们", "就是", "然后", "可以", "因为", "所以", "如果",
        "对面", "自己", "一个", "直接", "时候", "这里", "没有", "不是", "还是", "进行",
    }
    return value not in stopwords


def fuzzy_review_candidates(
    text: str,
    lexicon: dict[str, TermRecord],
    *,
    threshold: float = 0.78,
    max_items: int = 25,
) -> list[dict[str, Any]]:
    lexicon_terms = [term for term in lexicon if 2 <= len(term) <= 8]
    candidates: list[dict[str, Any]] = []
    for raw in _candidate_substrings(text):
        if raw in lexicon:
            continue
        if raw in GENERIC_DOMAIN_WORDS:
            continue
        best: list[tuple[float, str]] = []
        for term in lexicon_terms:
            if term in raw and len(raw) > len(term):
                continue
            if term in text and raw in term and len(raw) < len(term):
                continue
            if term in GENERIC_DOMAIN_WORDS:
                continue
            if abs(len(term) - len(raw)) > 2:
                continue
            overlap = len(set(raw) & set(term))
            if overlap == 0:
                continue
            score = SequenceMatcher(None, raw, term).ratio()
            if score >= threshold:
                best.append((score, term))
        if not best:
            continue
        best.sort(key=lambda item: (-item[0], item[1]))
        candidates.append(
            {
                "span": raw,
                "candidates": [
                    {
                        "term": term,
                        "score": round(score, 3),
                        "layer": lexicon[term].layer,
                        "kind": lexicon[term].kind,
                    }
                    for score, term in best[:3]
                ],
            }
        )
    candidates.sort(key=lambda item: (-item["candidates"][0]["score"], item["span"]))
    return candidates[:max_items]


def guided_repair_candidates(
    text: str,
    lexicon: dict[str, TermRecord],
    *,
    auto_threshold: float = 0.95,
    candidate_threshold: float = 0.72,
    max_items: int = 30,
) -> list[dict[str, Any]]:
    """Suggest A/B-constrained ASR repairs without inventing terms.

    This is stricter than fuzzy review: candidates are scored with local context
    and are allowed to be auto-applied only at very high confidence.
    """
    context_hits = exact_term_hits(text, lexicon, max_hits=80)
    exact_terms = {hit["term"] for hit in context_hits}
    repair_items: list[dict[str, Any]] = []
    lexicon_terms = [
        (term, record)
        for term, record in lexicon.items()
        if 2 <= len(term) <= 10 and term not in GENERIC_DOMAIN_WORDS
    ]

    spans = _guided_repair_spans(text, lexicon)
    for raw in sorted(spans, key=lambda item: (len(item), item)):
        if not _should_consider_repair_span(raw, text, lexicon):
            continue
        scored: list[RepairCandidate] = []
        for term, record in lexicon_terms:
            if abs(len(term) - len(raw)) > 4:
                continue
            score, evidence = _repair_score(raw, term, record, text, exact_terms)
            if score < candidate_threshold:
                continue
            action = "auto_replace" if score >= auto_threshold and term in lexicon else "suggest"
            scored.append(
                RepairCandidate(
                    raw=raw,
                    term=term,
                    score=round(min(score, 1.0), 3),
                    layer=record.layer,
                    kind=record.kind,
                    evidence=evidence,
                    action=action,
                )
            )
        if not scored:
            local = _local_context_candidates(raw, text, context_hits)
            if local:
                repair_items.append({"span": raw, "candidates": local})
            continue
        scored.sort(key=lambda item: (-item.score, item.action != "auto_replace", item.term))
        best = scored[:3]
        repair_items.append(
            {
                "span": raw,
                "candidates": [
                    {
                        "term": item.term,
                        "score": item.score,
                        "layer": item.layer,
                        "kind": item.kind,
                        "evidence": item.evidence,
                        "action": item.action,
                    }
                    for item in best
                ],
            }
        )

    repair_items.sort(
        key=lambda item: (
            item["candidates"][0]["action"] != "auto_replace",
            -item["candidates"][0]["score"],
            item["span"],
        )
    )
    return repair_items[:max_items]


def _guided_repair_spans(text: str, lexicon: dict[str, TermRecord]) -> set[str]:
    spans: set[str] = set()
    for item in fuzzy_review_candidates(text, lexicon, threshold=0.72, max_items=40):
        spans.add(str(item["span"]))
    for flag in transcript_quality_flags(text):
        if ":" in flag:
            marker = flag.split(":", 1)[1].strip()
            if marker:
                spans.add(marker)
                for chunk in CHINESE_RE.findall(marker):
                    if 2 <= len(chunk) <= 8:
                        spans.add(chunk)
    for phrase in unresolved_domain_phrases(text, lexicon):
        if 2 <= len(phrase) <= 8:
            spans.add(phrase)
    return spans


def apply_guided_repairs(
    text: str,
    repair_items: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    repaired = text
    applied: list[dict[str, Any]] = []
    for item in repair_items:
        candidates = item.get("candidates") or []
        if not candidates:
            continue
        best = candidates[0]
        raw = item.get("span", "")
        term = best.get("term", "")
        if best.get("action") != "auto_replace" or not raw or not term or raw == term:
            continue
        count = repaired.count(raw)
        if count == 0:
            continue
        repaired = repaired.replace(raw, term)
        applied.append(
            {
                "raw": raw,
                "canonical": term,
                "count": count,
                "status": "ab_guided_auto",
                "score": best.get("score"),
                "evidence": best.get("evidence"),
                "layer": best.get("layer"),
                "kind": best.get("kind"),
            }
        )
    return repaired, applied


def _should_consider_repair_span(raw: str, text: str, lexicon: dict[str, TermRecord]) -> bool:
    if len(raw) < 2 or len(raw) > 8:
        return False
    if raw in lexicon or raw in GENERIC_DOMAIN_WORDS:
        return False
    if raw in {"精校", "原文", "自动校正", "文本质量"}:
        return False
    if not _is_reviewable_substring(raw):
        return False
    for term in lexicon:
        if len(term) >= 2 and term in raw and len(raw) > len(term):
            return False
    # Prefer spans that look domain-adjacent. This prevents generic Chinese
    # prose from flooding the repair queue.
    domain_words = ("队", "王", "龙", "蛇", "菇", "兽", "鱼", "犬", "印记", "翼", "毒", "水", "电", "火", "冰", "草", "技能")
    if any(word in raw for word in domain_words):
        return True
    left = max(0, text.find(raw) - 10)
    right = text.find(raw) + len(raw) + 10
    context = text[left:right]
    return any(word in context for word in ("首发", "后排", "技能", "特性", "携带", "使用", "应对", "克制", "强化", "上场"))


def _repair_score(
    raw: str,
    term: str,
    record: TermRecord,
    text: str,
    exact_terms: set[str],
) -> tuple[float, str]:
    if term in exact_terms and _looks_like_boundary_artifact(raw, term):
        return 0.0, "known_term_boundary_artifact"
    base = SequenceMatcher(None, raw, term).ratio()
    raw_chars = set(raw)
    term_chars = set(term)
    overlap = len(raw_chars & term_chars) / max(len(raw_chars | term_chars), 1)
    length_penalty = min(abs(len(raw) - len(term)) * 0.035, 0.14)
    score = base * 0.76 + overlap * 0.18 - length_penalty
    evidence_parts = ["char_similarity"]

    if term in exact_terms:
        score += 0.08
        evidence_parts.append("same_paragraph_exact_hit")
    if _kind_context_bonus(record.kind, raw, text):
        score += 0.05
        evidence_parts.append("kind_context")
    if len(raw) == len(term):
        score += 0.03
        evidence_parts.append("same_length")
    if raw[-1:] == term[-1:] or raw[:1] == term[:1]:
        score += 0.03
        evidence_parts.append("edge_char_match")
    return score, "+".join(evidence_parts)


def _looks_like_boundary_artifact(raw: str, term: str) -> bool:
    if raw == term:
        return True
    matcher = SequenceMatcher(None, raw, term)
    longest = max((block.size for block in matcher.get_matching_blocks()), default=0)
    return longest >= min(len(raw), len(term)) - 1


def _kind_context_bonus(kind: str, raw: str, text: str) -> bool:
    idx = text.find(raw)
    if idx < 0:
        return False
    context = text[max(0, idx - 8): idx + len(raw) + 8]
    if kind in {"species", "species_initial"}:
        return any(word in context for word in ("首发", "后排", "上场", "对面", "精灵", "队伍", "死了", "联防"))
    if kind == "move":
        return any(word in context for word in ("技能", "使用", "点", "开", "携带", "打", "冲击", "应对"))
    if kind == "ability":
        return "特性" in context or "血脉" in context
    return False


def _local_context_candidates(raw: str, text: str, context_hits: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Give cautious candidates from nearby exact hits for severe ASR misses."""
    if not any(marker in raw for marker in ("韩", "寒", "音", "球", "蛇")):
        return []
    species_hits = [hit for hit in context_hits if hit["kind"] in {"species", "species_initial"}]
    if not species_hits:
        return []
    candidates: list[dict[str, Any]] = []
    for hit in species_hits[:3]:
        candidates.append(
            {
                "term": hit["term"],
                "score": 0.62,
                "layer": hit["layer"],
                "kind": hit["kind"],
                "evidence": "same_paragraph_species_context",
                "action": "suggest",
            }
        )
    return candidates


def unresolved_domain_phrases(text: str, lexicon: dict[str, TermRecord]) -> list[str]:
    suffixes = ("队", "体系", "印记", "天气", "技能", "特性", "首发", "联防", "收割")
    found: set[str] = set()
    for chunk in CHINESE_RE.findall(text):
        for idx in range(len(chunk)):
            for size in range(2, min(7, len(chunk) - idx) + 1):
                sub = chunk[idx : idx + size]
                if sub in lexicon:
                    continue
                if sub in GENERIC_DOMAIN_WORDS:
                    continue
                if any(term in sub for term in lexicon if len(term) >= 3):
                    continue
                if sub.endswith(suffixes) and _is_reviewable_substring(sub):
                    found.add(sub)
    return sorted(found, key=lambda item: (len(item), item))[:30]


def refine_transcript(
    source_path: Path,
    *,
    out_dir: Path,
    source_id: str | None = None,
    corrections_path: Path | None = DEFAULT_CORRECTIONS_PATH,
    db_path: Path = DEFAULT_RUNTIME_DB,
    include_unresolved: bool = False,
    repair_candidates: bool = False,
    auto_repair_threshold: float = 0.95,
) -> dict[str, Any]:
    raw_text = _read_text(source_path)
    a_terms = load_a_layer_terms(db_path)
    b_terms = load_b_layer_terms()
    lexicon = {**b_terms, **a_terms}
    rules = load_corrections(corrections_path)
    slug = _slugify(source_id or source_path.stem)
    source_profile = build_source_profile(raw_text, lexicon) if repair_candidates else {}

    out_dir.mkdir(parents=True, exist_ok=True)
    paragraphs = split_paragraphs(raw_text)

    cleaned_lines = [
        f"# {slug} - A/B Assisted Transcript Refinement",
        "",
        "## Metadata",
        "",
        f"- source_path: `{source_path}`",
        f"- generated_at: `{date.today().isoformat()}`",
        "- cleaning_level: ab_assisted_conservative",
        "- runtime_allowed: false",
        "- case_extraction_allowed: input_only_after_PM_review",
        "",
        "## Policy",
        "",
        "- 自动替换优先使用 PM-confirmed correction overlay，并校验 canonical term 是否存在于 A/B 词库。",
        "- source-profile 自动修复只处理本视频局部上下文支持的 A 层别名/音近短语，仍需人工抽样复核。",
        "- A/B exact hits 只证明词项存在，不证明源视频中的战术判断正确。",
        "- fuzzy candidates 和 unresolved phrases 必须人工复核，不能进入 runtime/gold case。",
        "",
        "## Transcript",
        "",
    ]
    review_questions: list[dict[str, Any]] = []
    applied_totals: dict[str, int] = defaultdict(int)
    blocked_totals: list[dict[str, Any]] = []
    unresolved_counts: dict[str, int] = defaultdict(int)
    paragraph_quality_counts: dict[str, int] = defaultdict(int)

    for index, paragraph in enumerate(paragraphs, start=1):
        corrected, applied, blocked = apply_corrections(paragraph, rules, lexicon)
        profile_applied: list[dict[str, Any]] = []
        if repair_candidates and source_profile:
            corrected, profile_applied = apply_source_profile_repairs(corrected, lexicon, source_profile)
        guided: list[dict[str, Any]] = []
        guided_applied: list[dict[str, Any]] = []
        preliminary_quality_label = transcript_quality_label(transcript_quality_flags(corrected))
        if repair_candidates and preliminary_quality_label == "needs_repair":
            guided = guided_repair_candidates(
                corrected,
                lexicon,
                auto_threshold=auto_repair_threshold,
            )
            corrected, guided_applied = apply_guided_repairs(corrected, guided)
        hits = exact_term_hits(corrected, lexicon)
        fuzzy = fuzzy_review_candidates(corrected, lexicon)
        unresolved = unresolved_domain_phrases(corrected, lexicon)
        quality_flags = transcript_quality_flags(corrected)
        quality_label = transcript_quality_label(quality_flags)
        paragraph_quality_counts[quality_label] += 1
        for phrase in unresolved:
            if 2 <= len(phrase) <= 5:
                unresolved_counts[phrase] += 1
        pid = f"P{index:03d}"
        all_applied = [*applied, *profile_applied, *guided_applied]

        for event in all_applied:
            applied_totals[f"{event['raw']} -> {event['canonical']}"] += event["count"]
        blocked_totals.extend({"paragraph_id": pid, **event} for event in blocked)
        if fuzzy or guided or blocked or all_applied or quality_label == "needs_repair":
            review_questions.append(
                {
                    "paragraph_id": pid,
                    "paragraph_quality": quality_label,
                    "quality_flags": quality_flags,
                    "applied_repairs": all_applied,
                    "guided_repair_candidates": guided,
                    "fuzzy_candidates": fuzzy,
                    "blocked_corrections": blocked,
                }
            )

        cleaned_lines.append(f"### {pid}")
        cleaned_lines.append("")
        cleaned_lines.append(f"- 原文：{paragraph}")
        cleaned_lines.append(f"- 精校：{corrected}")
        if all_applied:
            notes = "; ".join(
                f"{e['raw']} -> {e['canonical']} x{e['count']}"
                + (f" [{e.get('status')} score={e.get('score')}]" if e.get("score") is not None else f" [{e.get('status')}]")
                for e in all_applied
            )
            cleaned_lines.append(f"- 自动校正：{notes}")
        else:
            cleaned_lines.append("- 自动校正：无")
        if hits:
            rendered = ", ".join(f"{h['term']}[{h['layer']}/{h['kind']}]" for h in hits[:20])
            cleaned_lines.append(f"- A/B 命中：{rendered}")
        else:
            cleaned_lines.append("- A/B 命中：无")
        if quality_flags:
            cleaned_lines.append(f"- 文本质量：{quality_label} ({', '.join(quality_flags)})")
        else:
            cleaned_lines.append(f"- 文本质量：{quality_label}")
        if fuzzy:
            rendered = "; ".join(
                f"{item['span']} -> "
                + "/".join(f"{c['term']}({c['score']})" for c in item["candidates"])
                for item in fuzzy[:8]
            )
            cleaned_lines.append(f"- 需复核候选：{rendered}")
        if guided:
            rendered = "; ".join(
                f"{item['span']} -> "
                + "/".join(
                    f"{c['term']}({c['score']},{c['action']})"
                    for c in item["candidates"][:3]
                )
                for item in guided[:8]
            )
            cleaned_lines.append(f"- A/B 修复候选：{rendered}")
        if include_unresolved and unresolved:
            cleaned_lines.append(f"- 未解析领域短语：{', '.join(unresolved[:12])}")
        cleaned_lines.append("")

    cleaned_path = out_dir / f"{slug}.ab_refined.md"
    manifest_path = out_dir / f"{slug}.manifest.yaml"
    questions_path = out_dir / f"{slug}.review_questions.yaml"

    manifest = {
        "source_path": str(source_path),
        "source_id": slug,
        "generated_at": date.today().isoformat(),
        "cleaned_path": str(cleaned_path),
        "review_questions_path": str(questions_path),
        "paragraph_count": len(paragraphs),
        "raw_char_count": len(raw_text),
        "a_layer_term_count": len(a_terms),
        "b_layer_term_count": len(b_terms),
        "correction_rule_count": len(rules),
        "repair_candidates_enabled": repair_candidates,
        "auto_repair_threshold": auto_repair_threshold,
        "source_profile": {
            "profile_terms": list(source_profile.get("profile_terms", []))[:80],
            "triggers": source_profile.get("triggers", {}),
        } if source_profile else {},
        "applied_correction_counts": dict(sorted(applied_totals.items())),
        "blocked_corrections": blocked_totals,
        "review_question_count": len(review_questions),
        "paragraph_quality_counts": dict(sorted(paragraph_quality_counts.items())),
        "source_local_term_candidates": [
            {"term": term, "paragraph_hits": count}
            for term, count in sorted(
                unresolved_counts.items(),
                key=lambda item: (-item[1], len(item[0]), item[0]),
            )[:50]
            if count >= 2 and term not in GENERIC_DOMAIN_WORDS
        ],
    }

    cleaned_path.write_text("\n".join(cleaned_lines), encoding="utf-8")
    questions_path.write_text(yaml.dump(review_questions, allow_unicode=True, sort_keys=False), encoding="utf-8")
    manifest_path.write_text(yaml.dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8")

    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Raw transcript path")
    parser.add_argument("--source-id", help="Stable source id / output slug")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--corrections", type=Path, default=DEFAULT_CORRECTIONS_PATH)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_RUNTIME_DB)
    parser.add_argument(
        "--include-unresolved",
        action="store_true",
        help="Include noisy source-local unresolved phrases in the cleaned markdown",
    )
    parser.add_argument(
        "--repair-candidates",
        action="store_true",
        help="Generate A/B-guided ASR repair candidates and apply very high-confidence repairs",
    )
    parser.add_argument(
        "--auto-repair-threshold",
        type=float,
        default=0.95,
        help="Minimum guided repair score for automatic replacement",
    )
    parser.add_argument("--json", action="store_true", help="Print manifest JSON")
    args = parser.parse_args()

    manifest = refine_transcript(
        args.source,
        out_dir=args.out_dir,
        source_id=args.source_id,
        corrections_path=args.corrections,
        db_path=args.db_path,
        include_unresolved=args.include_unresolved,
        repair_candidates=args.repair_candidates,
        auto_repair_threshold=args.auto_repair_threshold,
    )
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        print(f"cleaned: {manifest['cleaned_path']}")
        print(f"questions: {manifest['review_questions_path']}")
        print(f"review_questions: {manifest['review_question_count']}")


if __name__ == "__main__":
    main()
