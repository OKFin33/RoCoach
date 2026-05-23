from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from advisor.contracts import DocContextSnippet
from advisor.retrieval import DocContextRetriever, MechanismMatch
from knowledge.contracts import ConfidenceTier


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_D_PACK_DIR = ROOT / "artifacts" / "p10h_intuition_demo_pack"


@dataclass(frozen=True)
class ExperimentLayerConfig:
    include_b_layer_candidates: bool = False
    include_d1_attention: bool = False
    include_d2_general_priors: bool = False
    include_d3_demonstrations: bool = False
    d_pack_dir: Path = DEFAULT_D_PACK_DIR


class P10hExperimentDocContextRetriever(DocContextRetriever):
    """Experiment-only retriever that keeps the app AdvisorAgent path intact.

    Production runtime currently consumes reviewed B-layer wiki snippets through
    `DocContextRetriever`. P10h experiments need controlled ablations over
    draft B candidates plus D1/D2/D3 artifacts without pretending those drafts
    are already release/runtime assets. This class preserves the same
    `retrieve_doc_context` tool interface used by the app Agent while adding
    condition-specific snippets.
    """

    def __init__(self, config: ExperimentLayerConfig) -> None:
        super().__init__()
        self.config = config
        self._extra_snippets = self._load_extra_snippets()

    def inspect_mechanisms(
        self,
        *,
        query: str,
        evidence_texts: tuple[str, ...] | list[str] = (),
    ) -> list[MechanismMatch]:
        return super().inspect_mechanisms(query=query, evidence_texts=evidence_texts)

    def retrieve(
        self,
        *,
        query: str,
        analysis_type: str,
        limit: int = 4,
        evidence_texts: tuple[str, ...] | list[str] = (),
    ) -> list[DocContextSnippet]:
        if limit <= 0:
            return []

        extra = self._rank_extra(query=query, analysis_type=analysis_type, evidence_texts=evidence_texts)
        # Keep the production B-layer path in every condition. Add at most two
        # or three experimental snippets so the tool output remains close to
        # app size while still allowing Bplus/D1/D2/D3 ablations to surface.
        extra_budget = min(3, limit)
        selected_extra = _select_layer_diverse(extra, extra_budget)
        remaining = max(0, limit - len(selected_extra))
        base = super().retrieve(
            query=query,
            analysis_type=analysis_type,
            limit=remaining,
            evidence_texts=evidence_texts,
        )

        seen_topics: set[str] = set()
        results: list[DocContextSnippet] = []
        for snippet in [*selected_extra, *base]:
            if snippet.topic in seen_topics:
                continue
            results.append(snippet)
            seen_topics.add(snippet.topic)
            if len(results) >= limit:
                break
        return results

    def _load_extra_snippets(self) -> list[DocContextSnippet]:
        snippets: list[DocContextSnippet] = []
        if self.config.include_b_layer_candidates:
            snippets.extend(
                self._snippets_from_items(
                    self.config.d_pack_dir / "b_layer_archetype_prior_candidates.yaml",
                    layer_label="Bplus_archetype_candidate",
                    source_prefix="artifacts/p10h_intuition_demo_pack/b_layer_archetype_prior_candidates.yaml",
                    confidence=ConfidenceTier.PROVISIONAL,
                )
            )
        if self.config.include_d1_attention:
            snippets.extend(
                self._snippets_from_items(
                    self.config.d_pack_dir / "tactical_intuition_primitives.yaml",
                    layer_label="D1_attention",
                    source_prefix="artifacts/p10h_intuition_demo_pack/tactical_intuition_primitives.yaml",
                    confidence=ConfidenceTier.PROVISIONAL,
                )
            )
        if self.config.include_d2_general_priors:
            snippets.extend(
                self._snippets_from_items(
                    self.config.d_pack_dir / "expert_tactical_priors.yaml",
                    layer_label="D2_general_prior",
                    source_prefix="artifacts/p10h_intuition_demo_pack/expert_tactical_priors.yaml",
                    confidence=ConfidenceTier.PROVISIONAL,
                )
            )
        if self.config.include_d3_demonstrations:
            snippets.extend(
                self._snippets_from_items(
                    self.config.d_pack_dir / "long_demonstrations.yaml",
                    layer_label="D3_long_demo",
                    source_prefix="artifacts/p10h_intuition_demo_pack/long_demonstrations.yaml",
                    confidence=ConfidenceTier.PROVISIONAL,
                )
            )
        return snippets

    def _snippets_from_items(
        self,
        path: Path,
        *,
        layer_label: str,
        source_prefix: str,
        confidence: ConfidenceTier,
    ) -> list[DocContextSnippet]:
        if not path.exists():
            return []
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        raw_items = data.get("items") or data.get("demos") or []
        if not isinstance(raw_items, list):
            return []

        snippets: list[DocContextSnippet] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or "unknown")
            content = _compact_item_content(item, layer_label=layer_label)
            if not content:
                continue
            snippets.append(
                DocContextSnippet(
                    source_path=f"{source_prefix}#{item_id}",
                    topic=f"{layer_label}:{item_id}",
                    confidence=confidence,
                    content=content,
                    retrieval_reason=f"p10h_experiment:{layer_label}",
                    version="2026-05-02",
                )
            )
        return snippets

    def _rank_extra(
        self,
        *,
        query: str,
        analysis_type: str,
        evidence_texts: tuple[str, ...] | list[str],
    ) -> list[DocContextSnippet]:
        haystack = "\n".join([query, *evidence_texts]).casefold()
        if not haystack.strip() or analysis_type not in {"team", "species"}:
            return []
        non_battle_terms = (
            "api key",
            "api 密钥",
            "apikey",
            "provider key",
            "模型服务",
            "接入点",
            "base url",
            "runtime",
        )
        if any(term in haystack for term in non_battle_terms):
            return []

        scored: list[tuple[int, str, DocContextSnippet]] = []
        for snippet in self._extra_snippets:
            score = _snippet_score(snippet, haystack)
            if score <= 0:
                continue
            scored.append((score, snippet.topic, snippet))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [snippet for _score, _topic, snippet in scored]


