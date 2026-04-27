from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from battle_engine.contracts import TeamSlot, to_payload
from battle_engine.team_structure import TeamStructureAnalyzer
from reporting.contracts import ConfidenceTier

from advisor.contracts import (
    AdvisorEvidenceItem,
    AdvisorResponse,
    AdvisorSessionState,
    AdvisorToolResult,
    DocContextSnippet,
    TeamCoherenceVerdict,
    TeamSemanticGuard,
    SourceType,
    ToolStatus,
)
from advisor.battle_dex import BattleDexRepository
from advisor.config import RocoNativeModelConfig
from advisor.retrieval import DocContextRetriever, MechanismMatch
from roco_world_model import RocoWorldTypeChart

try:
    from pydantic_ai import RunContext as PydanticAIRunContext
except ModuleNotFoundError:
    PydanticAIRunContext = Any

RunContext = PydanticAIRunContext


class Intent(StrEnum):
    HELP = "help"
    CLEAR = "clear"
    SHOW_TEAM = "show_team"
    SET_TEAM = "set_team"
    ANALYZE_TEAM = "analyze_team"
    SPECIES_QUERY = "species_query"
    EXIT = "exit"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class RouteDecision:
    intent: Intent
    tools: tuple[str, ...]
    team_slots: tuple[TeamSlot, ...] = ()
    species_query: str | None = None
    raw_argument: str | None = None


class TraceRecorder(Protocol):
    def record(self, *, message: str, response: AdvisorResponse) -> None: ...


class NullTraceRecorder:
    def record(self, *, message: str, response: AdvisorResponse) -> None:
        return None


class NativeRuntimeTimeoutError(TimeoutError):
    pass


def run_native_call_with_timeout(call, *, seconds: float) -> Any:
    if seconds <= 0:
        return call()
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(call)
    try:
        return future.result(timeout=seconds)
    except FutureTimeoutError as exc:
        future.cancel()
        raise NativeRuntimeTimeoutError(f"native runtime timeout after {seconds:.1f}s") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


class InMemorySessionStateStore:
    def __init__(self) -> None:
        self._state = AdvisorSessionState()

    def get(self) -> AdvisorSessionState:
        return self._state.model_copy(deep=True)

    def set(self, state: AdvisorSessionState) -> None:
        self._state = state.model_copy(deep=True)

    def clear(self) -> AdvisorSessionState:
        self._state = AdvisorSessionState()
        return self.get()


class TeamInputParser:
    def __init__(self, chart: RocoWorldTypeChart | None = None) -> None:
        self.chart = chart or RocoWorldTypeChart()
        names = sorted(self.chart.types, key=len, reverse=True)
        escaped = "|".join(re.escape(name) for name in names)
        self._slot_pattern = re.compile(rf"({escaped})(?:[/-]({escaped}))?")

    def parse_team_text(self, text: str) -> tuple[TeamSlot, ...]:
        matches = list(self._slot_pattern.finditer(text))
        if len(matches) < 2:
            return ()
        return tuple(
            TeamSlot(
                slot_index=index,
                species_key=None,
                primary_type=match.group(1),
                secondary_type=match.group(2),
            )
            for index, match in enumerate(matches, start=1)
        )

    def parse_set_team_argument(self, raw_argument: str) -> tuple[TeamSlot, ...]:
        parts = [part.strip() for part in re.split(r"[\s,，|]+", raw_argument) if part.strip()]
        slots: list[TeamSlot] = []
        for index, part in enumerate(parts, start=1):
            normalized = part.split(":", 1)[-1]
            match = self._slot_pattern.fullmatch(normalized)
            if match is None:
                raise ValueError(f"Unsupported team token: {part}")
            slots.append(
                TeamSlot(
                    slot_index=index,
                    species_key=None,
                    primary_type=match.group(1),
                    secondary_type=match.group(2),
                )
            )
        if not slots:
            raise ValueError("No valid team slots were provided")
        return tuple(slots)


class ToolRouter:
    def __init__(
        self,
        *,
        repository: BattleDexRepository | None = None,
        team_parser: TeamInputParser | None = None,
    ) -> None:
        self.repository = repository
        self.team_parser = team_parser or TeamInputParser()

    def route(self, message: str, state: AdvisorSessionState) -> RouteDecision:
        stripped = message.strip()
        if not stripped:
            return RouteDecision(Intent.UNSUPPORTED, ())

        if stripped.startswith("/"):
            return self._route_command(stripped)

        lowered = stripped.lower()
        if "help" in lowered or "怎么用" in stripped:
            return RouteDecision(Intent.HELP, ())
        if "清空" in stripped:
            return RouteDecision(Intent.CLEAR, ())
        if "当前队伍" in stripped or "show team" in lowered:
            return RouteDecision(Intent.SHOW_TEAM, ())
        if self._wants_future_or_live_meta(stripped):
            return RouteDecision(Intent.UNSUPPORTED, (), raw_argument="future_or_live_meta")

        extracted_team = self.team_parser.parse_team_text(stripped)
        if extracted_team:
            if self._wants_team_analysis(stripped):
                return RouteDecision(
                    Intent.ANALYZE_TEAM,
                    ("analyze_team_structure", "retrieve_doc_context"),
                    team_slots=extracted_team,
                )
            return RouteDecision(Intent.SET_TEAM, (), team_slots=extracted_team)

        if self._wants_team_analysis(stripped):
            return RouteDecision(
                Intent.ANALYZE_TEAM,
                ("analyze_team_structure", "retrieve_doc_context"),
            )

        species_query = self._extract_species_query(stripped, state)
        if species_query:
            return RouteDecision(
                Intent.SPECIES_QUERY,
                (
                    "get_species_profile",
                    "get_species_available_moves",
                    "retrieve_doc_context",
                    "analyze_species_semantics",
                ),
                species_query=species_query,
            )

        return RouteDecision(Intent.UNSUPPORTED, ())

    def _route_command(self, raw_command: str) -> RouteDecision:
        command, _, rest = raw_command.partition(" ")
        argument = rest.strip()
        if command == "/help":
            return RouteDecision(Intent.HELP, ())
        if command == "/clear":
            return RouteDecision(Intent.CLEAR, ())
        if command in {"/team", "/show-team"}:
            return RouteDecision(Intent.SHOW_TEAM, ())
        if command == "/exit":
            return RouteDecision(Intent.EXIT, ())
        if command == "/analyze":
            return RouteDecision(
                Intent.ANALYZE_TEAM,
                ("analyze_team_structure", "retrieve_doc_context"),
            )
        if command == "/species":
            return RouteDecision(
                Intent.SPECIES_QUERY,
                (
                    "get_species_profile",
                    "get_species_available_moves",
                    "retrieve_doc_context",
                    "analyze_species_semantics",
                ),
                species_query=argument or None,
                raw_argument=argument or None,
            )
        if command == "/set-team":
            slots = self.team_parser.parse_set_team_argument(argument)
            return RouteDecision(Intent.SET_TEAM, (), team_slots=slots, raw_argument=argument)
        return RouteDecision(Intent.UNSUPPORTED, (), raw_argument=argument or None)

    def _wants_team_analysis(self, message: str) -> bool:
        keywords = ("分析", "联防", "洞", "补洞", "结构", "weakness", "analyze", "/analyze")
        lowered = message.lower()
        return any(keyword in lowered for keyword in keywords)

    def _wants_future_or_live_meta(self, message: str) -> bool:
        lowered = message.lower()
        future_markers = ("明天", "未来", "下个版本", "会不会", "预测", "forecast", "predict", "future")
        official_balance_markers = (
            "官方",
            "加强",
            "削弱",
            "改动",
            "公告",
            "版本",
            "buff",
            "nerf",
            "balance patch",
        )
        live_meta_markers = (
            "live meta",
            "实时环境",
            "当前环境",
            "环境热门",
            "环境变化",
            "热门",
            "胜率",
            "meta",
        )
        future_prediction = any(marker in lowered for marker in future_markers) and any(
            marker in lowered for marker in official_balance_markers + live_meta_markers
        )
        live_meta_request = any(marker in lowered for marker in live_meta_markers)
        return future_prediction or live_meta_request

    def is_future_or_live_meta_refusal(self, route: RouteDecision) -> bool:
        return route.intent == Intent.UNSUPPORTED and route.raw_argument == "future_or_live_meta"

    def _extract_species_query(self, message: str, state: AdvisorSessionState) -> str | None:
        if self.repository is None:
            if state.current_species_context and any(pronoun in message for pronoun in ("它", "这只", "这个精灵")):
                return state.current_species_context
            return None

        if state.current_species_context and any(pronoun in message for pronoun in ("它", "这只", "这个精灵")):
            return state.current_species_context

        normalized = message
        for marker in ("适合", "干什么", "定位", "角色", "招式", "怎么样", "在这队里", "更像", "还是"):
            normalized = normalized.replace(marker, " ")
        candidates = sorted(
            {token for token in re.findall(r"[A-Za-z0-9一-龥“”'_-]{2,}", normalized)},
            key=len,
            reverse=True,
        )
        for token in candidates:
            hits = self.repository.search_species(token, limit=3)
            if any(hit.display_name == token or hit.initial_species_name == token for hit in hits):
                return token
        for token in candidates:
            hits = self.repository.search_species(token, limit=1)
            if hits:
                return hits[0].display_name
        return None


