from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from advisor.contracts import DocContextSnippet
from reporting.contracts import ConfidenceTier


@dataclass(frozen=True)
class _SnippetRule:
    snippet: DocContextSnippet
    analysis_types: tuple[str, ...]
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class MechanismMatch:
    token: str
    topic: str
    page_path: str | None
    has_reviewed_page: bool


@dataclass(frozen=True)
class _MechanismRule:
    token: str
    topic: str
    page_path: str | None


_RULES: tuple[_SnippetRule, ...] = (
    _SnippetRule(
        snippet=DocContextSnippet(
            source_path="docs/agent_framework_decision.md",
            topic="engine_grounding",
            confidence=ConfidenceTier.CONFIRMED,
            content=(
                "The advisor is Agent-led, but deterministic structure facts stay Engine-owned and "
                "must not be replaced by freeform model claims."
            ),
            retrieval_reason="baseline_guardrail",
        ),
        analysis_types=("team", "species"),
        keywords=("分析", "联防", "洞", "结构", "角色", "定位"),
    ),
    _SnippetRule(
        snippet=DocContextSnippet(
            source_path="specs/report_confidence_policy.md",
            topic="confidence_guard",
            confidence=ConfidenceTier.CONFIRMED,
            content=(
                "Confirmed claims require Engine or SQL backing. Provisional interpretation must stay labeled, "
                "and unsupported meta or role certainty should be refused."
            ),
            retrieval_reason="confidence_policy",
        ),
        analysis_types=("team", "species"),
        keywords=("证据", "confidence", "确定", "确认", "meta", "角色"),
    ),
    _SnippetRule(
        snippet=DocContextSnippet(
            source_path="docs/domain_primer.md",
            topic="dual_type_baseline",
            confidence=ConfidenceTier.PROVISIONAL,
            content=(
                "The current project baseline treats double strength as x3, double resistance as 1/3, "
                "and opposite modifiers as x1. This mechanic is still marked provisional."
            ),
            retrieval_reason="mechanic_baseline",
        ),
        analysis_types=("team",),
        keywords=("双属性", "补洞", "抗性", "弱点", "属性"),
    ),
    _SnippetRule(
        snippet=DocContextSnippet(
            source_path="docs/battle_analysis_architecture.md",
            topic="team_conditional_roles",
            confidence=ConfidenceTier.PROVISIONAL,
            content=(
                "Species role judgement should be team-conditional, set-conditional, and framed as a hypothesis "
                "until deterministic feature scoring and case evidence are available."
            ),
            retrieval_reason="role_guard",
        ),
        analysis_types=("species",),
        keywords=("主C", "副C", "辅助", "角色", "定位", "适合", "干什么"),
    ),
    _SnippetRule(
        snippet=DocContextSnippet(
            source_path="specs/conversation_cli_spec.md",
            topic="scope_boundary",
            confidence=ConfidenceTier.CONFIRMED,
            content=(
                "The first CLI delivery supports team entry, structure analysis, battle-dex-backed species lookup, "
                "and bounded follow-up questions inside one session."
            ),
            retrieval_reason="runtime_scope",
        ),
        analysis_types=("team", "species"),
        keywords=("支持", "能不能", "范围", "边界", "help"),
    ),
)