def _compact_item_content(item: dict[str, Any], *, layer_label: str) -> str:
    item_id = str(item.get("id") or "")
    title = str(item.get("title") or item.get("name") or "")
    lines = [f"{layer_label} {item_id}".strip()]
    if title:
        lines.append(f"title: {title}")

    for key in (
        "claim",
        "situation",
        "expert_frame",
        "attention_order",
        "reasoning_chain",
        "decision_boundary",
        "what_to_imitate",
        "runtime_use",
        "do_not_overclaim",
        "not_to_infer",
    ):
        value = item.get(key)
        text = _stringify_compact(value)
        if text:
            lines.append(f"{key}: {text}")

    retrieval_tags = item.get("retrieval_tags")
    tag_text = _stringify_compact(retrieval_tags)
    if tag_text:
        lines.append(f"retrieval_tags: {tag_text}")

    blockers = item.get("blockers")
    blocker_text = _stringify_compact(blockers)
    if blocker_text:
        lines.append(f"blockers: {blocker_text}")

    return " ".join(lines)[:1800]


def _stringify_compact(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "；".join(_stringify_compact(item) for item in value if _stringify_compact(item))
    if isinstance(value, dict):
        parts: list[str] = []
        for key, nested in value.items():
            text = _stringify_compact(nested)
            if text:
                parts.append(f"{key}={text}")
        return "；".join(parts)
    return str(value).strip()


def _snippet_score(snippet: DocContextSnippet, haystack: str) -> int:
    text = f"{snippet.topic}\n{snippet.content}".casefold()
    score = 0
    # Extract a small controlled vocabulary from the snippet text. Substring
    # matching is intentional here: the probe scale is tiny and Chinese tags are
    # often full terms rather than whitespace-separated tokens.
    important_terms = (
        "星陨",
        "毒",
        "龙息帕尔",
        "落陨星兔",
        "圣羽翼王",
        "翼王",
        "贝古斯",
        "尖嘴狐仙",
        "闪电鳗鱼",
        "雷暴",
        "印记",
        "倾泻",
        "水刃",
        "斩杀",
        "性格",
        "配置",
        "首发",
        "博弈",
        "赌",
        "轮转",
        "高温回火",
        "联防",
        "中转",
        "强化",
        "资源",
        "能量",
        "魔力",
        "压缩",
        "难打",
        "matchup",
        "default",
        "exception",
    )
    for term in important_terms:
        normalized = term.casefold()
        if normalized in haystack and normalized in text:
            score += 4
    # Give general D1/D2 items a small chance on broad team-analysis prompts.
    broad_terms = ("队伍", "分析", "怎么打", "怎么优化", "应该先看", "判断")
    if any(term in haystack for term in broad_terms):
        if snippet.topic.startswith(("D1_attention", "D2_general_prior")):
            score += 1
    return score


def _select_layer_diverse(snippets: list[DocContextSnippet], limit: int) -> list[DocContextSnippet]:
    if limit <= 0:
        return []
    selected: list[DocContextSnippet] = []
    seen_layers: set[str] = set()

    for snippet in snippets:
        layer = snippet.topic.split(":", 1)[0]
        if layer in seen_layers:
            continue
        selected.append(snippet)
        seen_layers.add(layer)
        if len(selected) >= limit:
            return selected

    for snippet in snippets:
        if snippet in selected:
            continue
        selected.append(snippet)
        if len(selected) >= limit:
            break
    return selected