class ContextBuilder:
    def build(
        self,
        *,
        facts: list[AdvisorEvidenceItem],
        mechanics: list[DocContextSnippet],
    ) -> list[AdvisorEvidenceItem]:
        evidence = list(facts)
        for snippet in mechanics:
            evidence.append(
                AdvisorEvidenceItem(
                    source_type=SourceType.DOC,
                    source_label=snippet.source_path,
                    confidence=snippet.confidence,
                    content=snippet.content,
                    retrieval_reason=snippet.retrieval_reason,
                )
            )
        return evidence


@dataclass
class ToolTrace:
    tool_results: list[AdvisorToolResult] = field(default_factory=list)
    evidence_summary: list[AdvisorEvidenceItem] = field(default_factory=list)
    species_display_name: str | None = None
    species_id: str | None = None
    team_structure_report: Any | None = None
    team_semantic_guard: TeamSemanticGuard | None = None
    species_profile: Any | None = None
    species_moves: list[Any] = field(default_factory=list)
    species_semantics: dict[str, Any] | None = None

    def add_tool_result(self, tool_result: AdvisorToolResult) -> None:
        self.tool_results.append(tool_result)

    def add_evidence(self, evidence: AdvisorEvidenceItem) -> None:
        key = (
            evidence.source_type,
            evidence.source_label,
            evidence.confidence,
            evidence.content,
            evidence.retrieval_reason,
        )
        existing = {
            (
                item.source_type,
                item.source_label,
                item.confidence,
                item.content,
                item.retrieval_reason,
            )
            for item in self.evidence_summary
        }
        if key not in existing:
            self.evidence_summary.append(evidence)


@dataclass
class NativeAdvisorDeps:
    repository: BattleDexRepository | None
    analyzer: TeamStructureAnalyzer
    doc_retriever: DocContextRetriever
    state: AdvisorSessionState
    route: RouteDecision
    message: str
    trace: ToolTrace = field(default_factory=ToolTrace)


def _analyze_species_semantics_payload(profile: Any, moves: list[Any]) -> dict[str, Any]:
    status_moves = [move for move in moves if move.category_raw == "状态"]
    attack_moves = [move for move in moves if move.category_raw in {"物攻", "魔攻"}]
    high_power_moves = [move for move in moves if (move.power or 0) >= 100]

    pressure_tags: list[str] = []
    if profile.base_stats.spe >= 100:
        pressure_tags.append("speed_lean")
    if max(profile.base_stats.atk, profile.base_stats.spa) >= 100 or len(high_power_moves) >= 2:
        pressure_tags.append("breaker_pressure")
    if len(status_moves) >= 3:
        pressure_tags.append("utility_access")
    if profile.base_stats.hp + max(profile.base_stats.defense, profile.base_stats.spd) >= 150:
        pressure_tags.append("bulk_present")

    if "breaker_pressure" in pressure_tags and "utility_access" in pressure_tags:
        interpretation = "它同时有输出和功能技入口，更像 team-conditional 的副C/功能位混合体"
    elif "breaker_pressure" in pressure_tags:
        interpretation = "它更像带进攻压力的输出位，但仍需要已选配招才能区分主C还是副C"
    elif "utility_access" in pressure_tags:
        interpretation = "它更像功能位或辅助位候选，但没有案例库前不能下硬结论"
    else:
        interpretation = "现有事实更适合做保守描述，角色归因仍应视为开放问题"

    return {
        "semantic_roles": pressure_tags,
        "summary_line": f"provisional_tags={','.join(pressure_tags) or 'none'}",
        "interpretation": interpretation,
        "status_move_count": len(status_moves),
        "attack_move_count": len(attack_moves),
        "high_power_move_count": len(high_power_moves),
    }


def _resolve_team_slots(route: RouteDecision, state: AdvisorSessionState) -> tuple[TeamSlot, ...]:
    if route.team_slots:
        return route.team_slots
    return tuple(_team_slot_from_payload(slot_payload) for slot_payload in state.current_team)


def _team_slot_from_payload(slot_payload: dict[str, Any]) -> TeamSlot:
    normalized = dict(slot_payload)
    normalized.setdefault("species_key", None)
    return TeamSlot(**normalized)


def _resolve_species_query(deps: NativeAdvisorDeps, species_key: str | None = None) -> str | None:
    return (
        species_key
        or deps.route.species_query
        or deps.trace.species_display_name
        or deps.state.current_species_context
    )


def _is_species_not_found_result(result: AdvisorToolResult) -> bool:
    if result.tool_name != "get_species_profile" or result.status != ToolStatus.REFUSED:
        return False
    if not result.payload:
        return False
    error = result.payload.get("error")
    return isinstance(error, str) and error.startswith("species_not_found:")


def _has_dual_type_baseline_note(notes: list[str]) -> bool:
    lowered = [note.lower() for note in notes]
    return any("dual-type" in note or "双属性" in note for note in lowered)


def _is_partial_team(slots: tuple[TeamSlot, ...] | list[TeamSlot]) -> bool:
    return 0 < len(slots) < 6


def _partial_team_note(slots: tuple[TeamSlot, ...] | list[TeamSlot]) -> str:
    return f"当前只识别到 {len(slots)} 个队伍槽位；这是 partial-team 结构分析，不应当作完整六槽队伍结论。"


def _add_partial_team_caveat(response: AdvisorResponse, slots: tuple[TeamSlot, ...] | list[TeamSlot]) -> AdvisorResponse:
    if not _is_partial_team(slots):
        return response

    note = _partial_team_note(slots)
    updated = response.model_copy(deep=True)
    if note not in updated.confidence_notes:
        updated.confidence_notes.append(note)
    prefix = f"注意：{note} "
    if not updated.answer_summary.startswith("注意："):
        updated.answer_summary = prefix + updated.answer_summary
    missing = 6 - len(slots)
    followup = f"补充剩余 {missing} 个槽位后再做完整队伍分析。"
    if followup not in updated.followup_options:
        updated.followup_options.insert(0, followup)
    return updated