_MECHANISM_RULES: tuple[_MechanismRule, ...] = (
    _MechanismRule("迅捷", "mechanism_speed_priority_swift", "pages/mechanics/speed_priority_and_swift.md"),
    _MechanismRule("先手", "mechanism_speed_priority_swift", "pages/mechanics/speed_priority_and_swift.md"),
    _MechanismRule("速度", "mechanism_speed_priority_swift", "pages/mechanics/speed_priority_and_swift.md"),
    _MechanismRule("印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("棘刺印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("光合印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("蓄势印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("龙噬印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("中毒印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("降灵印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("攻击印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("湿润印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("减速印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("蓄电印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("风起印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("星陨印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("清印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("驱散印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("偷印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("覆盖印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("转换印记", "mechanism_marks", "pages/mechanics/marks_and_persistence.md"),
    _MechanismRule("天气", "mechanism_weather", "pages/mechanics/weather_and_field_effects.md"),
    _MechanismRule("雨天", "mechanism_weather", "pages/mechanics/weather_and_field_effects.md"),
    _MechanismRule("沙暴", "mechanism_weather", "pages/mechanics/weather_and_field_effects.md"),
    _MechanismRule("雪天", "mechanism_weather", "pages/mechanics/weather_and_field_effects.md"),
    _MechanismRule("暴风雪", "mechanism_weather", "pages/mechanics/weather_and_field_effects.md"),
    _MechanismRule("应对", "mechanism_response", "pages/mechanics/response_counterplay.md"),
    _MechanismRule("打断", "mechanism_response", "pages/mechanics/response_counterplay.md"),
    _MechanismRule("传动", "mechanism_transmission", "pages/mechanics/transmission_and_skill_slots.md"),
    _MechanismRule("迸发", "mechanism_burst_trigger", "pages/mechanics/burst_trigger_and_entry_actions.md"),
    _MechanismRule("蓄力", "mechanism_charge", "pages/mechanics/charge_and_release.md"),
    _MechanismRule("奉献", "mechanism_bug_contribution", "pages/mechanics/bug_contribution_fengxian.md"),
    _MechanismRule("萌化", "mechanism_degeneration", "pages/mechanics/degeneration_and_menghua.md"),
    _MechanismRule("灼烧", "mechanism_burn", "pages/mechanics/burn_timing_and_full_combustion.md"),
    _MechanismRule("冻结", "mechanism_status_effects", "pages/mechanics/status_effects_and_persistence.md"),
    _MechanismRule("中毒", "mechanism_status_effects", "pages/mechanics/status_effects_and_persistence.md"),
    _MechanismRule("寄生", "mechanism_status_effects", "pages/mechanics/status_effects_and_persistence.md"),
    _MechanismRule("聚能", "mechanism_focus_action", "pages/mechanics/energy_actions_and_focus.md"),
    _MechanismRule("魔力", "mechanism_morale_revive", "pages/mechanics/morale_and_revive.md"),
    _MechanismRule("换人", "mechanism_entry_exit_replacement", "pages/mechanics/entry_exit_and_replacement_timing.md"),
    _MechanismRule("离场", "mechanism_entry_exit_replacement", "pages/mechanics/entry_exit_and_replacement_timing.md"),
    _MechanismRule("脱离", "mechanism_entry_exit_replacement", "pages/mechanics/entry_exit_and_replacement_timing.md"),
    _MechanismRule("回场", "mechanism_entry_exit_replacement", "pages/mechanics/entry_exit_and_replacement_timing.md"),
    _MechanismRule("入场", "mechanism_entry_exit_replacement", "pages/mechanics/entry_exit_and_replacement_timing.md"),
    _MechanismRule("替换上场", "mechanism_entry_exit_replacement", "pages/mechanics/entry_exit_and_replacement_timing.md"),
    _MechanismRule("主动离场", "mechanism_entry_exit_replacement", "pages/mechanics/entry_exit_and_replacement_timing.md"),
)


class DocContextRetriever:
    def __init__(self) -> None:
        self._available_pages, self._page_sections = self._load_compiled_wiki_index()

    def inspect_mechanisms(
        self,
        *,
        query: str,
        evidence_texts: tuple[str, ...] | list[str] = (),
    ) -> list[MechanismMatch]:
        haystack = "\n".join([query, *evidence_texts])
        if not haystack.strip():
            return []

        matches: list[MechanismMatch] = []
        seen_topics: set[tuple[str, str | None]] = set()
        for rule in _MECHANISM_RULES:
            if rule.token not in haystack:
                continue
            key = (rule.topic, rule.page_path)
            if key in seen_topics:
                continue
            has_reviewed_page = bool(rule.page_path and rule.page_path in self._available_pages)
            matches.append(
                MechanismMatch(
                    token=rule.token,
                    topic=rule.topic,
                    page_path=rule.page_path,
                    has_reviewed_page=has_reviewed_page,
                )
            )
            seen_topics.add(key)
        return matches

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

        lowered = query.lower()
        scored: list[tuple[int, DocContextSnippet]] = []
        for rule in _RULES:
            if analysis_type not in rule.analysis_types:
                continue
            score = 1 if rule.snippet.topic in {"engine_grounding", "confidence_guard"} else 0
            score += sum(1 for keyword in rule.keywords if keyword.lower() in lowered)
            if score <= 0:
                continue
            scored.append((score, rule.snippet))

        mechanism_matches = self.inspect_mechanisms(query=query, evidence_texts=evidence_texts)
        mechanism_snippets = [
            snippet
            for match in mechanism_matches
            if match.has_reviewed_page
            for snippet in [self._mechanism_snippet(match)]
            if snippet is not None
        ]

        scored.sort(key=lambda item: (-item[0], item[1].topic))
        seen_topics: set[str] = set()
        results: list[DocContextSnippet] = []
        for snippet in mechanism_snippets:
            if snippet.topic in seen_topics:
                continue
            results.append(snippet)
            seen_topics.add(snippet.topic)
            if len(results) >= limit:
                return results
        for _score, snippet in scored:
            if snippet.topic in seen_topics:
                continue
            results.append(snippet)
            seen_topics.add(snippet.topic)
            if len(results) >= limit:
                break
        return results

    def _mechanism_snippet(self, match: MechanismMatch) -> DocContextSnippet | None:
        if not match.page_path:
            return None
        sections = self._page_sections.get(match.page_path)
        if not sections:
            return None

        preferred_sections = (
            "Claim",
            "Strategic Use",
            "Confidence",
            "A-Layer Boundary",
        )
        content_parts = [sections[section] for section in preferred_sections if section in sections]
        if not content_parts:
            content_parts = list(sections.values())[:2]
        content = " ".join(part.strip().replace("\n", " ") for part in content_parts if part.strip())
        if not content:
            return None

        return DocContextSnippet(
            source_path=f"wiki/{match.page_path}",
            topic=match.topic,
            confidence=ConfidenceTier.PROVISIONAL,
            content=content,
            retrieval_reason=f"mechanism_auto_lookup:{match.token}",
            version="2026-04-21",
        )

    def _load_compiled_wiki_index(self) -> tuple[set[str], dict[str, dict[str, str]]]:
        root = Path(__file__).resolve().parents[1]
        manifest_path = root / "wiki" / "compiled" / "manifest.yaml"
        chunks_path = root / "wiki" / "compiled" / "chunks.jsonl"
        available_pages: set[str] = set()
        page_sections: dict[str, dict[str, str]] = {}

        if manifest_path.exists():
            available_pages.update(self._parse_manifest_source_pages(manifest_path.read_text(encoding="utf-8")))

        if chunks_path.exists():
            for line in chunks_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                chunk = json.loads(line)
                page = chunk.get("page")
                section = chunk.get("section")
                text = chunk.get("text")
                if not isinstance(page, str) or not isinstance(section, str) or not isinstance(text, str):
                    continue
                page_sections.setdefault(page, {})[section] = text

        return available_pages, page_sections

    def _parse_manifest_source_pages(self, text: str) -> set[str]:
        try:
            manifest = json.loads(text)
        except json.JSONDecodeError:
            manifest = None
        if isinstance(manifest, dict):
            source_pages = manifest.get("source_pages", [])
            if isinstance(source_pages, list):
                return {page for page in source_pages if isinstance(page, str)}

        source_pages: set[str] = set()
        in_block = False
        for line in text.splitlines():
            if line.startswith("source_pages:"):
                in_block = True
                continue
            if in_block and line.startswith("  - "):
                source_pages.add(line[4:].strip().strip('"'))
                continue
            if in_block and line and not line.startswith(" "):
                break
        return source_pages