def _build_team_semantic_guard(
    slots: tuple[TeamSlot, ...] | list[TeamSlot],
    report: Any,
) -> TeamSemanticGuard:
    supporting_evidence: list[str] = []
    counterevidence: list[str] = []
    repeated = list(getattr(report, "repeated_weaknesses", ()))
    missing = list(getattr(report, "missing_resistances", ()))
    structural_score = float(getattr(report, "structural_score", 0.0))

    if getattr(report, "primary_patch_types", ()):
        supporting_evidence.append(
            f"至少存在可描述的补洞方向：{', '.join(getattr(report, 'primary_patch_types')[:3])}"
        )
    if structural_score >= 0.55:
        supporting_evidence.append(f"属性结构分数达到 {structural_score:.3f}")
    else:
        counterevidence.append(f"属性结构分数只有 {structural_score:.3f}")

    if repeated:
        counterevidence.append(f"重复弱点集中在 {', '.join(repeated[:4])}")
    else:
        supporting_evidence.append("没有检测到明显的重复弱点集中")

    if missing:
        counterevidence.append(f"稳定抗性缺口在 {', '.join(missing[:4])}")
    else:
        supporting_evidence.append("没有检测到明显的稳定抗性空洞")

    counterevidence.append("当前仍缺少物种、特性、技能、案例层证据，不能直接证明完整队伍计划")

    if _is_partial_team(slots):
        counterevidence.insert(0, _partial_team_note(slots))
        verdict = TeamCoherenceVerdict.INSUFFICIENT_EVIDENCE
        score = min(structural_score, 0.35)
        candidate_plan = "当前只够做 partial-team 结构判读，无法确认完整六槽计划。"
    elif structural_score < 0.45 or len(repeated) >= 2 or len(missing) >= 3:
        verdict = TeamCoherenceVerdict.INTERNALLY_CONFLICTED
        score = min(structural_score, 0.4)
        candidate_plan = "目前更像是内部有冲突的拼装队，而不是已证明自洽的成熟体系。"
    elif structural_score >= 0.65 and not repeated and len(missing) <= 1:
        verdict = TeamCoherenceVerdict.PARTIALLY_COHERENT
        score = min(structural_score, 0.7)
        candidate_plan = "属性结构层面存在基本轮转雏形，但还不足以证明明确 win condition。"
    else:
        verdict = TeamCoherenceVerdict.GOODSTUFF_WITHOUT_CLEAR_PLAN
        score = min(max(structural_score, 0.45), 0.6)
        candidate_plan = "更像有一些单点强度或补洞意识，但暂时看不出清晰、被证实的整体计划。"

    return TeamSemanticGuard(
        candidate_plan=candidate_plan,
        supporting_evidence=supporting_evidence,
        counterevidence=counterevidence,
        coherence_verdict=verdict,
        coherence_score=round(score, 3),
    )


def _species_mechanism_evidence_texts(profile: Any, moves: list[Any]) -> list[str]:
    texts: list[str] = []
    if profile and getattr(profile, "ability_effect_text", None):
        texts.append(str(profile.ability_effect_text))
    texts.extend(move.move_name for move in moves if getattr(move, "move_name", None))
    texts.extend(str(move.effect_text) for move in moves if getattr(move, "effect_text", None))
    return texts


def _split_mechanism_matches(
    matches: list[MechanismMatch],
) -> tuple[list[MechanismMatch], list[str]]:
    resolved = [match for match in matches if match.has_reviewed_page and match.page_path]
    missing = [match.token for match in matches if not match.has_reviewed_page]
    return resolved, missing


def _mechanism_doc_payload(
    snippets: list[DocContextSnippet],
    mechanism_matches: list[MechanismMatch],
) -> dict[str, Any]:
    resolved, missing = _split_mechanism_matches(mechanism_matches)
    return {
        "topics": [snippet.topic for snippet in snippets],
        "resolved_mechanism_tokens": [match.token for match in resolved],
        "missing_reviewed_tokens": missing,
    }


def _mechanism_tool_summary(
    snippets: list[DocContextSnippet],
    mechanism_matches: list[MechanismMatch],
) -> str:
    resolved, missing = _split_mechanism_matches(mechanism_matches)
    parts = [f"retrieved {len(snippets)} approved doc snippets"]
    if resolved:
        parts.append("mechanism_hits=" + ",".join(match.token for match in resolved))
    if missing:
        parts.append("missing_reviewed=" + ",".join(missing))
    return "; ".join(parts)


def _has_mechanism_evidence(
    evidence_summary: list[AdvisorEvidenceItem],
    mechanism_matches: list[MechanismMatch],
) -> bool:
    expected_sources = {
        f"wiki/{match.page_path}"
        for match in mechanism_matches
        if match.has_reviewed_page and match.page_path
    }
    if not expected_sources:
        return True
    seen_sources = {item.source_label for item in evidence_summary if item.source_type == SourceType.DOC}
    return bool(expected_sources & seen_sources)


def _auto_doc_snippets(
    retriever: DocContextRetriever,
    *,
    query: str,
    analysis_type: str,
    evidence_texts: list[str],
    limit: int = 4,
) -> tuple[list[DocContextSnippet], list[MechanismMatch]]:
    mechanism_matches = retriever.inspect_mechanisms(query=query, evidence_texts=evidence_texts)
    snippets = retriever.retrieve(
        query=query,
        analysis_type=analysis_type,
        limit=limit,
        evidence_texts=evidence_texts,
    )
    return snippets, mechanism_matches


def _ensure_doc_context_trace(
    trace: ToolTrace,
    *,
    retriever: DocContextRetriever,
    query: str,
    analysis_type: str,
    evidence_texts: list[str],
    limit: int = 4,
) -> list[MechanismMatch]:
    snippets, mechanism_matches = _auto_doc_snippets(
        retriever,
        query=query,
        analysis_type=analysis_type,
        evidence_texts=evidence_texts,
        limit=limit,
    )
    payload = _mechanism_doc_payload(snippets, mechanism_matches)
    existing_tool = next(
        (tool for tool in trace.tool_results if tool.tool_name == "retrieve_doc_context"),
        None,
    )
    if existing_tool is None:
        trace.add_tool_result(
            AdvisorToolResult(
                tool_name="retrieve_doc_context",
                summary=_mechanism_tool_summary(snippets, mechanism_matches),
                payload=payload,
            )
        )
    else:
        existing_tool.summary = _mechanism_tool_summary(snippets, mechanism_matches)
        existing_tool.payload = payload
    for snippet in snippets:
        trace.add_evidence(
            AdvisorEvidenceItem(
                source_type=SourceType.DOC,
                source_label=snippet.source_path,
                confidence=snippet.confidence,
                content=snippet.content,
                retrieval_reason=snippet.retrieval_reason,
            )
        )
    return mechanism_matches


def _team_answer_summary(report: Any, guard: TeamSemanticGuard) -> str:
    repeated = getattr(report, "repeated_weaknesses")
    missing = getattr(report, "missing_resistances")
    primary_patch_types = getattr(report, "primary_patch_types")
    fragments = [
        "当前队伍默认按 unknown-quality team 处理，不预设它本来就有成熟计划。",
        (
            f"属性结构分为 {getattr(report, 'structural_score'):.3f}，"
            f"当前更接近 `{guard.coherence_verdict}`（score={guard.coherence_score:.3f}）。"
        ),
        guard.candidate_plan,
    ]
    if repeated:
        fragments.append(f"重复弱点集中在 {', '.join(repeated[:4])}。")
    if missing:
        fragments.append(f"稳定抗性缺口在 {', '.join(missing[:4])}。")
    if primary_patch_types:
        fragments.append(f"默认单属性补洞方向优先看 {', '.join(primary_patch_types[:3])}。")
    else:
        fragments.append("当前没有明显正收益的单属性补洞方向。")
    if guard.counterevidence:
        fragments.append(f"当前最关键的反证是：{guard.counterevidence[0]}。")
    return " ".join(fragments)


def _species_answer_summary(
    profile: Any,
    moves: list[Any],
    semantics: dict[str, Any],
    mechanism_matches: list[MechanismMatch],
) -> str:
    move_names = ", ".join(move.move_name for move in moves[:5]) if moves else "暂无已解析技能"
    ability_line = f"特性 `{profile.ability_name}`" if getattr(profile, "ability_name", None) else "特性信息不完整"
    summary = (
        f"{profile.display_name} 的已入库事实是 {profile.primary_type}/{profile.secondary_type or '-'}，"
        f"BST {profile.base_stats.bst}，{ability_line}。"
        f" 当前已解析技能包括 {move_names}。"
        f" 基于面板与技能池的 provisional 判断：{semantics['interpretation']}。"
    )
    resolved, missing = _split_mechanism_matches(mechanism_matches)
    if resolved:
        summary += (
            " 这次已自动加载 reviewed 机制页："
            + ", ".join(f"`{match.token}`" for match in resolved)
            + "。"
        )
    if missing:
        summary += (
            " 文本里检测到机制词 "
            + ", ".join(f"`{token}`" for token in missing)
            + "，但 reviewed wiki 还没有完整定义它们，所以这里不解释其确切执行规则。"
        )
    return summary


_NATIVE_AGENT: Any | None = None


def _build_native_agent() -> Any:
    global _NATIVE_AGENT
    if _NATIVE_AGENT is not None:
        return _NATIVE_AGENT

    try:
        from pydantic_ai import Agent, ModelRetry, RunContext
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "pydantic_ai is not installed in the active interpreter. "
            "Use the project .venv or install `pydantic-ai-slim[openai]`."
        ) from exc

    agent = Agent(
        output_type=AdvisorResponse,
        deps_type=NativeAdvisorDeps,
        system_prompt=(
            "You are the Roco conversational advisor. "
            "Use approved tools, ground confirmed claims only in deterministic engine or SQL facts, "
            "and keep species role judgements provisional. "
            "Do not invent tool results or evidence. "
            "Focus your output on answer_summary, confidence_notes, and followup_options."
        ),
        output_retries=2,
        defer_model_check=True,
    )

    @agent.tool
    def analyze_team_structure(ctx: RunContext[NativeAdvisorDeps]) -> dict[str, Any]:
        """Analyze the current team structure from deterministic type data."""
        slots = _resolve_team_slots(ctx.deps.route, ctx.deps.state)
        if not slots:
            payload = {"error": "no_team_in_session"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="analyze_team_structure",
                    status=ToolStatus.REFUSED,
                    summary="no team is currently available",
                    payload=payload,
                )
            )
            return payload

        report = ctx.deps.analyzer.analyze(slots)
        ctx.deps.trace.team_structure_report = report
        ctx.deps.trace.add_tool_result(
            AdvisorToolResult(
                tool_name="analyze_team_structure",
                summary=(
                    f"structural_score={report.structural_score:.3f}, "
                    f"repeated={len(report.repeated_weaknesses)}, "
                    f"missing_resistances={len(report.missing_resistances)}"
                ),
                payload=to_payload(report),
            )
        )
        for item in report.evidence[:6]:
            ctx.deps.trace.add_evidence(
                AdvisorEvidenceItem(
                    source_type=SourceType.ENGINE,
                    source_label="battle_engine.team_structure",
                    confidence=ConfidenceTier.CONFIRMED,
                    content=item,
                    retrieval_reason="deterministic_structure_output",
                )
            )
        return to_payload(report)

    @agent.tool
    def get_species_profile(
        ctx: RunContext[NativeAdvisorDeps],
        species_key: str | None = None,
    ) -> dict[str, Any]:
        """Load a species profile from the approved SQLite battle dex."""
        if ctx.deps.repository is None:
            payload = {"error": "battle_dex_unavailable"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="get_species_profile",
                    status=ToolStatus.REFUSED,
                    summary="battle dex repository is unavailable",
                    payload=payload,
                )
            )
            return payload

        query = _resolve_species_query(ctx.deps, species_key)
        if not query:
            payload = {"error": "missing_species_query"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="get_species_profile",
                    status=ToolStatus.REFUSED,
                    summary="no species query is available",
                    payload=payload,
                )
            )
            return payload

        profile = ctx.deps.repository.get_species_profile(query)
        if profile is None:
            payload = {"error": f"species_not_found:{query}"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="get_species_profile",
                    status=ToolStatus.REFUSED,
                    summary=f"no species profile found for {query}",
                    payload=payload,
                )
            )
            return payload

        ctx.deps.trace.species_display_name = profile.display_name
        ctx.deps.trace.species_id = profile.species_id
        ctx.deps.trace.species_profile = profile
        ctx.deps.trace.add_tool_result(
            AdvisorToolResult(
                tool_name="get_species_profile",
                summary=f"loaded {profile.display_name} ({profile.primary_type}/{profile.secondary_type or '-'})",
                payload=profile.model_dump(mode="json"),
            )
        )
        ctx.deps.trace.add_evidence(
            AdvisorEvidenceItem(
                source_type=SourceType.FACT,
                source_label=f"species_form:{profile.species_id}",
                confidence=profile.confidence,
                content=(
                    f"{profile.display_name}: type={profile.primary_type}/{profile.secondary_type or '-'} "
                    f"bst={profile.base_stats.bst} ability={profile.ability_name or 'unknown'}"
                ),
                retrieval_reason="sql_species_profile",
            )
        )
        if profile.ability_name:
            ability = ctx.deps.repository.get_ability_detail(profile.ability_name)
            if ability is not None:
                ctx.deps.trace.add_evidence(
                    AdvisorEvidenceItem(
                        source_type=SourceType.FACT,
                        source_label=f"derived_ability:{ability.ability_id}",
                        confidence=ability.confidence,
                        content=f"{ability.ability_name}: {ability.effect_text}",
                        retrieval_reason="sql_ability_lookup",
                    )
                )
        return profile.model_dump(mode="json")

    @agent.tool
    def get_species_available_moves(
        ctx: RunContext[NativeAdvisorDeps],
        species_key: str | None = None,
        limit: int | None = 10,
    ) -> dict[str, Any]:
        """Load available moves for a species from the approved SQLite battle dex."""
        if ctx.deps.repository is None:
            payload = {"moves": [], "error": "battle_dex_unavailable"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="get_species_available_moves",
                    status=ToolStatus.REFUSED,
                    summary="battle dex repository is unavailable",
                    payload=payload,
                )
            )
            return payload

        query = _resolve_species_query(ctx.deps, species_key)
        if not query:
            payload = {"moves": [], "error": "missing_species_query"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="get_species_available_moves",
                    status=ToolStatus.REFUSED,
                    summary="no species query is available",
                    payload=payload,
                )
            )
            return payload

        moves = ctx.deps.repository.get_species_available_moves(query, limit=limit)
        ctx.deps.trace.species_moves = list(moves)
        payload = {"moves": [move.model_dump(mode="json") for move in moves]}
        ctx.deps.trace.add_tool_result(
            AdvisorToolResult(
                tool_name="get_species_available_moves",
                summary=f"loaded {len(moves)} move records",
                payload=payload,
            )
        )
        if moves:
            species_ref = ctx.deps.trace.species_id or query
            ctx.deps.trace.add_evidence(
                AdvisorEvidenceItem(
                    source_type=SourceType.FACT,
                    source_label=f"species_move_pool:{species_ref}",
                    confidence=ConfidenceTier.CONFIRMED,
                    content="moves=" + ",".join(move.move_name for move in moves[:6]),
                    retrieval_reason="sql_move_pool_lookup",
                )
            )
        return payload

    @agent.tool
    def retrieve_doc_context(
        ctx: RunContext[NativeAdvisorDeps],
        analysis_type: str | None = None,
        query: str | None = None,
        limit: int = 4,
    ) -> dict[str, Any]:
        """Retrieve bounded approved mechanics or methodology snippets from local docs."""
        resolved_analysis_type = analysis_type or (
            "team" if ctx.deps.route.intent == Intent.ANALYZE_TEAM else "species"
        )
        resolved_query = query or ctx.deps.message
        evidence_texts = (
            _species_mechanism_evidence_texts(
                ctx.deps.trace.species_profile,
                ctx.deps.trace.species_moves,
            )
            if resolved_analysis_type == "species"
            else []
        )
        snippets, mechanism_matches = _auto_doc_snippets(
            ctx.deps.doc_retriever,
            query=resolved_query,
            analysis_type=resolved_analysis_type,
            evidence_texts=evidence_texts,
            limit=limit,
        )
        ctx.deps.trace.add_tool_result(
            AdvisorToolResult(
                tool_name="retrieve_doc_context",
                summary=_mechanism_tool_summary(snippets, mechanism_matches),
                payload=_mechanism_doc_payload(snippets, mechanism_matches),
            )
        )
        for snippet in snippets:
            ctx.deps.trace.add_evidence(
                AdvisorEvidenceItem(
                    source_type=SourceType.DOC,
                    source_label=snippet.source_path,
                    confidence=snippet.confidence,
                    content=snippet.content,
                    retrieval_reason=snippet.retrieval_reason,
                )
            )
        return {"snippets": [snippet.model_dump(mode="json") for snippet in snippets]}

    @agent.tool
    def analyze_species_semantics(
        ctx: RunContext[NativeAdvisorDeps],
        species_key: str | None = None,
    ) -> dict[str, Any]:
        """Produce bounded provisional species-role interpretation from approved facts."""
        if ctx.deps.repository is None:
            payload = {"error": "battle_dex_unavailable"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="analyze_species_semantics",
                    status=ToolStatus.REFUSED,
                    summary="battle dex repository is unavailable",
                    payload=payload,
                )
            )
            return payload

        query = _resolve_species_query(ctx.deps, species_key)
        if not query:
            payload = {"error": "missing_species_query"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="analyze_species_semantics",
                    status=ToolStatus.REFUSED,
                    summary="no species query is available",
                    payload=payload,
                )
            )
            return payload

        profile = ctx.deps.repository.get_species_profile(query)
        if profile is None:
            payload = {"error": f"species_not_found:{query}"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="analyze_species_semantics",
                    status=ToolStatus.REFUSED,
                    summary=f"no species profile found for {query}",
                    payload=payload,
                )
            )
            return payload

        moves = ctx.deps.repository.get_species_available_moves(profile.species_id, limit=10)
        payload = _analyze_species_semantics_payload(profile, moves)
        ctx.deps.trace.species_semantics = payload
        ctx.deps.trace.add_tool_result(
            AdvisorToolResult(
                tool_name="analyze_species_semantics",
                summary=payload["summary_line"],
                payload=payload,
            )
        )
        return payload

    @agent.output_validator
    def validate_output(ctx: RunContext[NativeAdvisorDeps], output: AdvisorResponse) -> AdvisorResponse:
        merged = output.model_copy(deep=True)
        merged.backend = "pydantic_ai_native"
        merged.tool_results = list(ctx.deps.trace.tool_results)
        merged.evidence_summary = list(ctx.deps.trace.evidence_summary)
        merged.answer_summary = merged.answer_summary.strip()

        if not merged.answer_summary:
            raise ModelRetry("answer_summary must not be empty")

        if ctx.deps.route.intent == Intent.ANALYZE_TEAM and not any(
            result.tool_name == "analyze_team_structure" and result.status == ToolStatus.OK
            for result in merged.tool_results
        ):
            raise ModelRetry("team analysis must call analyze_team_structure")

        if ctx.deps.route.intent == Intent.SPECIES_QUERY:
            species_profile_results = [
                result for result in merged.tool_results if result.tool_name == "get_species_profile"
            ]
            has_ok_profile = any(result.status == ToolStatus.OK for result in species_profile_results)
            has_not_found_profile = any(
                _is_species_not_found_result(result) for result in species_profile_results
            )
            if not has_ok_profile and not has_not_found_profile:
                raise ModelRetry("species analysis must call get_species_profile")
            if has_not_found_profile:
                query = ctx.deps.route.species_query or "该精灵"
                merged.answer_summary = (
                    f"battle-dex 里没有找到 `{query}`。当前只支持已入库物种的事实查询。"
                )
                merged.evidence_summary = []
                if not merged.followup_options:
                    merged.followup_options = ["/species 豆丁鱼", "/show-team"]

        if ctx.deps.route.intent == Intent.ANALYZE_TEAM and ctx.deps.trace.team_structure_report is not None:
            guard = ctx.deps.trace.team_semantic_guard or _build_team_semantic_guard(
                _resolve_team_slots(ctx.deps.route, ctx.deps.state),
                ctx.deps.trace.team_structure_report,
            )
            ctx.deps.trace.team_semantic_guard = guard
            if not any(tool.tool_name == "analyze_team_semantics_guard" for tool in ctx.deps.trace.tool_results):
                ctx.deps.trace.add_tool_result(
                    AdvisorToolResult(
                        tool_name="analyze_team_semantics_guard",
                        summary=(
                            f"coherence_verdict={guard.coherence_verdict}; "
                            f"coherence_score={guard.coherence_score:.3f}"
                        ),
                        payload=guard.model_dump(mode="json"),
                    )
                )
            _ensure_doc_context_trace(
                ctx.deps.trace,
                retriever=ctx.deps.doc_retriever,
                query=ctx.deps.message,
                analysis_type="team",
                evidence_texts=[],
            )
            merged.tool_results = list(ctx.deps.trace.tool_results)
            merged.evidence_summary = list(ctx.deps.trace.evidence_summary)
            merged.answer_summary = _team_answer_summary(ctx.deps.trace.team_structure_report, guard)
            if not any("unknown-quality" in note.lower() for note in merged.confidence_notes):
                merged.confidence_notes.insert(
                    0,
                    "队伍输入默认视为 unknown-quality team；当前分析是在检验它是否自洽，而不是默认它已经有成熟计划。",
                )

        if (
            ctx.deps.route.intent == Intent.SPECIES_QUERY
            and ctx.deps.trace.species_profile is not None
            and not has_not_found_profile
        ):
            mechanism_matches = _ensure_doc_context_trace(
                ctx.deps.trace,
                retriever=ctx.deps.doc_retriever,
                query=ctx.deps.message,
                analysis_type="species",
                evidence_texts=_species_mechanism_evidence_texts(
                    ctx.deps.trace.species_profile,
                    ctx.deps.trace.species_moves,
                ),
            )
            merged.tool_results = list(ctx.deps.trace.tool_results)
            merged.evidence_summary = list(ctx.deps.trace.evidence_summary)
            if not _has_mechanism_evidence(merged.evidence_summary, mechanism_matches):
                merged.confidence_notes.insert(
                    0,
                    "检测到机制词但没有匹配的 reviewed 机制证据，因此当前输出已强制降级为保守描述。",
                )
            merged.answer_summary = _species_answer_summary(
                ctx.deps.trace.species_profile,
                ctx.deps.trace.species_moves,
                ctx.deps.trace.species_semantics
                or _analyze_species_semantics_payload(
                    ctx.deps.trace.species_profile,
                    ctx.deps.trace.species_moves,
                ),
                mechanism_matches,
            )

        if not merged.followup_options:
            merged.followup_options = _default_followups(ctx.deps.route, ctx.deps.trace)

        if ctx.deps.route.intent == Intent.SPECIES_QUERY and not any(
            "provisional" in note.lower() for note in merged.confidence_notes
        ):
            merged.confidence_notes.append(
                "物种定位判断仍是 provisional hypothesis；没有案例库和已选配招前，不应上升为唯一正确角色。"
            )

        if ctx.deps.route.intent == Intent.ANALYZE_TEAM and not any(
            "confirmed" in note.lower() or "deterministic" in note.lower()
            for note in merged.confidence_notes
        ):
            merged.confidence_notes.append(
                "结构结论属于 confirmed，因为它们直接来自 deterministic Engine 输出。"
            )
        if ctx.deps.route.intent == Intent.ANALYZE_TEAM and not _has_dual_type_baseline_note(
            merged.confidence_notes
        ):
            merged.confidence_notes.append(
                "双属性承伤解释仍按当前项目 provisional baseline 处理，不应上升为硬机制结论。"
            )

        return merged

    _NATIVE_AGENT = agent
    return agent


def _default_followups(route: RouteDecision, trace: ToolTrace) -> list[str]:
    if route.intent == Intent.ANALYZE_TEAM:
        return [
            "继续问：这队补洞方向是什么",
            "继续问：如果把 3 号位换成火系会怎样",
            "继续问：某只精灵在这队里更像什么定位",
        ]
    if route.intent == Intent.SPECIES_QUERY:
        species_name = trace.species_display_name or route.species_query or "这只精灵"
        return [
            f"继续问：{species_name} 在这队里更像主C还是辅助",
            f"继续问：{species_name} 常见可用技能有哪些",
            "继续问：分析这队联防",
        ]
    return ["/help"]


class AdvisorAgent:
    def __init__(
        self,
        *,
        repository: BattleDexRepository | None = None,
        analyzer: TeamStructureAnalyzer | None = None,
        doc_retriever: DocContextRetriever | None = None,
        router: ToolRouter | None = None,
        state_store: InMemorySessionStateStore | None = None,
        trace_recorder: TraceRecorder | None = None,
        backend: str = "deterministic",
        model_name: str | None = None,
        native_model: Any | None = None,
        auto_selected: bool = False,
        native_timeout_seconds: float = 15.0,
    ) -> None:
        normalized_backend = "pydantic_ai_native" if backend == "pydantic_ai" else backend
        self.repository = repository
        self.analyzer = analyzer or TeamStructureAnalyzer()
        self.doc_retriever = doc_retriever or DocContextRetriever()
        self.state_store = state_store or InMemorySessionStateStore()
        self.router = router or ToolRouter(repository=repository)
        self.trace_recorder = trace_recorder or NullTraceRecorder()
        self.backend = normalized_backend
        self.model_name = model_name
        self.native_model = native_model
        self.auto_selected = auto_selected
        self.native_timeout_seconds = native_timeout_seconds
        self._native_unhealthy_reason: str | None = None

    def handle_message(self, message: str) -> AdvisorResponse:
        state = self.state_store.get()
        route = self.router.route(message, state)

        if route.intent == Intent.HELP:
            response = self._help_response()
        elif route.intent == Intent.CLEAR:
            self.state_store.clear()
            response = self._simple_response(
                "已清空当前会话状态。你可以重新设置队伍，或直接查询某只精灵。",
                followup_options=["/set-team 草 地 龙 翼 火 水", "/species 豆丁鱼"],
            )
        elif route.intent == Intent.SHOW_TEAM:
            response = self._show_team_response(state)
        elif route.intent == Intent.SET_TEAM:
            updated_state = state.model_copy(deep=True)
            updated_state.current_team = [to_payload(slot) for slot in route.team_slots]
            updated_state.last_analysis_type = "team_context"
            updated_state.last_result_ref = "team_set"
            self.state_store.set(updated_state)
            response = self._simple_response(
                f"已记录当前队伍：{self._format_team(route.team_slots)}。",
                followup_options=["分析这队联防", "补洞方向是什么"],
            )
        elif route.intent == Intent.ANALYZE_TEAM:
            response = (
                self._run_native_or_auto_fallback(message, route, state)
                if self.backend == "pydantic_ai_native"
                else self._handle_team_analysis_deterministic(message, route, state)
            )
        elif route.intent == Intent.SPECIES_QUERY:
            response = (
                self._run_native_or_auto_fallback(message, route, state)
                if self.backend == "pydantic_ai_native"
                else self._handle_species_query_deterministic(message, route, state)
            )
        elif route.intent == Intent.EXIT:
            response = self._simple_response("收到退出指令。", followup_options=[])
        elif self.router.is_future_or_live_meta_refusal(route):
            response = self._future_or_live_meta_refusal_response()
        else:
            response = self._simple_response(
                "当前 MVP 只支持队伍结构分析、battle-dex 物种查询和会话内追问。",
                followup_options=["/help", "/set-team 草 地 龙 翼 火 水", "/species 豆丁鱼"],
            )

        self.trace_recorder.record(message=message, response=response)
        return response

    def _run_native_or_auto_fallback(
        self,
        message: str,
        route: RouteDecision,
        state: AdvisorSessionState,
    ) -> AdvisorResponse:
        if self.auto_selected and self._native_unhealthy_reason:
            return self._auto_native_unhealthy_fallback(
                message=message,
                route=route,
                state=state,
                reason=self._native_unhealthy_reason,
            )
        return self._run_native_agent(message, route, state)

    def _run_native_agent(
        self,
        message: str,
        route: RouteDecision,
        state: AdvisorSessionState,
    ) -> AdvisorResponse:
        if route.intent == Intent.SPECIES_QUERY and self.repository is None:
            return self._simple_response(
                "battle-dex 仓库当前不可用，无法做物种级事实查询。结构分析仍可继续。",
                followup_options=["/set-team 草 地 龙 翼 火 水", "分析这队联防"],
            )

        try:
            agent = _build_native_agent()
        except RuntimeError as exc:
            return self._native_failure_response(
                route=route,
                state=state,
                reason=str(exc),
            )

        try:
            model = self._resolve_native_model()
        except Exception:
            return self._native_failure_response(
                route=route,
                state=state,
                reason="native_model_config_unavailable",
            )
        if model is None:
            return self._native_failure_response(
                route=route,
                state=state,
                reason="missing_native_model_config",
            )

        deps = NativeAdvisorDeps(
            repository=self.repository,
            analyzer=self.analyzer,
            doc_retriever=self.doc_retriever,
            state=state,
            route=route,
            message=message,
        )

        def run_agent() -> Any:
            return agent.run_sync(
                message,
                deps=deps,
                model=model,
                instructions=self._native_instructions(route, state),
            )
        try:
            result = run_native_call_with_timeout(
                run_agent,
                seconds=self.native_timeout_seconds,
            )
        except NativeRuntimeTimeoutError:
            return self._native_failure_response(
                route=route,
                state=state,
                reason=f"native runtime timeout after {self.native_timeout_seconds:.1f}s",
            )
        except Exception as exc:
            return self._native_failure_response(
                route=route,
                state=state,
                reason=f"provider/model failure: {exc.__class__.__name__}",
            )
        response = result.output
        self._update_state_after_analysis(route, state, deps.trace)
        return _add_partial_team_caveat(response, _resolve_team_slots(route, state)) if route.intent == Intent.ANALYZE_TEAM else response

    def _native_failure_response(
        self,
        *,
        route: RouteDecision,
        state: AdvisorSessionState,
        reason: str,
    ) -> AdvisorResponse:
        if self.auto_selected:
            self._native_unhealthy_reason = reason
            if route.intent == Intent.ANALYZE_TEAM:
                fallback = self._handle_team_analysis_deterministic(
                    message=f"native_fallback:{reason}",
                    route=route,
                    state=state,
                )
            elif route.intent == Intent.SPECIES_QUERY:
                fallback = self._handle_species_query_deterministic(
                    message=f"native_fallback:{reason}",
                    route=route,
                    state=state,
                )
            else:
                fallback = self._simple_response(
                    "native runtime 当前不可用，auto 已回退到 deterministic 近邻路径。",
                    followup_options=["/help"],
                )
            fallback.backend = "auto_fallback_deterministic"
            fallback.confidence_notes.insert(
                0,
                f"auto backend 已因 native runtime 不可用回退到 deterministic；reason={reason}.",
            )
            return fallback

        return self._simple_response(
            (
                "native runtime 当前不可用，已拒绝本次调用。"
                f" reason={reason}."
            ),
            followup_options=["/help", "/analyze"],
        )

    def _auto_native_unhealthy_fallback(
        self,
        *,
        message: str,
        route: RouteDecision,
        state: AdvisorSessionState,
        reason: str,
    ) -> AdvisorResponse:
        if route.intent == Intent.ANALYZE_TEAM:
            fallback = self._handle_team_analysis_deterministic(
                message=f"native_unhealthy_skip:{reason}:{message}",
                route=route,
                state=state,
            )
        elif route.intent == Intent.SPECIES_QUERY:
            fallback = self._handle_species_query_deterministic(
                message=f"native_unhealthy_skip:{reason}:{message}",
                route=route,
                state=state,
            )
        else:
            fallback = self._simple_response(
                "native runtime 已在当前 CLI 进程内标记为不可用，auto 直接使用 deterministic 近邻路径。",
                followup_options=["/help"],
            )
        fallback.backend = "auto_fallback_deterministic"
        fallback.confidence_notes.insert(
            0,
            f"auto backend 已跳过 native runtime：当前 CLI 进程内 native 已标记为不可用；reason={reason}.",
        )
        return fallback

    def _resolve_native_model(self) -> Any | None:
        if isinstance(self.native_model, RocoNativeModelConfig):
            from pydantic_ai.models.openai import OpenAIModel
            from pydantic_ai.providers.openai import OpenAIProvider

            provider = OpenAIProvider(
                base_url=self.native_model.base_url,
                api_key=self.native_model.api_key,
            )
            return OpenAIModel(self.native_model.model_name, provider=provider)
        if self.native_model is not None:
            return self.native_model
        return self.model_name or os.getenv("ROCO_ADVISOR_MODEL")

    def _native_instructions(self, route: RouteDecision, state: AdvisorSessionState) -> str:
        team_summary = (
            self._format_team(tuple(_team_slot_from_payload(slot_payload) for slot_payload in state.current_team))
            if state.current_team
            else "none"
        )
        route_lines = [
            f"Approved intent: {route.intent.value}.",
            f"Current team state: {team_summary}.",
            f"Current species context: {state.current_species_context or 'none'}.",
            "You must keep confirmed claims limited to deterministic engine or SQL-backed facts.",
            "Do not invent evidence_summary or tool_results; they are taken from tool traces.",
        ]
        if route.intent == Intent.ANALYZE_TEAM:
            route_lines.append(
                "Before finalizing, call analyze_team_structure and retrieve_doc_context."
            )
        if route.intent == Intent.SPECIES_QUERY:
            route_lines.append(
                "Before finalizing, call get_species_profile, get_species_available_moves, retrieve_doc_context, and analyze_species_semantics."
            )
        return " ".join(route_lines)

    def _update_state_after_analysis(
        self,
        route: RouteDecision,
        state: AdvisorSessionState,
        trace: ToolTrace,
    ) -> None:
        updated_state = state.model_copy(deep=True)
        if route.intent == Intent.ANALYZE_TEAM:
            slots = route.team_slots or tuple(self._slots_from_state(state))
            updated_state.current_team = [to_payload(slot) for slot in slots]
            updated_state.last_analysis_type = "team_structure"
            updated_state.last_result_ref = "team_structure"
        elif route.intent == Intent.SPECIES_QUERY:
            if trace.species_display_name:
                updated_state.current_species_context = trace.species_display_name
            updated_state.last_analysis_type = "species_query"
            updated_state.last_result_ref = trace.species_id or route.species_query
        self.state_store.set(updated_state)

    def _handle_team_analysis_deterministic(
        self,
        message: str,
        route: RouteDecision,
        state: AdvisorSessionState,
    ) -> AdvisorResponse:
        slots = route.team_slots or tuple(self._slots_from_state(state))
        if not slots:
            return self._simple_response(
                "当前没有可分析的队伍。先用 `/set-team` 或直接在一句话里给出属性列表。",
                followup_options=["/set-team 草 地 龙 翼 火 水"],
            )

        structure_report = self.analyzer.analyze(slots)
        guard = _build_team_semantic_guard(slots, structure_report)
        snippets, mechanism_matches = _auto_doc_snippets(
            self.doc_retriever,
            query=message,
            analysis_type="team",
            evidence_texts=[],
        )

        tool_results = [
            AdvisorToolResult(
                tool_name="analyze_team_structure",
                summary=(
                    f"structural_score={structure_report.structural_score:.3f}, "
                    f"repeated={len(structure_report.repeated_weaknesses)}, "
                    f"missing_resistances={len(structure_report.missing_resistances)}"
                ),
                payload=to_payload(structure_report),
            ),
            AdvisorToolResult(
                tool_name="analyze_team_semantics_guard",
                summary=(
                    f"coherence_verdict={guard.coherence_verdict}; "
                    f"coherence_score={guard.coherence_score:.3f}"
                ),
                payload=guard.model_dump(mode="json"),
            ),
            AdvisorToolResult(
                tool_name="retrieve_doc_context",
                summary=_mechanism_tool_summary(snippets, mechanism_matches),
                payload=_mechanism_doc_payload(snippets, mechanism_matches),
            ),
        ]
        facts = [
            AdvisorEvidenceItem(
                source_type=SourceType.ENGINE,
                source_label="battle_engine.team_structure",
                confidence=ConfidenceTier.CONFIRMED,
                content=item,
                retrieval_reason="deterministic_structure_output",
            )
            for item in structure_report.evidence[:6]
        ]
        evidence = ContextBuilder().build(facts=facts, mechanics=snippets)
        self._update_state_after_analysis(route, state, ToolTrace())
        response = AdvisorResponse(
            backend=self.backend,
            answer_summary=self._team_answer_summary(structure_report, guard),
            tool_results=tool_results,
            evidence_summary=evidence,
            confidence_notes=[
                "队伍输入默认视为 unknown-quality team；当前分析是在检验它是否自洽，而不是默认它已经有成熟计划。",
                "结构结论属于 confirmed，因为它们直接来自 deterministic Engine 输出。",
                "双属性承伤解释仍按当前项目 provisional baseline 处理，不应上升为硬机制结论。",
            ],
            followup_options=_default_followups(route, ToolTrace()),
        )
        return _add_partial_team_caveat(response, slots)

    def _handle_species_query_deterministic(
        self,
        message: str,
        route: RouteDecision,
        state: AdvisorSessionState,
    ) -> AdvisorResponse:
        if self.repository is None:
            return self._simple_response(
                "battle-dex 仓库当前不可用，无法做物种级事实查询。结构分析仍可继续。",
                followup_options=["/set-team 草 地 龙 翼 火 水", "分析这队联防"],
            )

        query = route.species_query or route.raw_argument
        if not query:
            return self._simple_response(
                "请给出物种名，例如 `/species 豆丁鱼`。",
                followup_options=["/species 豆丁鱼"],
            )

        profile = self.repository.get_species_profile(query)
        if profile is None:
            return self._simple_response(
                f"battle-dex 里没有找到 `{query}`。当前只支持已入库物种的事实查询。",
                followup_options=["/species 豆丁鱼", "/show-team"],
            )

        moves = self.repository.get_species_available_moves(profile.species_id, limit=10)
        ability = self.repository.get_ability_detail(profile.ability_name) if profile.ability_name else None
        evidence_texts = _species_mechanism_evidence_texts(profile, moves)
        snippets, mechanism_matches = _auto_doc_snippets(
            self.doc_retriever,
            query=message,
            analysis_type="species",
            evidence_texts=evidence_texts,
        )
        semantics = _analyze_species_semantics_payload(profile, moves)

        tool_results = [
            AdvisorToolResult(
                tool_name="get_species_profile",
                summary=f"loaded {profile.display_name} ({profile.primary_type}/{profile.secondary_type or '-'})",
                payload=profile.model_dump(mode="json"),
            ),
            AdvisorToolResult(
                tool_name="get_species_available_moves",
                summary=f"loaded {len(moves)} move records",
                payload={"moves": [move.model_dump(mode="json") for move in moves[:8]]},
            ),
            AdvisorToolResult(
                tool_name="retrieve_doc_context",
                summary=_mechanism_tool_summary(snippets, mechanism_matches),
                payload=_mechanism_doc_payload(snippets, mechanism_matches),
            ),
            AdvisorToolResult(
                tool_name="analyze_species_semantics",
                summary=semantics["summary_line"],
                payload=semantics,
            ),
        ]
        facts = [
            AdvisorEvidenceItem(
                source_type=SourceType.FACT,
                source_label=f"species_form:{profile.species_id}",
                confidence=profile.confidence,
                content=(
                    f"{profile.display_name}: type={profile.primary_type}/{profile.secondary_type or '-'} "
                    f"bst={profile.base_stats.bst} ability={profile.ability_name or 'unknown'}"
                ),
                retrieval_reason="sql_species_profile",
            )
        ]
        if ability is not None:
            facts.append(
                AdvisorEvidenceItem(
                    source_type=SourceType.FACT,
                    source_label=f"derived_ability:{ability.ability_id}",
                    confidence=ability.confidence,
                    content=f"{ability.ability_name}: {ability.effect_text}",
                    retrieval_reason="sql_ability_lookup",
                )
            )
        if moves:
            facts.append(
                AdvisorEvidenceItem(
                    source_type=SourceType.FACT,
                    source_label=f"species_move_pool:{profile.species_id}",
                    confidence=ConfidenceTier.CONFIRMED,
                    content="moves=" + ",".join(move.move_name for move in moves[:6]),
                    retrieval_reason="sql_move_pool_lookup",
                )
            )
        evidence = ContextBuilder().build(facts=facts, mechanics=snippets)
        self._update_state_after_analysis(
            route,
            state,
            ToolTrace(species_display_name=profile.display_name, species_id=profile.species_id),
        )
        return AdvisorResponse(
            backend=self.backend,
            answer_summary=self._species_answer_summary(profile, moves, semantics, mechanism_matches),
            tool_results=tool_results,
            evidence_summary=evidence,
            confidence_notes=[
                "物种资料与技能池事实属于 confirmed，因为它们直接来自 SQLite battle-dex。",
                "定位判断仅是 provisional hypothesis；没有案例库和已选配招前，不应该把它当作唯一正确角色。",
                *(
                    [
                        "检测到机制词但 reviewed wiki 尚未完整覆盖全部相关页面，因此当前解释已按保守边界降级。"
                    ]
                    if any(not match.has_reviewed_page for match in mechanism_matches)
                    else []
                ),
            ],
            followup_options=_default_followups(
                route,
                ToolTrace(species_display_name=profile.display_name, species_id=profile.species_id),
            ),
        )

    def _help_response(self) -> AdvisorResponse:
        return self._simple_response(
            "可用命令：`/set-team`、`/show-team`、`/analyze`、`/species <名称>`、`/clear`、`/exit`。自然语言也支持队伍结构问题和已入库精灵查询。",
            followup_options=["/set-team 草 地 龙 翼 火 水", "/species 豆丁鱼", "分析这队联防"],
        )

    def _future_or_live_meta_refusal_response(self) -> AdvisorResponse:
        return self._simple_response(
            (
                "当前 MVP 没有 web/live 官方平衡公告 feed，也没有实时环境数据；"
                "因此不能预测未来加强/削弱、明天官方改动，或 live meta 变化。"
                " 我现在能做的是：分析当前队伍结构、查询 battle-dex 已入库事实，"
                "以及基于当前事实保守讨论某只精灵的 provisional 定位。"
            ),
            followup_options=["分析 草 地 龙 翼 火 水 这队联防", "/species 豆丁鱼", "豆丁鱼适合干什么"],
        )

    def _show_team_response(self, state: AdvisorSessionState) -> AdvisorResponse:
        slots = tuple(self._slots_from_state(state))
        if not slots:
            return self._simple_response(
                "当前会话里还没有队伍。",
                followup_options=["/set-team 草 地 龙 翼 火 水"],
            )
        return self._simple_response(
            f"当前队伍：{self._format_team(slots)}。",
            followup_options=["/analyze", "补洞方向是什么"],
        )

    def _simple_response(self, answer: str, *, followup_options: list[str]) -> AdvisorResponse:
        return AdvisorResponse(
            backend=self.backend,
            answer_summary=answer,
            tool_results=[],
            evidence_summary=[],
            confidence_notes=[],
            followup_options=followup_options,
        )

    def _slots_from_state(self, state: AdvisorSessionState) -> list[TeamSlot]:
        return [_team_slot_from_payload(slot_payload) for slot_payload in state.current_team]

    def _format_team(self, slots: tuple[TeamSlot, ...] | list[TeamSlot]) -> str:
        return " | ".join(
            f"{slot.slot_index}:{slot.primary_type}{'/' + slot.secondary_type if slot.secondary_type else ''}"
            for slot in slots
        )

    def _team_answer_summary(self, report: Any, guard: TeamSemanticGuard) -> str:
        return _team_answer_summary(report, guard)

    def _species_answer_summary(
        self,
        profile: Any,
        moves: list[Any],
        semantics: dict[str, Any],
        mechanism_matches: list[MechanismMatch],
    ) -> str:
        return _species_answer_summary(profile, moves, semantics, mechanism_matches)


def render_response(response: AdvisorResponse) -> str:
    lines = [
        "== Roco Advisor MVP ==",
        response.answer_summary,
    ]
    if response.tool_results:
        lines.append("")
        lines.append("== Tool Results ==")
        for tool_result in response.tool_results:
            lines.append(f"- {tool_result.tool_name} [{tool_result.status}]: {tool_result.summary}")
    if response.evidence_summary:
        lines.append("")
        lines.append("== Evidence ==")
        for item in _visible_evidence_items(response.evidence_summary):
            lines.append(
                f"- [{item.confidence}] {item.source_type}:{item.source_label} -> {item.content}"
            )
    if response.confidence_notes:
        lines.append("")
        lines.append("== Confidence Notes ==")
        for note in response.confidence_notes:
            lines.append(f"- {note}")
    if response.followup_options:
        lines.append("")
        lines.append("== Next ==")
        for option in response.followup_options:
            lines.append(f"- {option}")
    return "\n".join(lines)


def _visible_evidence_items(
    evidence_summary: list[AdvisorEvidenceItem],
    *,
    limit: int = 6,
) -> list[AdvisorEvidenceItem]:
    visible = list(evidence_summary[:limit])
    has_doc_available = any(item.source_type == SourceType.DOC for item in evidence_summary)
    has_doc_visible = any(item.source_type == SourceType.DOC for item in visible)
    if has_doc_available and not has_doc_visible and visible:
        first_doc = next(item for item in evidence_summary if item.source_type == SourceType.DOC)
        visible[-1] = first_doc
    return visible
