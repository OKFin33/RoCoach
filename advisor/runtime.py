from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from hashlib import sha256
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from enum import StrEnum
from time import monotonic
from typing import Any, Protocol
from uuid import uuid4

from battle_engine.contracts import TeamSlot, to_payload
from battle_engine.team_structure import TeamStructureAnalyzer
from reporting.contracts import ConfidenceTier

from advisor.contracts import (
    AdvisorEvidenceItem,
    AdvisorResponse,
    AdvisorSessionState,
    AdvisorTurnSummary,
    ClarificationState,
    ConfidenceFloor,
    ConversationActiveFocus,
    ConversationTopicPool,
    ConversationTopicRelation,
    ConversationTopicSpecies,
    AdvisorToolResult,
    DocContextSnippet,
    GroundingClaimSupport,
    GroundingEvidenceItem,
    GroundingIntent,
    GroundingMissingEvidence,
    GroundingPacket,
    GroundingSubject,
    GroundingToolCall,
    GroundingToolCallStatus,
    MissingEvidenceKind,
    MissingEvidenceSeverity,
    RuntimePath,
    SubjectResolutionStatus,
    TeamCoherenceVerdict,
    TeamSemanticGuard,
    SourceType,
    TopicFocusType,
    TopicPoolDelta,
    TopicSourceRecord,
    TopicSourceType,
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
    COUNTERPLAY = "counterplay"
    RELATION_QUERY = "relation_query"
    GENERAL_CHAT = "general_chat"
    EXIT = "exit"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class RouteDecision:
    intent: Intent
    tools: tuple[str, ...]
    team_slots: tuple[TeamSlot, ...] = ()
    species_query: str | None = None
    relation_anchor_query: str | None = None
    relation_partner_query: str | None = None
    relation_kind: str | None = None
    anchor_role_hint: str | None = None
    partner_role_hint: str | None = None
    raw_argument: str | None = None


@dataclass(frozen=True)
class AgentExecutionTrace:
    turn_id: str
    session_id: str
    plan_intent: str
    loop_iterations: int
    loop_actions: tuple[str, ...]
    stop_reason: str
    grounding_packet_status: str
    topic_pool_delta: dict[str, Any]
    answer_shape_checks: tuple[str, ...]
    final_grade: str
    runtime_path: str
    tool_calls: tuple[str, ...]
    retrieval_refs: tuple[str, ...]
    provider_timeout_seconds: float
    per_tool_timeout_seconds: float
    max_turn_timeout_seconds: float


class TraceRecorder(Protocol):
    def record(self, *, trace: AgentExecutionTrace) -> None: ...


class NullTraceRecorder:
    def record(self, *, trace: AgentExecutionTrace) -> None:
        return None


class LocalQATraceRecorder:
    def __init__(self, *, max_records: int = 200, ttl_seconds: float = 7 * 24 * 3600) -> None:
        self.max_records = max(1, max_records)
        self.ttl_seconds = max(1.0, ttl_seconds)
        self.records: list[tuple[float, AgentExecutionTrace]] = []

    def record(self, *, trace: AgentExecutionTrace) -> None:
        now = monotonic()
        cutoff = now - self.ttl_seconds
        self.records = [
            (created_at, item)
            for created_at, item in self.records
            if created_at >= cutoff
        ]
        self.records.append((now, trace))
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records :]

    def recent(self) -> list[AgentExecutionTrace]:
        return [item for _, item in self.records]


class NativeRuntimeTimeoutError(TimeoutError):
    pass


class ToolRuntimeTimeoutError(TimeoutError):
    pass


NATIVE_TERMINAL_RESPONSE_RESERVE = 1
RECENT_TURN_SUMMARY_LIMIT = 12
NATIVE_INSTRUCTION_SUMMARY_LIMIT = 6
DEFAULT_PER_TOOL_TIMEOUT_SECONDS = 8.0
DEFAULT_MAX_TURN_TIMEOUT_SECONDS = 60.0

CONTEXTUAL_FOLLOWUP_MARKERS = (
    "什么意思",
    "解释一下",
    "展开说",
    "继续",
    "那怎么打",
    "这是什么意思",
    "刚才",
    "你刚才",
)
COUNTERPLAY_MARKERS = ("反制", "怎么打", "针对", "处理", "碰到", "应对", "counter")
RELATION_MARKERS = ("配合", "搭配", "组合", "核心", "主c", "主C", "副c", "副C", "辅助")
NON_FINAL_FORM_MARKERS = (
    "未进化",
    "不进化",
    "一阶",
    "1阶",
    "低阶",
    "初始形态",
    "原始形态",
    "小形态",
    "本体",
    "就小",
)


def _role_hint_from_message(message: str, *, anchor: bool) -> str | None:
    lowered = message.lower()
    if "主c" in lowered:
        return "main_carry" if anchor else "support_or_lead"
    if "副c" in lowered:
        return "secondary_carry" if anchor else "support_or_lead"
    if "辅助" in message:
        return "support" if anchor else "core_partner"
    return None


def _requests_non_final_form(message: str) -> bool:
    return any(marker in message for marker in NON_FINAL_FORM_MARKERS)


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


def run_tool_call_with_timeout(tool_name: str, call, *, seconds: float) -> Any:
    try:
        return run_native_call_with_timeout(call, seconds=seconds)
    except NativeRuntimeTimeoutError as exc:
        raise ToolRuntimeTimeoutError(f"{tool_name} timeout after {seconds:.1f}s") from exc


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
        if "当前队伍" in stripped or "show team" in lowered:
            return RouteDecision(Intent.SHOW_TEAM, ())
        if self._wants_future_or_live_meta(stripped):
            return RouteDecision(Intent.GENERAL_CHAT, (), raw_argument="future_or_live_meta")

        extracted_team = self.team_parser.parse_team_text(stripped)
        if extracted_team:
            counterplay_subject = self._extract_species_query(stripped, state)
            if self._wants_counterplay(stripped) and counterplay_subject:
                return RouteDecision(
                    Intent.COUNTERPLAY,
                    (
                        "get_species_profile",
                        "get_species_available_moves",
                        "retrieve_doc_context",
                        "analyze_species_semantics",
                    ),
                    team_slots=extracted_team,
                    species_query=counterplay_subject,
                )
            if self._wants_team_analysis(stripped):
                return RouteDecision(
                    Intent.ANALYZE_TEAM,
                    ("analyze_team_structure", "retrieve_doc_context"),
                    team_slots=extracted_team,
                )
            return RouteDecision(Intent.SET_TEAM, (), team_slots=extracted_team)

        if state.current_team and self._references_current_team(stripped):
            return RouteDecision(
                Intent.ANALYZE_TEAM,
                ("analyze_team_structure", "retrieve_doc_context"),
            )

        if self._wants_team_analysis(stripped):
            return RouteDecision(
                Intent.ANALYZE_TEAM,
                ("analyze_team_structure", "retrieve_doc_context"),
            )

        if self._is_contextual_followup(stripped):
            relation_focus = self._latest_relation_focus(state)
            if relation_focus is not None:
                anchor, partner = relation_focus
                return RouteDecision(
                    Intent.RELATION_QUERY,
                    (
                        "get_species_profile",
                        "get_species_available_moves",
                        "retrieve_doc_context",
                        "analyze_species_semantics",
                    ),
                    species_query=anchor,
                    relation_anchor_query=anchor,
                    relation_partner_query=partner,
                    relation_kind="team_core_pairing",
                    raw_argument=stripped,
                )

        species_query = self._extract_species_query(stripped, state)
        if species_query:
            relation_anchor = self._relation_anchor_for_message(stripped, state, species_query)
            if relation_anchor:
                return RouteDecision(
                    Intent.RELATION_QUERY,
                    (
                        "get_species_profile",
                        "get_species_available_moves",
                        "retrieve_doc_context",
                        "analyze_species_semantics",
                    ),
                    species_query=relation_anchor,
                    relation_anchor_query=relation_anchor,
                    relation_partner_query=species_query,
                    relation_kind="team_core_pairing",
                    anchor_role_hint=_role_hint_from_message(stripped, anchor=False),
                    partner_role_hint=_role_hint_from_message(stripped, anchor=True),
                    raw_argument=stripped,
                )
            if self._wants_counterplay(stripped):
                return RouteDecision(
                    Intent.COUNTERPLAY,
                    (
                        "get_species_profile",
                        "get_species_available_moves",
                        "retrieve_doc_context",
                        "analyze_species_semantics",
                    ),
                    species_query=species_query,
                )
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

        if self._is_contextual_followup(stripped):
            followup_subject = self._latest_grounded_subject(state)
            if followup_subject:
                intent = Intent.COUNTERPLAY if self._wants_counterplay(stripped) else Intent.SPECIES_QUERY
                return RouteDecision(
                    intent,
                    (
                        "get_species_profile",
                        "get_species_available_moves",
                        "retrieve_doc_context",
                        "analyze_species_semantics",
                    ),
                    species_query=followup_subject,
                    raw_argument=stripped,
                )

        return RouteDecision(Intent.GENERAL_CHAT, ())

    def _relation_anchor_for_message(
        self,
        message: str,
        state: AdvisorSessionState,
        mentioned_species: str,
    ) -> str | None:
        if not any(marker in message for marker in RELATION_MARKERS):
            return None
        focus = state.conversation_topic_pool.active_focus
        anchor = focus.subject_display_names[-1] if focus.subject_display_names else None
        if not anchor:
            anchor = self._latest_grounded_subject(state)
        if not anchor or anchor == mentioned_species:
            return None
        return anchor

    def _latest_relation_focus(self, state: AdvisorSessionState) -> tuple[str, str] | None:
        focus = state.conversation_topic_pool.active_focus
        if focus.focus_type != "relation":
            return None
        if len(focus.subject_display_names) >= 2:
            return focus.subject_display_names[0], focus.subject_display_names[1]
        if not focus.from_species_id or not focus.to_species_id:
            return None
        names_by_id = {
            item.canonical_species_id: item.display_name
            for item in state.conversation_topic_pool.species
        }
        anchor = names_by_id.get(focus.from_species_id)
        partner = names_by_id.get(focus.to_species_id)
        if anchor and partner:
            return anchor, partner
        return None

    def _route_command(self, raw_command: str) -> RouteDecision:
        command, _, rest = raw_command.partition(" ")
        argument = rest.strip()
        if command == "/help":
            return RouteDecision(Intent.HELP, ())
        if command == "/clear" and not argument:
            return RouteDecision(Intent.CLEAR, ())
        if command == "/clear":
            return RouteDecision(Intent.GENERAL_CHAT, (), raw_argument=raw_command)
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
        keywords = ("分析", "联防", "洞", "补洞", "结构", "先手", "速度", "weakness", "analyze", "/analyze")
        lowered = message.lower()
        return any(keyword in lowered for keyword in keywords)

    def _references_current_team(self, message: str) -> bool:
        markers = ("这套队伍", "当前队伍", "这队", "队伍", "先手", "速度")
        lowered = message.lower()
        return any(marker in message or marker in lowered for marker in markers)

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

    def _wants_counterplay(self, message: str) -> bool:
        lowered = message.lower()
        return any(marker in lowered or marker in message for marker in COUNTERPLAY_MARKERS)

    def _is_contextual_followup(self, message: str) -> bool:
        return any(marker in message for marker in CONTEXTUAL_FOLLOWUP_MARKERS)

    def _latest_grounded_subject(self, state: AdvisorSessionState) -> str | None:
        topic_pool_subject = self._topic_pool_followup_subject(state)
        if topic_pool_subject:
            return topic_pool_subject
        if (
            state.conversation_topic_pool.species
            or state.conversation_topic_pool.relations
            or state.conversation_topic_pool.active_focus.focus_type != TopicFocusType.NONE
        ):
            return None
        return state.current_species_context

    def _topic_pool_followup_subject(self, state: AdvisorSessionState) -> str | None:
        pool = state.conversation_topic_pool
        focus = pool.active_focus
        if focus.focus_type == TopicFocusType.SINGLE_SPECIES and len(focus.subject_display_names) == 1:
            return focus.subject_display_names[0]
        if focus.focus_type == TopicFocusType.RELATION:
            return None
        if len(pool.species) == 1:
            return pool.species[0].display_name
        return None

    def is_future_or_live_meta_refusal(self, route: RouteDecision) -> bool:
        return route.intent == Intent.UNSUPPORTED and route.raw_argument == "future_or_live_meta"

    def _extract_species_query(self, message: str, state: AdvisorSessionState) -> str | None:
        if self.repository is None:
            if state.current_species_context and (
                any(pronoun in message for pronoun in ("它", "这只", "这个精灵"))
                or self._is_contextual_followup(message)
            ):
                return state.current_species_context
            return None

        explicit_species = self._extract_explicit_species_query(message)
        if explicit_species:
            return explicit_species
        if self._has_unresolved_explicit_species_candidate(message):
            return None

        contextual_subject = self._topic_pool_followup_subject(state)
        if contextual_subject and (
            any(pronoun in message for pronoun in ("它", "这只", "这个精灵"))
            or self._is_contextual_followup(message)
            or self._mentions_active_focus_move(message, state)
            or self._looks_like_active_focus_question(message)
        ):
            return contextual_subject

        return None

    def _extract_explicit_species_query(self, message: str) -> str | None:
        if self.repository is None:
            return None

        mentioned = self._find_species_name_mention(message)
        if mentioned:
            return mentioned

        for token in self._explicit_species_candidate_tokens(message):
            hits = self.repository.search_species(token, limit=3)
            if any(hit.species_id == token or hit.display_name == token or hit.initial_species_name == token for hit in hits):
                return self._battle_default_species_name(token, message)
        for token in self._explicit_species_candidate_tokens(message):
            hits = self.repository.search_species(token, limit=1)
            if hits:
                return self._battle_default_species_name(hits[0].display_name, message)
        return None

    def _has_unresolved_explicit_species_candidate(self, message: str) -> bool:
        if not any(marker in message for marker in ("我有", "一只", "名叫", "叫做")):
            return False
        return bool(self._explicit_species_candidate_tokens(message))

    def _explicit_species_candidate_tokens(self, message: str) -> tuple[str, ...]:
        normalized = message
        for marker in (
            "我有一只",
            "我有个",
            "这个精灵",
            "这只精灵",
            "这只",
            "它",
            "玩法",
            "有什么",
            "是什么",
            "什么",
            "怎么",
            "反制",
            "适合",
            "干什么",
            "定位",
            "角色",
            "招式",
            "怎么样",
            "在这队里",
            "更像",
            "还是",
            "配合",
            "主C",
            "主c",
            "的",
            "有",
        ):
            normalized = normalized.replace(marker, " ")
        raw_candidates = sorted(
            {token for token in re.findall(r"[A-Za-z0-9一-龥“”'_-]{2,}", normalized)},
            key=len,
            reverse=True,
        )
        candidates: list[str] = []
        for token in raw_candidates:
            candidates.append(token)
            if 3 <= len(token) <= 6 and re.fullmatch(r"[一-龥]+", token):
                candidates.extend(token[:index] + token[index + 1 :] for index in range(1, len(token) - 1))
        return tuple(dict.fromkeys(candidates))

    def _find_species_name_mention(self, message: str) -> str | None:
        if self.repository is None:
            return None
        for species_name in self.repository.iter_species_names():
            if species_name and species_name in message:
                return self._battle_default_species_name(species_name, message)
        return None

    def _battle_default_species_name(self, species_name: str, message: str) -> str:
        if self.repository is None or _requests_non_final_form(message):
            return species_name
        hits = self.repository.search_species(species_name, limit=12)
        if not hits:
            return species_name
        exact_profile = self.repository.get_species_profile(species_name)
        lineage = exact_profile.initial_species_name if exact_profile is not None else hits[0].initial_species_name
        final_candidates = []
        for hit in hits:
            profile = self.repository.get_species_profile(hit.species_id)
            if profile is None or profile.initial_species_name != lineage:
                continue
            if profile.evolution_stage == "最终形态":
                final_candidates.append(profile)
        if not final_candidates:
            return species_name
        final_candidates.sort(key=lambda item: (len(item.display_name), item.display_name))
        return final_candidates[0].display_name

    def _mentions_active_focus_move(self, message: str, state: AdvisorSessionState) -> bool:
        if self.repository is None:
            return False
        subject = self._topic_pool_followup_subject(state)
        if not subject:
            return False
        try:
            moves = self.repository.get_species_available_moves(subject, limit=32)
        except Exception:
            return False
        return any(move.move_name and move.move_name in message for move in moves)

    def _looks_like_active_focus_question(self, message: str) -> bool:
        if not any(marker in message for marker in ("吗", "？", "?", "不是", "能", "不能", "为什么")):
            return False
        return any(marker in message for marker in ("技能", "特性", "能力", "恢复", "回复", "吸血", "伤害", "输出", "玩法"))


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
    per_tool_timeout_seconds: float = DEFAULT_PER_TOOL_TIMEOUT_SECONDS


@dataclass
class GroundedLoopResult:
    response: AdvisorResponse
    packet: GroundingPacket
    packet_ok: bool
    packet_error: str | None
    iterations: int
    actions: tuple[str, ...]
    stop_reason: str


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
        interpretation = "它同时有输出和功能技入口，更像副C/功能位混合体，要靠队友给它创造进场机会"
    elif "breaker_pressure" in pressure_tags:
        interpretation = "它更像带进攻压力的输出位，但仍需要已选配招才能区分主C还是副C"
    elif "utility_access" in pressure_tags:
        ability_text = f"{getattr(profile, 'ability_name', '')} {getattr(profile, 'ability_effect_text', '')}"
        if "连击" in ability_text:
            interpretation = "它更像消耗/补刀位：利用受伤后的连击收益找反打窗口，别拿它无脑站场"
        else:
            interpretation = "它更像功能位或辅助位：用状态技制造节奏，再给核心输出创造进场机会"
    else:
        interpretation = "它的面板不支持无脑站场，优先按辅助消耗或后手补刀来用"

    return {
        "semantic_roles": pressure_tags,
        "summary_line": f"provisional_tags={','.join(pressure_tags) or 'none'}",
        "interpretation": interpretation,
        "status_move_count": len(status_moves),
        "attack_move_count": len(attack_moves),
        "high_power_move_count": len(high_power_moves),
    }


def _public_species_semantics_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "role_read": payload.get("interpretation") or "按当前资料给出保守打法判断。",
        "status_move_count": payload.get("status_move_count", 0),
        "attack_move_count": payload.get("attack_move_count", 0),
        "high_power_move_count": payload.get("high_power_move_count", 0),
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
    candidates = (
        deps.route.species_query,
        species_key,
        deps.trace.species_display_name,
        deps.state.current_species_context,
    )
    for candidate in candidates:
        normalized = _normalize_species_tool_argument(candidate)
        if normalized:
            return normalized
    return None


def _normalize_species_tool_argument(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().strip("`'\"“”‘’")
    normalized = re.sub(r"^[#：:、，,。？?！!\\s]+|[#：:、，,。？?！!\\s]+$", "", normalized)
    return normalized or None


def _is_species_not_found_result(result: AdvisorToolResult) -> bool:
    if result.tool_name != "get_species_profile" or result.status != ToolStatus.REFUSED:
        return False
    if not result.payload:
        return False
    error = result.payload.get("error")
    return isinstance(error, str) and error.startswith("species_not_found:")


def _tool_timeout_result(response: AdvisorResponse) -> AdvisorToolResult | None:
    for result in response.tool_results:
        if result.status == ToolStatus.FAILED and (result.payload or {}).get("error") == "tool_timeout":
            return result
    return None


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


def _team_slot_context_line(slot: TeamSlot) -> str:
    parts = [
        f"slot {slot.slot_index}",
        f"name={slot.nickname or slot.species_key or 'unknown'}",
        f"type={slot.primary_type}/{slot.secondary_type or '-'}",
    ]
    if slot.selected_ability:
        parts.append(f"ability={slot.selected_ability}")
    if slot.selected_moves:
        parts.append("moves=" + ",".join(slot.selected_moves))
    if slot.nature_label:
        parts.append(f"nature={slot.nature_label}")
    if slot.individual_value_bonuses:
        iv_parts = [
            f"{bonus.get('stat')}={bonus.get('value')}"
            for bonus in slot.individual_value_bonuses
        ]
        parts.append("iv_bonus=" + ",".join(iv_parts))
    if slot.base_stats:
        parts.append(
            "base_stats="
            + ",".join(
                f"{key}:{slot.base_stats[key]}"
                for key in ("hp", "atk", "defense", "spa", "spd", "spe")
                if key in slot.base_stats
            )
        )
    return " ".join(parts)


def _team_member_intro(slots: tuple[TeamSlot, ...] | list[TeamSlot]) -> str:
    names = [
        slot.nickname or slot.species_key
        for slot in slots
        if slot.nickname or slot.species_key
    ]
    return "、".join(str(name) for name in names)


def _ensure_general_chat_confidence_note(response: AdvisorResponse, route: RouteDecision) -> AdvisorResponse:
    if route.intent != Intent.GENERAL_CHAT or response.tool_results:
        return response

    note = (
        "本轮是 general_chat 自然语言回复，未调用事实工具；涉及精灵、技能、机制或队伍结论时应继续追问或调用 approved tools。"
    )
    if note in response.confidence_notes:
        return response

    updated = response.model_copy(deep=True)
    updated.confidence_notes.append(note)
    if not updated.followup_options:
        updated.followup_options = _default_followups(route, ToolTrace())
    return updated


def _native_output_mode_for_config(native_model: Any | None) -> str:
    if isinstance(native_model, RocoNativeModelConfig):
        marker = f"{native_model.model_name} {native_model.base_url}".casefold()
        if "deepseek" in marker:
            return "prompted"
    return "tool"


def _native_model_settings_for_config(native_model: Any | None) -> dict[str, Any] | None:
    if not isinstance(native_model, RocoNativeModelConfig):
        return None

    marker = f"{native_model.model_name} {native_model.base_url}".casefold()
    if "deepseek" not in marker:
        return None

    try:
        from pydantic_ai.models.openai import OpenAIModelSettings
    except ModuleNotFoundError:
        return None

    if native_model.reasoning_mode == "enabled":
        settings: dict[str, Any] = {"extra_body": {"thinking": {"type": "enabled"}}}
        if native_model.reasoning_effort:
            settings["openai_reasoning_effort"] = native_model.reasoning_effort
        return OpenAIModelSettings(**settings)

    return OpenAIModelSettings(extra_body={"thinking": {"type": "disabled"}})


def _native_usage_limits_for_route(route: RouteDecision) -> Any | None:
    try:
        from pydantic_ai import UsageLimits
    except ModuleNotFoundError:
        return None

    if route.intent == Intent.GENERAL_CHAT:
        return UsageLimits(request_limit=2, tool_calls_limit=0)
    if route.intent == Intent.ANALYZE_TEAM:
        return UsageLimits(
            request_limit=3,
            tool_calls_limit=max(len(route.tools), 1),
        )
    if route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY}:
        return UsageLimits(
            request_limit=3,
            tool_calls_limit=max(len(route.tools), 1),
        )
    return UsageLimits(request_limit=2, tool_calls_limit=0)


def _is_native_usage_limit_error(exc: Exception) -> bool:
    try:
        from pydantic_ai.usage import UsageLimitExceeded
    except ModuleNotFoundError:
        return False
    return isinstance(exc, UsageLimitExceeded)


def _native_runtime_fingerprint(native_model: Any | None) -> str | None:
    if not isinstance(native_model, RocoNativeModelConfig):
        return None
    base_url_hash = sha256(native_model.base_url.encode("utf-8")).hexdigest()[:16]
    return "|".join(
        (
            "roco_session_state.v2",
            "pydantic_ai_model_messages.v1",
            "runtime=pydantic_ai_native",
            "provider=openai_compatible",
            native_model.model_name,
            base_url_hash,
            native_model.reasoning_mode,
            native_model.reasoning_effort or "none",
        )
    )


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
    timeout_seconds: float = DEFAULT_PER_TOOL_TIMEOUT_SECONDS,
) -> tuple[list[DocContextSnippet], list[MechanismMatch]]:
    def retrieve() -> tuple[list[DocContextSnippet], list[MechanismMatch]]:
        mechanism_matches = retriever.inspect_mechanisms(query=query, evidence_texts=evidence_texts)
        snippets = retriever.retrieve(
            query=query,
            analysis_type=analysis_type,
            limit=limit,
            evidence_texts=evidence_texts,
        )
        return snippets, mechanism_matches

    try:
        return run_native_call_with_timeout(retrieve, seconds=timeout_seconds)
    except NativeRuntimeTimeoutError:
        return [], []


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


def _team_answer_summary(
    report: Any,
    guard: TeamSemanticGuard,
    slots: tuple[TeamSlot, ...] | list[TeamSlot] = (),
) -> str:
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
    speed_line = _team_speed_line(slots)
    if speed_line:
        fragments.append(speed_line)
    if guard.counterevidence:
        fragments.append(f"当前最关键的反证是：{guard.counterevidence[0]}。")
    member_intro = _team_member_intro(slots)
    if member_intro:
        fragments.insert(0, f"已读取队伍成员：{member_intro}。")
    return " ".join(fragments)


def _species_answer_summary(
    profile: Any,
    moves: list[Any],
    semantics: dict[str, Any],
    mechanism_matches: list[MechanismMatch],
) -> str:
    move_names = ", ".join(move.move_name for move in moves[:5]) if moves else "暂无已解析技能"
    ability_line = f"特性「{profile.ability_name}」" if getattr(profile, "ability_name", None) else "特性信息不完整"
    summary = (
        f"先按对战默认形态看：{profile.display_name} 是{profile.primary_type}"
        f"{('/' + profile.secondary_type) if profile.secondary_type else ''}系，"
        f"种族值 {profile.base_stats.bst}，{ability_line}。"
        f" 已看到的关键技能有 {move_names}。"
        f" 结论：{semantics['interpretation']}。"
    )
    resolved, missing = _split_mechanism_matches(mechanism_matches)
    if resolved:
        summary += " 这里要注意 " + "、".join(f"「{match.token}」" for match in resolved[:3]) + " 的触发节奏。"
    if missing:
        summary += (
            " 有些机制细节还不能说死，所以别把它当成固定套路；实战要看配招和队友保护。"
        )
    return summary


def _counterplay_answer_summary(
    profile: Any,
    moves: list[Any],
    semantics: dict[str, Any],
    mechanism_matches: list[MechanismMatch],
) -> str:
    base = _species_answer_summary(profile, moves, semantics, mechanism_matches)
    attack_moves = [
        move.move_name
        for move in moves
        if getattr(move, "category_raw", None) in {"物攻", "魔攻"}
    ][:4]
    utility_moves = [
        move.move_name
        for move in moves
        if getattr(move, "category_raw", None) == "状态"
    ][:4]
    axes = [
        "先确认它实际携带的技能，因为当前只能用已入库技能池做保守判断",
        "围绕速度/先手权做交换，避免让它免费进入最舒服的输出或功能节奏",
    ]
    if attack_moves:
        axes.append("对它的进攻技能池做换入预案：" + "、".join(attack_moves))
    if utility_moves:
        axes.append("注意它可能通过功能技制造回合差：" + "、".join(utility_moves))
    return (
        f"反制 {profile.display_name} 的核心不是背规则，而是先把它当作一个有条件威胁来拆。"
        f" {base} 可执行的处理轴是："
        + "；".join(axes)
        + "。如果你给我当前队伍，我可以把这些轴落到具体换入和牺牲顺序。"
    )


def _team_speed_line(slots: tuple[TeamSlot, ...] | list[TeamSlot]) -> str | None:
    speed_parts: list[str] = []
    for slot in slots:
        if not slot.base_stats:
            continue
        spe = slot.base_stats.get("spe")
        if isinstance(spe, int):
            speed_parts.append(f"{slot.nickname or slot.species_key or slot.slot_index}:速度{spe}")
    if not speed_parts:
        return None
    return "已读取速度线：" + "，".join(speed_parts) + "。"


_NATIVE_AGENTS: dict[str, Any] = {}


def _build_native_agent(output_mode: str = "tool") -> Any:
    if output_mode in _NATIVE_AGENTS:
        return _NATIVE_AGENTS[output_mode]

    try:
        from pydantic_ai import Agent, ModelRetry, RunContext
        from pydantic_ai.output import PromptedOutput
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "pydantic_ai is not installed in the active interpreter. "
            "Use the project .venv or install `pydantic-ai-slim[openai]`."
        ) from exc

    output_type: Any = PromptedOutput(AdvisorResponse) if output_mode == "prompted" else AdvisorResponse
    agent = Agent(
        output_type=output_type,
        deps_type=NativeAdvisorDeps,
        system_prompt=(
            "Answer through the selected public persona. "
            "Do not introduce yourself, name the app, or state a job title unless the user explicitly asks who you are. "
            "Treat battle-advice role as task context, not self-identity. "
            "Use the project vocabulary: 精灵, 队伍, 技能. Never call its species Pokémon, 宝可梦, or Pokemon. "
            "Use approved tools, ground confirmed claims only in deterministic engine or SQL facts, "
            "and express uncertainty as natural coaching copy, not backend labels. "
            "Do not proactively mention cultivation, breeding, leveling, training, resource planning, or general progression features "
            "unless the user explicitly asks and grounded data exists. "
            "Do not invent tool results or evidence. "
            "Focus your output on answer_summary, confidence_notes, and followup_options. "
            "Never put internal words like provisional, reviewed, D-layer, grounding packet, runtime_path, or semantic tags in answer_summary."
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

        try:
            report = run_tool_call_with_timeout(
                "analyze_team_structure",
                lambda: ctx.deps.analyzer.analyze(slots),
                seconds=ctx.deps.per_tool_timeout_seconds,
            )
        except ToolRuntimeTimeoutError as exc:
            payload = {"error": "tool_timeout"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="analyze_team_structure",
                    status=ToolStatus.FAILED,
                    summary=str(exc),
                    payload=payload,
                )
            )
            return payload
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

        try:
            profile = run_tool_call_with_timeout(
                "get_species_profile",
                lambda: ctx.deps.repository.get_species_profile(query),
                seconds=ctx.deps.per_tool_timeout_seconds,
            )
        except ToolRuntimeTimeoutError as exc:
            payload = {"error": "tool_timeout"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="get_species_profile",
                    status=ToolStatus.FAILED,
                    summary=str(exc),
                    payload=payload,
                )
            )
            return payload
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
            ability = run_tool_call_with_timeout(
                "get_ability_detail",
                lambda: ctx.deps.repository.get_ability_detail(profile.ability_name),
                seconds=ctx.deps.per_tool_timeout_seconds,
            )
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

        try:
            moves = run_tool_call_with_timeout(
                "get_species_available_moves",
                lambda: ctx.deps.repository.get_species_available_moves(query, limit=limit),
                seconds=ctx.deps.per_tool_timeout_seconds,
            )
        except ToolRuntimeTimeoutError as exc:
            payload = {"moves": [], "error": "tool_timeout"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="get_species_available_moves",
                    status=ToolStatus.FAILED,
                    summary=str(exc),
                    payload=payload,
                )
            )
            return payload
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
            timeout_seconds=ctx.deps.per_tool_timeout_seconds,
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
        """Produce a bounded species-role interpretation from approved facts."""
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

        try:
            profile = run_tool_call_with_timeout(
                "analyze_species_semantics.get_species_profile",
                lambda: ctx.deps.repository.get_species_profile(query),
                seconds=ctx.deps.per_tool_timeout_seconds,
            )
        except ToolRuntimeTimeoutError as exc:
            payload = {"error": "tool_timeout"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="analyze_species_semantics",
                    status=ToolStatus.FAILED,
                    summary=str(exc),
                    payload=payload,
                )
            )
            return payload
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

        try:
            moves = run_tool_call_with_timeout(
                "analyze_species_semantics.get_species_available_moves",
                lambda: ctx.deps.repository.get_species_available_moves(profile.species_id, limit=10),
                seconds=ctx.deps.per_tool_timeout_seconds,
            )
        except ToolRuntimeTimeoutError as exc:
            payload = {"error": "tool_timeout"}
            ctx.deps.trace.add_tool_result(
                AdvisorToolResult(
                    tool_name="analyze_species_semantics",
                    status=ToolStatus.FAILED,
                    summary=str(exc),
                    payload=payload,
                )
            )
            return payload
        payload = _analyze_species_semantics_payload(profile, moves)
        public_payload = _public_species_semantics_payload(payload)
        ctx.deps.trace.species_semantics = payload
        ctx.deps.trace.add_tool_result(
            AdvisorToolResult(
                tool_name="analyze_species_semantics",
                summary=public_payload["role_read"],
                payload=public_payload,
            )
        )
        return public_payload

    @agent.output_validator
    def validate_output(ctx: RunContext[NativeAdvisorDeps], output: AdvisorResponse) -> AdvisorResponse:
        merged = output.model_copy(deep=True)
        merged.backend = "pydantic_ai_native"
        merged.runtime_path = RuntimePath.NATIVE_LLM_TERMINAL
        merged.tool_results = list(ctx.deps.trace.tool_results)
        merged.evidence_summary = list(ctx.deps.trace.evidence_summary)
        merged.answer_summary = merged.answer_summary.strip()

        if not merged.answer_summary:
            raise ModelRetry("answer_summary must not be empty")
        shape_error = _answer_shape_violation(merged.answer_summary)
        if shape_error:
            raise ModelRetry(f"answer_summary contains forbidden internal wording: {shape_error}")

        if ctx.deps.route.intent == Intent.ANALYZE_TEAM and not any(
            result.tool_name == "analyze_team_structure" and result.status == ToolStatus.OK
            for result in merged.tool_results
        ):
            timeout_result = next(
                (
                    result
                    for result in merged.tool_results
                    if result.tool_name == "analyze_team_structure"
                    and result.status == ToolStatus.FAILED
                    and (result.payload or {}).get("error") == "tool_timeout"
                ),
                None,
            )
            if timeout_result is not None:
                merged.answer_summary = (
                    "本轮有本地工具调用超过预算，已停止继续分析。请缩小问题范围，或稍后重试。"
                )
                merged.evidence_summary = []
                merged.confidence_notes.insert(0, f"tool_timeout: {timeout_result.summary}")
                return merged
            no_team_result = next(
                (
                    result
                    for result in merged.tool_results
                    if result.tool_name == "analyze_team_structure"
                    and result.status == ToolStatus.REFUSED
                    and (result.payload or {}).get("error") == "no_team_in_session"
                ),
                None,
            )
            if no_team_result is None:
                raise ModelRetry("team analysis must call analyze_team_structure")
            merged.answer_summary = (
                "我还没有拿到可分析的队伍。先给我 2-6 个队伍槽位、想保留的核心精灵，"
                "或等 P8 队伍设置接入后从结构化队伍上下文读取。"
            )
            merged.evidence_summary = []
            if not merged.followup_options:
                merged.followup_options = [
                    "告诉我当前队伍有哪些精灵",
                    "先按属性写：草 地 龙 翼 火 水",
                    "说明你想优化输出、联防还是先手节奏",
                ]
            if not any("missing_team_context" in note for note in merged.confidence_notes):
                merged.confidence_notes.insert(
                    0,
                    "missing_team_context: 未获得队伍上下文，不能声称已经完成队伍结构分析。",
                )

        if ctx.deps.route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY}:
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
            merged.answer_summary = _team_answer_summary(
                ctx.deps.trace.team_structure_report,
                guard,
                _resolve_team_slots(ctx.deps.route, ctx.deps.state),
            )
            if not any("unknown-quality" in note.lower() for note in merged.confidence_notes):
                merged.confidence_notes.insert(
                    0,
                    "队伍输入默认视为 unknown-quality team；当前分析是在检验它是否自洽，而不是默认它已经有成熟计划。",
                )

        if (
            ctx.deps.route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY}
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
                    "检测到机制词但没有匹配的机制证据，因此当前输出已强制降级为保守描述。",
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
            if ctx.deps.route.intent == Intent.COUNTERPLAY:
                merged.answer_summary = _counterplay_answer_summary(
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

        if ctx.deps.route.intent == Intent.GENERAL_CHAT and not merged.tool_results:
            note = (
                "本轮是 general_chat 自然语言回复，未调用事实工具；涉及精灵、技能、机制或队伍结论时应继续追问或调用 approved tools。"
            )
            if note not in merged.confidence_notes:
                merged.confidence_notes.append(note)

        if ctx.deps.route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY} and not any(
            "provisional" in note.lower() for note in merged.confidence_notes
        ):
            merged.confidence_notes.append(
                "物种定位判断基于当前可用信息；用户侧回答应保留战术边界但避免暴露内部置信标签。"
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

    _NATIVE_AGENTS[output_mode] = agent
    return agent


def _default_followups(route: RouteDecision, trace: ToolTrace) -> list[str]:
    if route.intent == Intent.ANALYZE_TEAM:
        return [
            "继续问：这队补洞方向是什么",
            "继续问：如果把 3 号位换成火系会怎样",
            "继续问：某只精灵在这队里更像什么定位",
        ]
    if route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY}:
        species_name = trace.species_display_name or route.species_query or "这只精灵"
        if route.intent == Intent.COUNTERPLAY:
            return [
                f"继续问：{species_name} 为什么难处理",
                f"继续问：我这队怎么打 {species_name}",
                "继续问：分析这队联防",
            ]
        return [
            f"继续问：{species_name} 在这队里更像主C还是辅助",
            f"继续问：{species_name} 常见可用技能有哪些",
            "继续问：分析这队联防",
        ]
    if route.intent == Intent.GENERAL_CHAT:
        return [
            "继续问：分析这队联防",
            "继续问：查询某只精灵的定位",
            "继续问：我应该补充哪些队伍信息",
        ]
    return ["/help"]


def _format_recent_turn_summaries(state: AdvisorSessionState) -> str:
    summaries = state.recent_turn_summaries[-NATIVE_INSTRUCTION_SUMMARY_LIMIT:]
    if not summaries:
        return "none"
    parts: list[str] = []
    for summary in summaries:
        subject = summary.resolved_subject or "none"
        tools = ",".join(summary.tool_names) if summary.tool_names else "none"
        refs = ",".join(summary.grounding_refs[:4]) if summary.grounding_refs else "none"
        excerpt = summary.user_message_excerpt or summary.user_message
        parts.append(
            (
                f"[{summary.route_intent}] user_excerpt={excerpt!r}; "
                f"user_digest={summary.user_message_digest or 'none'}; "
                f"subject={subject}; digest={summary.answer_digest!r}; "
                f"tools={tools}; refs={refs}"
            )
        )
    return " || ".join(parts)


def _format_topic_pool(pool: ConversationTopicPool) -> str:
    species = ", ".join(
        f"{item.display_name}<{item.canonical_species_id}> roles={','.join(item.role_hints) or 'none'}"
        for item in pool.species[-8:]
    ) or "none"
    relations = ", ".join(
        f"{item.from_species_id}->{item.to_species_id}:{item.relation_kind}"
        for item in pool.relations[-6:]
    ) or "none"
    focus = pool.active_focus.model_dump_json(exclude_none=True)
    return f"species=[{species}] relations=[{relations}] active_focus={focus}"


def _resolved_turn_subject(
    route: RouteDecision,
    response: AdvisorResponse,
    state: AdvisorSessionState,
) -> str | None:
    if route.species_query:
        return route.species_query
    for item in response.evidence_summary:
        if item.source_label.startswith("species_form:"):
            content_name = item.content.split(":", 1)[0].strip()
            if content_name:
                return content_name
    return state.current_species_context


def _compact_text(value: str, *, limit: int) -> str:
    normalized = re.sub(r"\s+", " ", _redact_summary_text(value)).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 1)].rstrip() + "…"


def _redact_summary_text(value: str) -> str:
    redacted = re.sub(r"p4b-secret-[A-Za-z0-9_-]+", "[redacted-secret]", value)
    redacted = re.sub(r"(?i)(api[_-]?key|provider[_-]?key)\s*[:=]\s*\S+", r"\1=[redacted-secret]", redacted)
    redacted = re.sub(r"\b1[3-9]\d{9}\b", "[redacted-phone]", redacted)
    redacted = re.sub(r"https?://[^\s]+", "[redacted-url]", redacted)
    return redacted


def _text_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()[:16]


def _compact_unique(values: list[str], *, limit: int) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
        if len(result) >= limit:
            break
    return result


def _species_refs_from_response(response: AdvisorResponse) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for item in response.evidence_summary:
        if not item.source_label.startswith("species_form:"):
            continue
        species_id = item.source_label.split(":", 1)[1].strip()
        display_name = item.content.split(":", 1)[0].strip() or species_id
        if species_id and (species_id, display_name) not in refs:
            refs.append((species_id, display_name))
    return refs


def _source_record(
    *,
    source_type: TopicSourceType,
    turn_id: str,
    created_at: str,
    confidence: float,
) -> TopicSourceRecord:
    return TopicSourceRecord(
        source_type=source_type,
        turn_id=turn_id,
        confidence=confidence,
        created_at=created_at,
        updated_at=created_at,
    )


def _merge_source_record(
    records: list[TopicSourceRecord],
    record: TopicSourceRecord,
) -> list[TopicSourceRecord]:
    merged = list(records)
    for index, existing in enumerate(merged):
        if existing.source_type == record.source_type and existing.turn_id == record.turn_id:
            merged[index] = record
            return merged
    merged.append(record)
    return merged[-6:]


def _upsert_topic_species(
    pool: ConversationTopicPool,
    *,
    species_id: str,
    display_name: str,
    source_type: TopicSourceType,
    turn_id: str,
    created_at: str,
    role_hint: str | None = None,
) -> None:
    record = _source_record(
        source_type=source_type,
        turn_id=turn_id,
        created_at=created_at,
        confidence=0.85 if source_type == TopicSourceType.TOOL_RESOLUTION else 0.65,
    )
    for index, item in enumerate(pool.species):
        if item.canonical_species_id != species_id:
            continue
        role_hints = list(item.role_hints)
        if role_hint and role_hint not in role_hints:
            role_hints.append(role_hint)
        pool.species[index] = item.model_copy(
            update={
                "display_name": display_name,
                "canonical_name": item.canonical_name or display_name,
                "aliases": _compact_unique([*item.aliases, display_name], limit=8),
                "role_hints": role_hints[-6:],
                "source_records": _merge_source_record(item.source_records, record),
                "mention_count": item.mention_count + 1,
                "confidence": max(item.confidence, record.confidence),
                "last_mentioned_at": created_at,
            },
            deep=True,
        )
        return
    pool.species.append(
        ConversationTopicSpecies(
            canonical_species_id=species_id,
            display_name=display_name,
            canonical_name=display_name,
            aliases=[display_name],
            role_hints=[role_hint] if role_hint else [],
            source_records=[record],
            confidence=record.confidence,
            last_mentioned_at=created_at,
        )
    )


def _relation_edge_id(from_species_id: str, to_species_id: str, relation_kind: str) -> str:
    digest = sha256(f"{from_species_id}>{to_species_id}:{relation_kind}".encode("utf-8")).hexdigest()[:12]
    return f"rel_{digest}"


def _upsert_topic_relation(
    pool: ConversationTopicPool,
    *,
    from_species_id: str,
    to_species_id: str,
    relation_kind: str,
    from_role_hint: str | None,
    to_role_hint: str | None,
    turn_id: str,
    created_at: str,
) -> ConversationTopicRelation:
    edge_id = _relation_edge_id(from_species_id, to_species_id, relation_kind)
    record = _source_record(
        source_type=TopicSourceType.USER_MENTION,
        turn_id=turn_id,
        created_at=created_at,
        confidence=0.7,
    )
    for index, item in enumerate(pool.relations):
        if item.relation_edge_id != edge_id:
            continue
        updated = item.model_copy(
            update={
                "from_role_hint": from_role_hint or item.from_role_hint,
                "to_role_hint": to_role_hint or item.to_role_hint,
                "source_records": _merge_source_record(item.source_records, record),
                "mention_count": item.mention_count + 1,
                "confidence": max(item.confidence, record.confidence),
                "last_mentioned_at": created_at,
            },
            deep=True,
        )
        pool.relations[index] = updated
        return updated
    relation = ConversationTopicRelation(
        relation_edge_id=edge_id,
        from_species_id=from_species_id,
        to_species_id=to_species_id,
        relation_kind=relation_kind,
        from_role_hint=from_role_hint,
        to_role_hint=to_role_hint,
        source_records=[record],
        confidence=record.confidence,
        last_mentioned_at=created_at,
    )
    pool.relations.append(relation)
    return relation


def _bounded_topic_pool(pool: ConversationTopicPool, *, max_species: int = 16, max_relations: int = 24) -> ConversationTopicPool:
    active_ids = set(pool.active_focus.subject_species_ids)
    species = sorted(
        pool.species,
        key=lambda item: (
            item.canonical_species_id in active_ids,
            item.last_mentioned_at,
            item.confidence,
            item.mention_count,
        ),
        reverse=True,
    )[:max_species]
    species_ids = {item.canonical_species_id for item in species}
    relations = [
        relation
        for relation in sorted(
            pool.relations,
            key=lambda item: (item.relation_edge_id == pool.active_focus.relation_edge_id, item.last_mentioned_at, item.confidence),
            reverse=True,
        )
        if relation.from_species_id in species_ids and relation.to_species_id in species_ids
    ][:max_relations]
    return pool.model_copy(update={"species": species, "relations": relations}, deep=True)


def _update_topic_pool(
    pool: ConversationTopicPool,
    *,
    route: RouteDecision,
    response: AdvisorResponse,
    turn_id: str,
    created_at: str,
) -> ConversationTopicPool:
    updated = pool.model_copy(deep=True)
    refs = _species_refs_from_response(response)
    if route.intent == Intent.RELATION_QUERY and len(refs) >= 2:
        anchor_id, anchor_name = refs[0]
        partner_id, partner_name = refs[1]
        _upsert_topic_species(
            updated,
            species_id=anchor_id,
            display_name=anchor_name,
            source_type=TopicSourceType.TOOL_RESOLUTION,
            turn_id=turn_id,
            created_at=created_at,
            role_hint=route.anchor_role_hint,
        )
        _upsert_topic_species(
            updated,
            species_id=partner_id,
            display_name=partner_name,
            source_type=TopicSourceType.TOOL_RESOLUTION,
            turn_id=turn_id,
            created_at=created_at,
            role_hint=route.partner_role_hint,
        )
        relation = _upsert_topic_relation(
            updated,
            from_species_id=anchor_id,
            to_species_id=partner_id,
            relation_kind=route.relation_kind or "related",
            from_role_hint=route.anchor_role_hint,
            to_role_hint=route.partner_role_hint,
            turn_id=turn_id,
            created_at=created_at,
        )
        updated.active_focus = ConversationActiveFocus(
            focus_type=TopicFocusType.RELATION,
            subject_species_ids=[anchor_id, partner_id],
            subject_display_names=[anchor_name, partner_name],
            relation_edge_id=relation.relation_edge_id,
            from_species_id=anchor_id,
            to_species_id=partner_id,
            from_role_hint=route.anchor_role_hint,
            to_role_hint=route.partner_role_hint,
            anchor_turn_id=updated.active_focus.anchor_turn_id or turn_id,
            updated_turn_id=turn_id,
            confidence=relation.confidence,
        )
        return _bounded_topic_pool(updated)

    for species_id, display_name in refs:
        _upsert_topic_species(
            updated,
            species_id=species_id,
            display_name=display_name,
            source_type=TopicSourceType.TOOL_RESOLUTION,
            turn_id=turn_id,
            created_at=created_at,
        )
    if refs:
        species_id, display_name = refs[-1]
        updated.active_focus = ConversationActiveFocus(
            focus_type=TopicFocusType.SINGLE_SPECIES,
            subject_species_ids=[species_id],
            subject_display_names=[display_name],
            anchor_turn_id=turn_id,
            updated_turn_id=turn_id,
            confidence=0.85,
        )
    return _bounded_topic_pool(updated)


def _grounding_intent_for_route(route: RouteDecision) -> GroundingIntent:
    if route.intent == Intent.ANALYZE_TEAM:
        return GroundingIntent.TEAM_ANALYSIS
    if route.intent == Intent.COUNTERPLAY:
        return GroundingIntent.COUNTERPLAY
    if route.intent == Intent.RELATION_QUERY:
        return GroundingIntent.RELATION_QUERY
    if route.intent == Intent.SPECIES_QUERY:
        return GroundingIntent.SPECIES_QUERY
    if route.intent == Intent.GENERAL_CHAT:
        return GroundingIntent.GENERAL_CHAT
    return GroundingIntent.STATIC_CONTROL


def _evidence_id_for(index: int, item: AdvisorEvidenceItem) -> str:
    digest = sha256(
        f"{item.source_type}:{item.source_label}:{item.retrieval_reason}:{item.content}".encode("utf-8")
    ).hexdigest()[:12]
    return f"ev_{index:03d}_{digest}"


def _packet_evidence_items(response: AdvisorResponse) -> tuple[list[GroundingEvidenceItem], dict[str, str]]:
    items: list[GroundingEvidenceItem] = []
    by_label: dict[str, str] = {}
    for index, evidence in enumerate(response.evidence_summary, start=1):
        evidence_id = _evidence_id_for(index, evidence)
        items.append(
            GroundingEvidenceItem(
                evidence_id=evidence_id,
                source_type=SourceType(str(evidence.source_type)),
                source_label=evidence.source_label,
                content_digest=_text_digest(evidence.content),
                confidence=evidence.confidence,
            )
        )
        by_label.setdefault(evidence.source_label, evidence_id)
    return items, by_label


def _required_tools_for_intent(intent: Intent) -> set[str]:
    if intent == Intent.ANALYZE_TEAM:
        return {"analyze_team_structure", "retrieve_doc_context"}
    if intent == Intent.RELATION_QUERY:
        return {
            "get_species_profile",
            "get_species_available_moves",
            "retrieve_doc_context",
            "analyze_species_semantics",
        }
    if intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY}:
        return {
            "get_species_profile",
            "get_species_available_moves",
            "retrieve_doc_context",
            "analyze_species_semantics",
        }
    return set()


def _tool_evidence_ids(tool_name: str, evidence_by_label: dict[str, str]) -> list[str]:
    if tool_name == "retrieve_doc_context":
        return [evidence_id for label, evidence_id in evidence_by_label.items() if label.startswith("specs/") or label.startswith("wiki/")]
    if tool_name == "get_species_profile":
        return [evidence_id for label, evidence_id in evidence_by_label.items() if label.startswith("species_form:")]
    if tool_name == "get_species_available_moves":
        return [evidence_id for label, evidence_id in evidence_by_label.items() if label.startswith("species_move_pool:")]
    if tool_name == "analyze_team_structure":
        return [evidence_id for label, evidence_id in evidence_by_label.items() if label == "battle_engine.team_structure"]
    if tool_name == "analyze_species_semantics":
        return [evidence_id for label, evidence_id in evidence_by_label.items() if label.startswith("species_form:") or label.startswith("species_move_pool:")]
    return []


def _build_grounding_packet(route: RouteDecision, response: AdvisorResponse) -> GroundingPacket:
    species_refs = _species_refs_from_response(response)
    evidence_items, evidence_by_label = _packet_evidence_items(response)
    subjects = [
        GroundingSubject(
            canonical_species_id=species_id,
            display_name=display_name,
            resolution_status=SubjectResolutionStatus.RESOLVED,
            role_hint=route.anchor_role_hint if index == 0 else route.partner_role_hint,
        )
        for index, (species_id, display_name) in enumerate(species_refs)
    ]
    if not subjects and route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY}:
        subjects.append(
            GroundingSubject(
                display_name=route.species_query or route.relation_anchor_query,
                resolution_status=SubjectResolutionStatus.MISSING,
            )
        )
    tool_calls = [
        GroundingToolCall(
            tool_name=tool.tool_name,
            status=GroundingToolCallStatus(getattr(tool.status, "value", tool.status)),
            evidence_ids=_tool_evidence_ids(tool.tool_name, evidence_by_label),
        )
        for tool in response.tool_results
    ]
    missing: list[GroundingMissingEvidence] = []
    if any(subject.resolution_status != SubjectResolutionStatus.RESOLVED for subject in subjects):
        missing.append(
            GroundingMissingEvidence(
                kind=MissingEvidenceKind.SUBJECT,
                severity=MissingEvidenceSeverity.CLARIFY,
                repair_path="ask_for_species_name",
            )
        )
    if route.intent == Intent.ANALYZE_TEAM and not any(tool.tool_name == "analyze_team_structure" for tool in response.tool_results):
        missing.append(
            GroundingMissingEvidence(
                kind=MissingEvidenceKind.TEAM_CONTEXT,
                severity=MissingEvidenceSeverity.CLARIFY,
                repair_path="ask_for_team_context",
            )
        )
    required_tools = _required_tools_for_intent(route.intent)
    tool_by_name = {tool.tool_name: tool for tool in response.tool_results}
    for tool_name in sorted(required_tools):
        tool = tool_by_name.get(tool_name)
        tool_status = None if tool is None else getattr(tool.status, "value", tool.status)
        if tool is None or tool_status != ToolStatus.OK.value:
            missing.append(
                GroundingMissingEvidence(
                    kind=MissingEvidenceKind.MECHANISM_DOC if tool_name == "retrieve_doc_context" else MissingEvidenceKind.SUBJECT,
                    severity=MissingEvidenceSeverity.FAIL_CLOSED,
                    repair_path=f"required_tool_not_ok:{tool_name}",
                )
            )
    evidence_ids = [item.evidence_id for item in evidence_items]
    support_level = ConfidenceFloor.CONFIRMED if evidence_ids else ConfidenceFloor.UNSUPPORTED
    if route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY}:
        support_level = ConfidenceFloor.PROVISIONAL if evidence_ids else ConfidenceFloor.UNSUPPORTED
    return GroundingPacket(
        intent=_grounding_intent_for_route(route),
        subjects=subjects,
        evidence_items=evidence_items,
        tool_calls=tool_calls,
        claim_support=[
            GroundingClaimSupport(
                claim_id="answer_summary",
                supporting_evidence_ids=evidence_ids[:10],
                support_level=support_level,
                provisional_reason=(
                    "species/relation judgement lacks D-layer casebank or full team evidence"
                    if support_level == ConfidenceFloor.PROVISIONAL
                    else None
                ),
            )
        ],
        topic_pool_delta=TopicPoolDelta(
            species_ids_added_or_updated=[species_id for species_id, _ in species_refs],
            relation_edge_ids_added_or_updated=(
                [
                    _relation_edge_id(
                        species_refs[0][0],
                        species_refs[1][0],
                        route.relation_kind or "related",
                    )
                ]
                if route.intent == Intent.RELATION_QUERY and len(species_refs) >= 2
                else []
            ),
            active_focus_type=(
                TopicFocusType.RELATION
                if route.intent == Intent.RELATION_QUERY and len(species_refs) >= 2
                else TopicFocusType.SINGLE_SPECIES
                if species_refs
                else TopicFocusType.NONE
            ),
        ),
        missing_evidence=missing,
        confidence_floor=support_level,
        clarification_state=ClarificationState.NEEDED if missing else ClarificationState.NOT_NEEDED,
    )


def _validate_grounding_packet(packet: GroundingPacket) -> tuple[bool, str | None]:
    evidence_ids = {item.evidence_id for item in packet.evidence_items}
    if len(evidence_ids) != len(packet.evidence_items):
        return False, "duplicate_evidence_ids"
    for tool in packet.tool_calls:
        status = getattr(tool.status, "value", tool.status)
        if status in {GroundingToolCallStatus.FAILED.value, GroundingToolCallStatus.SKIPPED.value}:
            return False, f"tool_not_usable:{tool.tool_name}"
        dangling = [evidence_id for evidence_id in tool.evidence_ids if evidence_id not in evidence_ids]
        if dangling:
            return False, f"dangling_tool_evidence:{tool.tool_name}"
    for claim in packet.claim_support:
        claim_support_level = getattr(claim.support_level, "value", claim.support_level)
        if claim_support_level == ConfidenceFloor.UNSUPPORTED.value:
            return False, f"unsupported_claim:{claim.claim_id}"
        dangling = [evidence_id for evidence_id in claim.supporting_evidence_ids if evidence_id not in evidence_ids]
        if dangling:
            return False, f"dangling_claim_evidence:{claim.claim_id}"
        if claim_support_level in {ConfidenceFloor.CONFIRMED.value, ConfidenceFloor.PROVISIONAL.value} and not claim.supporting_evidence_ids:
            return False, f"claim_without_evidence:{claim.claim_id}"
    if any(getattr(item.severity, "value", item.severity) == MissingEvidenceSeverity.FAIL_CLOSED.value for item in packet.missing_evidence):
        return False, "fail_closed_missing_evidence"
    clarification_state = getattr(packet.clarification_state, "value", packet.clarification_state)
    if any(getattr(item.severity, "value", item.severity) == MissingEvidenceSeverity.CLARIFY.value for item in packet.missing_evidence) and clarification_state == ClarificationState.NOT_NEEDED.value:
        return False, "clarification_missing"
    confidence_floor = getattr(packet.confidence_floor, "value", packet.confidence_floor)
    if confidence_floor == ConfidenceFloor.UNSUPPORTED.value:
        return False, "unsupported_grounding_packet"
    packet_intent = getattr(packet.intent, "value", packet.intent)
    if packet_intent in {
        GroundingIntent.SPECIES_QUERY.value,
        GroundingIntent.COUNTERPLAY.value,
        GroundingIntent.RELATION_QUERY.value,
    } and not any(getattr(subject.resolution_status, "value", subject.resolution_status) == SubjectResolutionStatus.RESOLVED.value for subject in packet.subjects):
        return False, "missing_resolved_subject"
    if packet_intent == GroundingIntent.RELATION_QUERY.value and len(
        [
            subject
            for subject in packet.subjects
            if getattr(subject.resolution_status, "value", subject.resolution_status) == SubjectResolutionStatus.RESOLVED.value
        ]
    ) < 2:
        return False, "relation_requires_two_subjects"
    return True, None


INTERNAL_ANSWER_LEAK_PATTERNS = (
    "runtime_path",
    "tool_results",
    "evidence_summary",
    "provisional",
    "reviewed",
    "d-layer",
    "d layer",
    "案例库",
    "groundingpacket",
    "grounding packet",
    "validated grounding packet",
    "internal work plan",
    "semantic_roles",
    "provisional_tags",
    "bulk_present",
    "speed_lean",
    "breaker_pressure",
    "utility_access",
    "team-conditional",
    "source_label",
    "source_type",
    "pydantic_ai",
    "native_llm_terminal",
    "deterministic_degraded_fallback",
    "retrieve_doc_context",
    "get_species_profile",
    "get_species_available_moves",
    "analyze_species_semantics",
    "analyze_team_structure",
)

UNSUPPORTED_AFFIRMATIVE_CLAIMS = ("最优", "必带", "稳吃", "环境答案")


def _answer_shape_violation(answer: str) -> str | None:
    normalized = answer.casefold()
    for pattern in INTERNAL_ANSWER_LEAK_PATTERNS:
        if pattern in normalized:
            return f"internal_label_leak:{pattern}"
    if re.search(r"(^|[^不没未无非])成熟核心", answer) and "不能断言这是成熟核心" not in answer:
        return "unsupported_affirmative_claim:成熟核心"
    for claim in UNSUPPORTED_AFFIRMATIVE_CLAIMS:
        if claim in answer:
            return f"unsupported_affirmative_claim:{claim}"
    if "{" in answer and "}" in answer and any(token in normalized for token in ("tool", "evidence", "packet", "runtime")):
        return "structured_payload_leak"
    return None


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
        per_tool_timeout_seconds: float = DEFAULT_PER_TOOL_TIMEOUT_SECONDS,
        max_turn_timeout_seconds: float = DEFAULT_MAX_TURN_TIMEOUT_SECONDS,
        max_native_model_messages: int = 64,
    ) -> None:
        normalized_backend = "pydantic_ai_native" if backend == "pydantic_ai" else backend
        self.repository = repository
        self.analyzer = analyzer or TeamStructureAnalyzer()
        self.doc_retriever = doc_retriever or DocContextRetriever()
        self.state_store = state_store or InMemorySessionStateStore()
        self.router = router or ToolRouter(repository=repository)
        self.trace_recorder = trace_recorder or LocalQATraceRecorder()
        self.backend = normalized_backend
        self.model_name = model_name
        self.native_model = native_model
        self.auto_selected = auto_selected
        self.native_timeout_seconds = native_timeout_seconds
        self.per_tool_timeout_seconds = max(0.001, per_tool_timeout_seconds)
        self.max_turn_timeout_seconds = max(1.0, max_turn_timeout_seconds)
        self.max_native_model_messages = max(1, max_native_model_messages)
        self._native_unhealthy_reason: str | None = None
        self._persona_llm_context: str | None = None

    def handle_message(self, message: str) -> AdvisorResponse:
        turn_started_at = monotonic()
        self._turn_continuity_persisted = True
        self._last_loop_iterations = 0
        self._last_loop_actions = ()
        self._last_stop_reason = "not_started"
        self._last_grounding_packet_status = "not_applicable"
        self._last_topic_pool_delta = {}
        self._last_answer_shape_checks = ()
        preloaded_state = getattr(self, "_pending_state", None)
        if preloaded_state is None:
            self._pending_state = None
            state = self.state_store.get()
        else:
            state = preloaded_state.model_copy(deep=True)
        route = self.router.route(message, state)

        if self.backend == "pydantic_ai_native" and self._should_run_native_agent_first(message, route):
            response = self._run_native_or_auto_fallback(
                message,
                self._native_route_for(route),
                state,
            )
        elif route.intent == Intent.HELP:
            response = self._help_response()
        elif route.intent == Intent.CLEAR:
            self.state_store.clear()
            self._pending_state = None
            response = self._simple_response(
                "已清空当前会话状态。你可以重新设置队伍，或直接查询某只精灵。",
                followup_options=["/set-team 草 地 龙 翼 火 水", "/species 豆丁鱼"],
                runtime_path=RuntimePath.STATIC_CONTROL_RESPONSE,
            )
        elif route.intent == Intent.SHOW_TEAM:
            response = self._show_team_response(state)
        elif route.intent == Intent.SET_TEAM:
            updated_state = state.model_copy(deep=True)
            updated_state.current_team = [to_payload(slot) for slot in route.team_slots]
            updated_state.last_analysis_type = "team_context"
            updated_state.last_result_ref = "team_set"
            self._stage_state_update(updated_state)
            response = self._simple_response(
                f"已记录当前队伍：{self._format_team(route.team_slots)}。",
                followup_options=["分析这队联防", "补洞方向是什么"],
                runtime_path=RuntimePath.STATIC_CONTROL_RESPONSE,
            )
        elif route.intent == Intent.ANALYZE_TEAM:
            response = (
                self._run_native_or_auto_fallback(message, route, state)
                if self.backend == "pydantic_ai_native"
                else self._handle_team_analysis_deterministic(message, route, state)
            )
        elif route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY}:
            response = (
                self._run_native_or_auto_fallback(message, route, state)
                if self.backend == "pydantic_ai_native"
                else self._handle_species_query_deterministic(message, route, state)
            )
        elif route.intent == Intent.EXIT:
            response = self._simple_response(
                "收到退出指令。",
                followup_options=[],
                runtime_path=RuntimePath.STATIC_CONTROL_RESPONSE,
            )
        elif self.router.is_future_or_live_meta_refusal(route):
            response = self._future_or_live_meta_refusal_response()
        elif route.intent == Intent.GENERAL_CHAT:
            response = (
                self._future_or_live_meta_refusal_response()
                if route.raw_argument == "future_or_live_meta"
                else self._general_chat_degraded_response(message)
            )
        else:
            response = self._simple_response(
                "这个问题需要我先确认目标。你可以直接给一只精灵、当前队伍，或说明你想优化输出、联防还是先手节奏。",
                followup_options=["分析这队联防", "查询某只精灵的定位", "我应该补充哪些队伍信息"],
            )

        if monotonic() - turn_started_at > self.max_turn_timeout_seconds:
            response = self._max_turn_timeout_response(route=route, response=response)

        self._record_turn_summary(message=message, route=route, response=response)
        self._commit_staged_state()
        if not getattr(self, "_turn_continuity_persisted", True):
            response = response.model_copy(deep=True)
            response.continuity_persisted = False
            response.confidence_notes.insert(
                0,
                "continuity_not_persisted: 本轮回答已生成，但当前会话连续性写入失败；后续追问可能需要重新说明上下文。",
            )
        self.trace_recorder.record(
            trace=self._build_execution_trace(
                route=route,
                response=response,
                turn_started_at=turn_started_at,
            )
        )
        return response

    def set_team_context_slots(self, slots: list[dict[str, Any]]) -> None:
        updated_state = self._current_working_state().model_copy(deep=True)
        updated_state.current_team = [dict(slot) for slot in slots]
        updated_state.last_analysis_type = "team_context"
        updated_state.last_result_ref = "team_builder_context" if slots else None
        now = datetime.now(UTC).isoformat()
        turn_id = f"team_context:{_text_digest(now)}"
        for slot in slots:
            species_id = str(slot.get("species_key") or "").strip()
            display_name = str(slot.get("nickname") or species_id).strip()
            if species_id and display_name:
                _upsert_topic_species(
                    updated_state.conversation_topic_pool,
                    species_id=species_id,
                    display_name=display_name,
                    source_type=TopicSourceType.TEAM_SETTING,
                    turn_id=turn_id,
                    created_at=now,
                )
        self._stage_state_update(updated_state)

    def set_persona_llm_context(self, context: str | None) -> None:
        self._persona_llm_context = context.strip() if context and context.strip() else None

    def _should_run_native_agent_first(self, message: str, route: RouteDecision) -> bool:
        return not self._is_local_control_command(message, route)

    def _is_local_control_command(self, message: str, route: RouteDecision) -> bool:
        if not message.strip().startswith("/"):
            return False
        return route.intent in {
            Intent.HELP,
            Intent.CLEAR,
            Intent.SHOW_TEAM,
            Intent.SET_TEAM,
            Intent.EXIT,
        }

    def _native_route_for(self, route: RouteDecision) -> RouteDecision:
        if route.intent == Intent.UNSUPPORTED:
            return RouteDecision(Intent.GENERAL_CHAT, ())
        return route

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
        if route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY} and self.repository is None:
            return self._simple_response(
                "battle-dex 仓库当前不可用，无法做物种级事实查询。结构分析仍可继续。",
                followup_options=["/set-team 草 地 龙 翼 火 水", "分析这队联防"],
            )
        if route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY} and isinstance(self.native_model, RocoNativeModelConfig):
            return self._native_grounded_terminal_response(message, route, state)
        if (
            route.intent == Intent.ANALYZE_TEAM
            and isinstance(self.native_model, RocoNativeModelConfig)
            and _resolve_team_slots(route, state)
        ):
            return self._native_grounded_terminal_response(message, route, state)

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

        try:
            agent = _build_native_agent(self._native_output_mode())
        except RuntimeError as exc:
            return self._native_failure_response(
                route=route,
                state=state,
                reason=str(exc),
            )

        deps = NativeAdvisorDeps(
            repository=self.repository,
            analyzer=self.analyzer,
            doc_retriever=self.doc_retriever,
            state=state,
            route=route,
            message=message,
            per_tool_timeout_seconds=self.per_tool_timeout_seconds,
        )
        runtime_fingerprint = _native_runtime_fingerprint(self.native_model)
        message_history = (
            list(state.native_model_messages)
            if runtime_fingerprint is not None
            and state.native_runtime_fingerprint == runtime_fingerprint
            else []
        )

        def run_agent() -> Any:
            kwargs: dict[str, Any] = {
                "deps": deps,
                "model": model,
                "instructions": self._native_instructions(route, state),
            }
            if message_history:
                kwargs["message_history"] = message_history
            model_settings = _native_model_settings_for_config(self.native_model)
            if model_settings is not None:
                kwargs["model_settings"] = model_settings
            usage_limits = _native_usage_limits_for_route(route)
            if usage_limits is not None:
                kwargs["usage_limits"] = usage_limits
            return agent.run_sync(message, **kwargs)
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
            if _is_native_usage_limit_error(exc):
                return self._native_terminal_budget_failure_response(
                    route=route,
                    state=state,
                    trace=deps.trace,
                    reason=str(exc),
                )
            return self._native_failure_response(
                route=route,
                state=state,
                reason=f"provider/model failure: {exc.__class__.__name__}",
            )
        response = _ensure_general_chat_confidence_note(result.output, route)
        timeout_tool = _tool_timeout_result(response)
        if timeout_tool is not None:
            return self._tool_timeout_response(timeout_tool.summary)
        response.runtime_path = RuntimePath.NATIVE_LLM_TERMINAL
        shape_error = _answer_shape_violation(response.answer_summary)
        if shape_error is not None:
            return self._answer_shape_failure_response(reason=shape_error)
        self._set_loop_state(
            iterations=1,
            actions=("synthesize",),
            stop_reason="native_terminal_synthesized",
            grounding_packet_status="not_required",
            answer_shape_checks=("passed",),
        )
        self._update_state_after_analysis(route, state, deps.trace)
        self._update_native_protocol_history(
            result,
            runtime_fingerprint=runtime_fingerprint,
        )
        return _add_partial_team_caveat(response, _resolve_team_slots(route, state)) if route.intent == Intent.ANALYZE_TEAM else response

    def _native_grounded_terminal_response(
        self,
        message: str,
        route: RouteDecision,
        state: AdvisorSessionState,
    ) -> AdvisorResponse:
        loop = self._run_grounded_planner_tool_loop(message=message, route=route, state=state)
        grounded = loop.response
        packet = loop.packet
        packet_ok = loop.packet_ok
        packet_error = loop.packet_error
        self._set_loop_state(
            iterations=loop.iterations,
            actions=loop.actions,
            stop_reason=loop.stop_reason,
            grounding_packet_status="valid" if packet_ok else f"invalid:{packet_error}",
            topic_pool_delta=packet.topic_pool_delta.model_dump(mode="json"),
        )
        if not packet_ok:
            self._append_loop_action("degrade")
            return self._grounded_native_failure_fallback(
                grounded,
                reason=f"grounding_packet_invalid:{packet_error}",
            )
        try:
            model = self._resolve_native_model()
        except Exception:
            return self._grounded_native_failure_fallback(grounded, reason="native_model_config_unavailable")
        if model is None:
            return self._grounded_native_failure_fallback(grounded, reason="missing_native_model_config")
        try:
            agent = _build_native_agent("prompted")
        except RuntimeError as exc:
            return self._grounded_native_failure_fallback(grounded, reason=str(exc))

        runtime_fingerprint = _native_runtime_fingerprint(self.native_model)
        synthesis_prompt = self._grounded_terminal_prompt(
            message=message,
            route=route,
            grounded=grounded,
            packet=packet,
        )

        def run_agent() -> Any:
            working_state = self._current_working_state(default=state)
            kwargs: dict[str, Any] = {
                "deps": NativeAdvisorDeps(
                    repository=self.repository,
                    analyzer=self.analyzer,
                    doc_retriever=self.doc_retriever,
                    state=working_state,
                    route=RouteDecision(Intent.GENERAL_CHAT, ()),
                    message=message,
                    per_tool_timeout_seconds=self.per_tool_timeout_seconds,
                ),
                "model": model,
                "instructions": self._native_instructions(route, working_state),
            }
            model_settings = _native_model_settings_for_config(self.native_model)
            if model_settings is not None:
                kwargs["model_settings"] = model_settings
            return agent.run_sync(synthesis_prompt, **kwargs)

        try:
            result = run_native_call_with_timeout(run_agent, seconds=self.native_timeout_seconds)
        except NativeRuntimeTimeoutError:
            self._append_loop_action("degrade")
            return self._grounded_native_failure_fallback(
                grounded,
                reason=f"native runtime timeout after {self.native_timeout_seconds:.1f}s",
            )
        except Exception as exc:
            self._append_loop_action("degrade")
            return self._grounded_native_failure_fallback(
                grounded,
                reason=f"provider/model failure: {exc.__class__.__name__}",
            )

        synthesized = result.output.model_copy(deep=True)
        synthesized.backend = "pydantic_ai_native"
        synthesized.runtime_path = RuntimePath.NATIVE_LLM_TERMINAL
        synthesized.tool_results = list(grounded.tool_results)
        synthesized.evidence_summary = list(grounded.evidence_summary)
        synthesized.confidence_notes = [
            "native_llm_terminal: deterministic tools/rules were used as hidden grounding before final Agent synthesis.",
            *grounded.confidence_notes,
            *[
                note
                for note in synthesized.confidence_notes
                if note not in grounded.confidence_notes
            ],
        ]
        if not synthesized.followup_options:
            synthesized.followup_options = list(grounded.followup_options)
        if not synthesized.answer_summary.strip():
            synthesized.answer_summary = grounded.answer_summary
        shape_error = _answer_shape_violation(synthesized.answer_summary)
        if shape_error is not None:
            self._append_loop_action("grade_answer")
            self._set_answer_shape_checks((f"failed:{shape_error}",))
            return self._grounded_native_failure_fallback(
                grounded,
                reason=f"answer_shape_invalid:{shape_error}",
            )
        self._append_loop_action("synthesize")
        self._append_loop_action("grade_answer")
        self._set_answer_shape_checks(("passed",))
        self._last_stop_reason = "native_grounded_terminal_synthesized"
        self._update_native_protocol_history(result, runtime_fingerprint=runtime_fingerprint)
        return synthesized

    def _run_grounded_planner_tool_loop(
        self,
        *,
        message: str,
        route: RouteDecision,
        state: AdvisorSessionState,
    ) -> GroundedLoopResult:
        actions: list[str] = []
        seen_repairs: set[str] = set()
        last_response: AdvisorResponse | None = None
        last_packet: GroundingPacket | None = None
        last_error: str | None = None
        previous_missing_count: int | None = None

        for iteration in range(1, 4):
            actions.append("ground" if iteration == 1 else "repair")
            response = (
                self._handle_team_analysis_deterministic(message, route, state)
                if route.intent == Intent.ANALYZE_TEAM
                else self._handle_species_query_deterministic(message, route, state)
            )
            packet = _build_grounding_packet(route, response)
            actions.append("validate_packet")
            packet_ok, packet_error = _validate_grounding_packet(packet)
            last_response = response
            last_packet = packet
            last_error = packet_error
            if packet_ok:
                actions.append("synthesize")
                return GroundedLoopResult(
                    response=response,
                    packet=packet,
                    packet_ok=True,
                    packet_error=None,
                    iterations=iteration,
                    actions=tuple(actions),
                    stop_reason="packet_validated",
                )

            missing_count = len(packet.missing_evidence)
            if previous_missing_count is not None and missing_count >= previous_missing_count:
                actions.append("degrade")
                return GroundedLoopResult(
                    response=response,
                    packet=packet,
                    packet_ok=False,
                    packet_error=packet_error,
                    iterations=iteration,
                    actions=tuple(actions),
                    stop_reason="missing_evidence_not_reduced",
                )
            previous_missing_count = missing_count
            needs_subject_clarification = any(
                subject.resolution_status != SubjectResolutionStatus.RESOLVED
                for subject in packet.subjects
            )
            if (
                packet_error in {"missing_resolved_subject", "relation_requires_two_subjects", "clarification_missing"}
                or needs_subject_clarification
            ):
                actions.append("ask_clarification")
                return GroundedLoopResult(
                    response=response,
                    packet=packet,
                    packet_ok=False,
                    packet_error=packet_error,
                    iterations=iteration,
                    actions=tuple(actions),
                    stop_reason="clarification_required",
                )
            repair_key = f"{route.intent.value}:{packet_error}:retrieve_more"
            if repair_key in seen_repairs:
                actions.append("degrade")
                return GroundedLoopResult(
                    response=response,
                    packet=packet,
                    packet_ok=False,
                    packet_error=packet_error,
                    iterations=iteration,
                    actions=tuple(actions),
                    stop_reason="repeated_retrieve_deduped",
                )
            seen_repairs.add(repair_key)
            actions.append("retrieve_more")
            repaired = self._retrieve_more_for_grounded_packet(
                message=message,
                route=route,
                response=response,
            )
            repaired_packet = _build_grounding_packet(route, repaired)
            actions.append("validate_packet")
            repaired_ok, repaired_error = _validate_grounding_packet(repaired_packet)
            if repaired_ok:
                actions.append("synthesize")
                return GroundedLoopResult(
                    response=repaired,
                    packet=repaired_packet,
                    packet_ok=True,
                    packet_error=None,
                    iterations=min(3, iteration + 1),
                    actions=tuple(actions),
                    stop_reason="packet_repaired_by_retrieve_more",
                )
            if len(repaired_packet.missing_evidence) >= missing_count:
                actions.append("degrade")
                return GroundedLoopResult(
                    response=repaired,
                    packet=repaired_packet,
                    packet_ok=False,
                    packet_error=repaired_error,
                    iterations=min(3, iteration + 1),
                    actions=tuple(actions),
                    stop_reason="missing_evidence_not_reduced",
                )

        assert last_response is not None and last_packet is not None
        actions.append("degrade")
        return GroundedLoopResult(
            response=last_response,
            packet=last_packet,
            packet_ok=False,
            packet_error=last_error or "max_iteration_exhausted",
            iterations=3,
            actions=tuple(actions),
            stop_reason="max_iteration_exhausted",
        )

    def _retrieve_more_for_grounded_packet(
        self,
        *,
        message: str,
        route: RouteDecision,
        response: AdvisorResponse,
    ) -> AdvisorResponse:
        expanded_query = " ".join(
            part
            for part in (
                message,
                route.species_query,
                route.relation_anchor_query,
                route.relation_partner_query,
                "机制 克制 配合 队伍 反制",
            )
            if part
        )
        snippets, mechanism_matches = _auto_doc_snippets(
            self.doc_retriever,
            query=expanded_query,
            analysis_type="team" if route.intent == Intent.ANALYZE_TEAM else "species",
            evidence_texts=[item.content for item in response.evidence_summary[:8]],
            limit=8,
            timeout_seconds=self.per_tool_timeout_seconds,
        )
        repaired = response.model_copy(deep=True)
        existing_tool_names = {tool.tool_name for tool in repaired.tool_results}
        repair_tool = AdvisorToolResult(
            tool_name="retrieve_doc_context",
            summary="retrieve_more:" + _mechanism_tool_summary(snippets, mechanism_matches),
            payload=_mechanism_doc_payload(snippets, mechanism_matches),
        )
        if "retrieve_doc_context" in existing_tool_names:
            repaired.tool_results = [
                repair_tool if tool.tool_name == "retrieve_doc_context" else tool
                for tool in repaired.tool_results
            ]
        else:
            repaired.tool_results.append(repair_tool)
        existing_labels = {item.source_label for item in repaired.evidence_summary}
        for snippet in snippets:
            if snippet.source_path not in existing_labels:
                repaired.evidence_summary.append(
                    AdvisorEvidenceItem(
                        source_type=SourceType.DOC,
                        source_label=snippet.source_path,
                        confidence=snippet.confidence,
                        content=snippet.content,
                        retrieval_reason="retrieve_more:" + snippet.retrieval_reason,
                    )
                )
        if snippets and not any("retrieve_more" in note for note in repaired.confidence_notes):
            repaired.confidence_notes.append("retrieve_more: 扩展检索已补充机制上下文。")
        return repaired

    def _answer_shape_failure_response(self, *, reason: str) -> AdvisorResponse:
        self._set_loop_state(
            iterations=1,
            actions=("synthesize", "grade_answer", "degrade"),
            stop_reason=f"answer_shape_invalid:{reason}",
            grounding_packet_status="not_required",
            answer_shape_checks=(f"failed:{reason}",),
        )
        return AdvisorResponse(
            backend=self.backend,
            runtime_path=RuntimePath.DETERMINISTIC_DEGRADED_FALLBACK,
            answer_summary=(
                "本轮 native Agent 回复没有通过展示安全检查，因此已停止展示模型原文。"
                "请换一种更具体的问法，或让我基于已确认资料重新回答。"
            ),
            tool_results=[],
            evidence_summary=[],
            confidence_notes=[
                f"answer_shape_invalid:{reason}; raw native answer was discarded before user-visible return.",
            ],
            followup_options=["重新问这个问题", "补充具体精灵或队伍", "先查单只精灵"],
        )

    def _max_turn_timeout_response(
        self,
        *,
        route: RouteDecision,
        response: AdvisorResponse,
    ) -> AdvisorResponse:
        self._append_loop_action("degrade")
        self._last_stop_reason = "max_turn_timeout_exceeded"
        return AdvisorResponse(
            backend=response.backend,
            runtime_path=RuntimePath.DETERMINISTIC_DEGRADED_FALLBACK,
            answer_summary=(
                "本轮处理超过最大回合预算，已停止继续推理以避免卡住。"
                "请缩小问题范围，或先给出明确的精灵/队伍目标。"
            ),
            tool_results=list(response.tool_results),
            evidence_summary=list(response.evidence_summary),
            confidence_notes=[
                f"max_turn_timeout_exceeded: budget={self.max_turn_timeout_seconds:.1f}s.",
                *response.confidence_notes,
            ],
            followup_options=response.followup_options or _default_followups(route, ToolTrace()),
        )

    def _tool_timeout_response(self, reason: str) -> AdvisorResponse:
        self._append_loop_action("degrade")
        self._last_stop_reason = "tool_timeout"
        return AdvisorResponse(
            backend=self.backend,
            runtime_path=RuntimePath.DETERMINISTIC_DEGRADED_FALLBACK,
            answer_summary=(
                "本轮有本地工具调用超过预算，已停止继续分析。"
                "请缩小问题范围，或稍后重试。"
            ),
            tool_results=[
                AdvisorToolResult(
                    tool_name="runtime_tool_timeout",
                    status=ToolStatus.FAILED,
                    summary=reason,
                    payload={"error": "tool_timeout"},
                )
            ],
            evidence_summary=[],
            confidence_notes=[f"tool_timeout: {reason}"],
            followup_options=["缩小问题范围后重试", "先查询单只精灵", "补充明确队伍目标"],
        )

    def _grounded_native_failure_fallback(self, grounded: AdvisorResponse, *, reason: str) -> AdvisorResponse:
        fallback = grounded.model_copy(deep=True)
        fallback.runtime_path = RuntimePath.DETERMINISTIC_DEGRADED_FALLBACK
        if self.auto_selected:
            fallback.backend = "auto_fallback_deterministic"
            self._native_unhealthy_reason = reason
        fallback.confidence_notes.insert(
            0,
            f"deterministic_degraded_fallback: native terminal synthesis unavailable; reason={reason}.",
        )
        return fallback

    def _grounded_terminal_prompt(
        self,
        *,
        message: str,
        route: RouteDecision,
        grounded: AdvisorResponse,
        packet: GroundingPacket,
    ) -> str:
        evidence_lines = [
            f"- {item.source_label}: {item.content}"
            for item in grounded.evidence_summary[:8]
        ]
        tool_lines = [
            f"- {tool.tool_name}: {tool.summary}"
            for tool in grounded.tool_results
        ]
        mode = "counterplay tactical advice" if route.intent == Intent.COUNTERPLAY else route.intent.value
        return "\n".join(
            [
                "User question:",
                message,
                "",
                f"Internal work plan: {mode}.",
                "",
                "Hidden grounding tool results:",
                *tool_lines,
                "",
                "Grounding evidence:",
                *evidence_lines,
                "",
                "Internal grounding packet, do not mention it:",
                packet.model_dump_json(exclude_none=True),
                "",
                "Draft deterministic digest, for grounding only, not for direct copy:",
                grounded.answer_summary,
                "",
                "Write one natural Chinese Agent answer for the user. Do not expose JSON, route names, tool payloads, backend labels, raw rules, internal uncertainty terms, or semantic tags. Forbidden visible words include provisional, reviewed, D-layer, 案例库, grounding packet, runtime_path, bulk_present, speed_lean, breaker_pressure, and utility_access. If this is counterplay, focus on what threatens the user and practical response axes grounded above.",
            ]
        )

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
            elif route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY}:
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

    def _native_terminal_budget_failure_response(
        self,
        *,
        route: RouteDecision,
        state: AdvisorSessionState,
        trace: ToolTrace,
        reason: str,
    ) -> AdvisorResponse:
        response = AdvisorResponse(
            backend="pydantic_ai_native",
            runtime_path=RuntimePath.DETERMINISTIC_DEGRADED_FALLBACK,
            answer_summary=(
                "本轮已到达 Agent 调用预算上限，runtime 已停止继续调用工具以保留安全回复边界。"
                "请缩小问题范围，或先提供更明确的精灵/队伍目标后重试。"
            ),
            tool_results=list(trace.tool_results),
            evidence_summary=list(trace.evidence_summary),
            confidence_notes=[
                "terminal_response_budget_exhausted: 最终回复阶段由 Roco runtime 接管，避免空回复或无界工具循环。",
                f"native_usage_limit_reason={reason}",
            ],
            followup_options=_default_followups(route, trace),
        )
        return _add_partial_team_caveat(response, _resolve_team_slots(route, state)) if route.intent == Intent.ANALYZE_TEAM else response

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
        elif route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY}:
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

    def _native_output_mode(self) -> str:
        return _native_output_mode_for_config(self.native_model)

    def _native_instructions(self, route: RouteDecision, state: AdvisorSessionState) -> str:
        team_slots = tuple(_team_slot_from_payload(slot_payload) for slot_payload in state.current_team)
        team_summary = self._format_team(team_slots) if team_slots else "none"
        route_lines = [
            f"Approved intent: {route.intent.value}.",
            f"Current team state: {team_summary}.",
            f"Current species context: {state.current_species_context or 'none'}.",
            "Recent compact turn summaries: " + _format_recent_turn_summaries(state),
            "Conversation topic pool: " + _format_topic_pool(state.conversation_topic_pool),
            "You must keep confirmed claims limited to deterministic engine or SQL-backed facts.",
            "Do not invent evidence_summary or tool_results; they are taken from tool traces.",
            "Every normal user question must be answered through the Agent boundary. Routing is only an internal work plan.",
            "Do not expose route names, raw tool payloads, backend labels, or JSON as the primary user answer.",
            "Do not expose internal uncertainty or trace vocabulary in answer_summary: no provisional, reviewed, D-layer, 案例库, grounding packet, runtime_path, bulk_present, speed_lean, breaker_pressure, utility_access, or semantic_roles.",
        ]
        if self._persona_llm_context:
            route_lines.append("Selected persona writing context: " + self._persona_llm_context)
        if team_slots:
            route_lines.append(
                "Structured team context: " + " ; ".join(_team_slot_context_line(slot) for slot in team_slots)
            )
        if route.intent == Intent.GENERAL_CHAT:
            route_lines.extend(
                [
                    "This is the P7 real-agent-chat path for natural-language prompts that did not match deterministic routing.",
                    "Use the project vocabulary: 精灵, 队伍, 技能. Do not say Pokémon, 宝可梦, 宠物小精灵, or Pokemon.",
                    "Do not introduce yourself, name the app, or state a job title unless explicitly asked; persona identity is supplied by the persona layer.",
                    "Answer directly only for product guidance, clarifying questions, or high-level non-factual advice.",
                    "For greetings or broad help requests, do not list unsupported game-wide features such as cultivation, breeding, leveling, training, resource planning, or general progression.",
                    "If the user asks for concrete Roco species, move, mechanism, or team claims, call approved tools when enough identifiers/context exist.",
                    "If there is not enough team/species context, ask one concise clarifying question instead of pretending analysis ran.",
                    "Do not say the MVP only supports fixed commands unless the request truly requires an unavailable capability.",
                ]
            )
            if route.raw_argument == "future_or_live_meta":
                route_lines.append(
                    "The user is asking for future official changes or live meta. Answer through the Agent boundary with a concise bounded refusal: no live/web/official-feed data is available, then offer current battle-dex or team-structure analysis. Do not route this as a static control response."
                )
        if route.intent == Intent.ANALYZE_TEAM:
            route_lines.append(
                "Before finalizing, call analyze_team_structure and retrieve_doc_context."
            )
        if route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY}:
            route_lines.append(
                "Before finalizing, call get_species_profile, get_species_available_moves, retrieve_doc_context, and analyze_species_semantics."
            )
            if route.intent == Intent.COUNTERPLAY:
                route_lines.append(
                    "The user is asking for counterplay. Synthesize practical response axes from grounded facts, not a raw species sheet."
                )
        return " ".join(route_lines)

    def _update_state_after_analysis(
        self,
        route: RouteDecision,
        state: AdvisorSessionState,
        trace: ToolTrace,
    ) -> None:
        updated_state = self._current_working_state(default=state).model_copy(deep=True)
        if route.intent == Intent.ANALYZE_TEAM:
            slots = route.team_slots or tuple(self._slots_from_state(state))
            updated_state.current_team = [to_payload(slot) for slot in slots]
            updated_state.last_analysis_type = "team_structure"
            updated_state.last_result_ref = "team_structure"
        elif route.intent == Intent.SET_TEAM:
            updated_state.current_team = [to_payload(slot) for slot in route.team_slots]
            updated_state.last_analysis_type = "team_context"
            updated_state.last_result_ref = "team_set"
        elif route.intent in {Intent.SPECIES_QUERY, Intent.COUNTERPLAY, Intent.RELATION_QUERY}:
            if route.team_slots:
                updated_state.current_team = [to_payload(slot) for slot in route.team_slots]
            if trace.species_display_name:
                updated_state.current_species_context = trace.species_display_name
            updated_state.last_analysis_type = route.intent.value
            updated_state.last_result_ref = trace.species_id or route.species_query
        self._stage_state_update(updated_state)

    def _current_working_state(self, default: AdvisorSessionState | None = None) -> AdvisorSessionState:
        pending = getattr(self, "_pending_state", None)
        if pending is not None:
            return pending.model_copy(deep=True)
        if default is not None:
            return default.model_copy(deep=True)
        return self.state_store.get().model_copy(deep=True)

    def _stage_state_update(self, state: AdvisorSessionState) -> None:
        self._pending_state = state.model_copy(deep=True)

    def _commit_staged_state(self) -> bool:
        pending = getattr(self, "_pending_state", None)
        if pending is None:
            return True
        try:
            self.state_store.set(pending)
            self._pending_state = None
            return True
        except Exception:
            self._turn_continuity_persisted = False
            self._pending_state = None
            return False

    def _set_loop_state(
        self,
        *,
        iterations: int,
        actions: tuple[str, ...],
        stop_reason: str,
        grounding_packet_status: str,
        topic_pool_delta: dict[str, Any] | None = None,
        answer_shape_checks: tuple[str, ...] | None = None,
    ) -> None:
        self._last_loop_iterations = max(1, iterations)
        self._last_loop_actions = actions
        self._last_stop_reason = stop_reason
        self._last_grounding_packet_status = grounding_packet_status
        if topic_pool_delta is not None:
            self._last_topic_pool_delta = topic_pool_delta
        if answer_shape_checks is not None:
            self._last_answer_shape_checks = answer_shape_checks

    def _append_loop_action(self, action: str) -> None:
        actions = tuple(getattr(self, "_last_loop_actions", ()))
        if not actions or actions[-1] != action:
            self._last_loop_actions = (*actions, action)

    def _set_answer_shape_checks(self, checks: tuple[str, ...]) -> None:
        self._last_answer_shape_checks = checks

    def _build_execution_trace(
        self,
        *,
        route: RouteDecision,
        response: AdvisorResponse,
        turn_started_at: float,
    ) -> AgentExecutionTrace:
        shape_error = _answer_shape_violation(response.answer_summary)
        answer_shape_checks = tuple(getattr(self, "_last_answer_shape_checks", ())) or (
            f"failed:{shape_error}" if shape_error else "passed",
        )
        loop_actions = tuple(getattr(self, "_last_loop_actions", ()))
        if not loop_actions:
            loop_actions = ("degrade",) if response.runtime_path == RuntimePath.DETERMINISTIC_DEGRADED_FALLBACK else ("synthesize",)
        stop_reason = str(getattr(self, "_last_stop_reason", "completed"))
        if stop_reason == "not_started":
            stop_reason = "deterministic_fallback" if response.runtime_path == RuntimePath.DETERMINISTIC_DEGRADED_FALLBACK else "completed"
        elapsed = monotonic() - turn_started_at
        if elapsed > self.max_turn_timeout_seconds:
            stop_reason = "max_turn_timeout_exceeded"
        return AgentExecutionTrace(
            turn_id=uuid4().hex,
            session_id=str(getattr(self.state_store, "session_id", "local_session")),
            plan_intent=route.intent.value,
            loop_iterations=max(1, int(getattr(self, "_last_loop_iterations", 1))),
            loop_actions=loop_actions,
            stop_reason=stop_reason,
            grounding_packet_status=str(getattr(self, "_last_grounding_packet_status", "not_applicable")),
            topic_pool_delta=dict(getattr(self, "_last_topic_pool_delta", {}) or {}),
            answer_shape_checks=answer_shape_checks,
            final_grade="fail" if any(check.startswith("failed:") for check in answer_shape_checks) else "pass",
            runtime_path=str(response.runtime_path),
            tool_calls=tuple(tool.tool_name for tool in response.tool_results),
            retrieval_refs=tuple(item.source_label for item in response.evidence_summary),
            provider_timeout_seconds=self.native_timeout_seconds,
            per_tool_timeout_seconds=self.per_tool_timeout_seconds,
            max_turn_timeout_seconds=self.max_turn_timeout_seconds,
        )

    def _record_turn_summary(
        self,
        *,
        message: str,
        route: RouteDecision,
        response: AdvisorResponse,
    ) -> None:
        if route.intent in {Intent.CLEAR, Intent.EXIT}:
            return
        if response.runtime_path == RuntimePath.STATIC_CONTROL_RESPONSE:
            return
        updated_state = self._current_working_state().model_copy(deep=True)
        subject = _resolved_turn_subject(route, response, updated_state)
        turn_id = uuid4().hex
        user_excerpt = _compact_text(message, limit=96)
        summary = AdvisorTurnSummary(
            turn_id=turn_id,
            user_message="",
            user_message_excerpt=user_excerpt,
            user_message_digest=_text_digest(message),
            intent_digest=_text_digest(f"{route.intent.value}:{subject or ''}:{route.relation_partner_query or ''}"),
            route_intent=route.intent.value,
            resolved_subject=subject,
            answer_digest=_compact_text(response.answer_summary, limit=360),
            grounding_refs=_compact_unique(
                [item.source_label for item in response.evidence_summary],
                limit=10,
            ),
            tool_names=_compact_unique(
                [tool.tool_name for tool in response.tool_results],
                limit=10,
            ),
            backend=response.backend,
            created_at=datetime.now(UTC).isoformat(),
        )
        updated_state.recent_turn_summaries = [
            *updated_state.recent_turn_summaries,
            summary,
        ][-RECENT_TURN_SUMMARY_LIMIT:]
        updated_state.conversation_topic_pool = _update_topic_pool(
            updated_state.conversation_topic_pool,
            route=route,
            response=response,
            turn_id=turn_id,
            created_at=summary.created_at,
        )
        self._stage_state_update(updated_state)

    def _update_native_protocol_history(
        self,
        result: Any,
        *,
        runtime_fingerprint: str | None,
    ) -> None:
        if runtime_fingerprint is None or not hasattr(result, "all_messages"):
            return
        all_messages = result.all_messages
        try:
            messages = all_messages() if callable(all_messages) else all_messages
        except Exception:
            return
        if not isinstance(messages, list):
            return
        if len(messages) > self.max_native_model_messages:
            messages = messages[-self.max_native_model_messages :]
        updated_state = self._current_working_state().model_copy(deep=True)
        updated_state.native_model_messages = list(messages)
        updated_state.native_runtime_fingerprint = runtime_fingerprint
        self._stage_state_update(updated_state)

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

        try:
            structure_report = run_tool_call_with_timeout(
                "analyze_team_structure",
                lambda: self.analyzer.analyze(slots),
                seconds=self.per_tool_timeout_seconds,
            )
        except ToolRuntimeTimeoutError as exc:
            return self._tool_timeout_response(str(exc))
        guard = _build_team_semantic_guard(slots, structure_report)
        snippets, mechanism_matches = _auto_doc_snippets(
            self.doc_retriever,
            query=message,
            analysis_type="team",
            evidence_texts=[],
            timeout_seconds=self.per_tool_timeout_seconds,
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
            answer_summary=self._team_answer_summary(structure_report, guard, slots),
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

        if route.intent == Intent.RELATION_QUERY and route.relation_anchor_query and route.relation_partner_query:
            return self._handle_relation_query_deterministic(message, route, state)

        query = route.species_query or route.raw_argument
        if not query:
            return self._simple_response(
                "请给出物种名，例如 `/species 豆丁鱼`。",
                followup_options=["/species 豆丁鱼"],
            )

        try:
            profile = run_tool_call_with_timeout(
                "get_species_profile",
                lambda: self.repository.get_species_profile(query),
                seconds=self.per_tool_timeout_seconds,
            )
        except ToolRuntimeTimeoutError as exc:
            return self._tool_timeout_response(str(exc))
        if profile is None:
            return self._simple_response(
                f"battle-dex 里没有找到 `{query}`。当前只支持已入库物种的事实查询。",
                followup_options=["/species 豆丁鱼", "/show-team"],
            )

        try:
            moves = run_tool_call_with_timeout(
                "get_species_available_moves",
                lambda: self.repository.get_species_available_moves(profile.species_id, limit=10),
                seconds=self.per_tool_timeout_seconds,
            )
            ability = (
                run_tool_call_with_timeout(
                    "get_ability_detail",
                    lambda: self.repository.get_ability_detail(profile.ability_name),
                    seconds=self.per_tool_timeout_seconds,
                )
                if profile.ability_name
                else None
            )
        except ToolRuntimeTimeoutError as exc:
            return self._tool_timeout_response(str(exc))
        evidence_texts = _species_mechanism_evidence_texts(profile, moves)
        snippets, mechanism_matches = _auto_doc_snippets(
            self.doc_retriever,
            query=message,
            analysis_type="species",
            evidence_texts=evidence_texts,
            timeout_seconds=self.per_tool_timeout_seconds,
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
            answer_summary=self._species_answer_summary(route, profile, moves, semantics, mechanism_matches),
            tool_results=tool_results,
            evidence_summary=evidence,
            confidence_notes=[
                "物种资料与技能池事实属于 confirmed，因为它们直接来自 SQLite battle-dex。",
                "定位判断是基于面板、特性和技能池的当前可用信息；用户侧回答应避免暴露内部置信标签。",
                *(
                    [
                        "检测到机制词但机制资料尚未完整覆盖全部相关页面，因此当前解释已按保守边界降级。"
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

    def _handle_relation_query_deterministic(
        self,
        message: str,
        route: RouteDecision,
        state: AdvisorSessionState,
    ) -> AdvisorResponse:
        assert self.repository is not None
        try:
            anchor = run_tool_call_with_timeout(
                "get_species_profile",
                lambda: self.repository.get_species_profile(route.relation_anchor_query or ""),
                seconds=self.per_tool_timeout_seconds,
            )
            partner = run_tool_call_with_timeout(
                "get_species_profile",
                lambda: self.repository.get_species_profile(route.relation_partner_query or ""),
                seconds=self.per_tool_timeout_seconds,
            )
        except ToolRuntimeTimeoutError as exc:
            return self._tool_timeout_response(str(exc))
        if anchor is None or partner is None:
            missing = route.relation_anchor_query if anchor is None else route.relation_partner_query
            return self._simple_response(
                f"battle-dex 里没有找到 `{missing}`。这组搭配暂时不能做事实化分析。",
                followup_options=["换一个已入库精灵名", "先查询单只精灵定位"],
            )

        try:
            anchor_moves = run_tool_call_with_timeout(
                "get_species_available_moves",
                lambda: self.repository.get_species_available_moves(anchor.species_id, limit=10),
                seconds=self.per_tool_timeout_seconds,
            )
            partner_moves = run_tool_call_with_timeout(
                "get_species_available_moves",
                lambda: self.repository.get_species_available_moves(partner.species_id, limit=10),
                seconds=self.per_tool_timeout_seconds,
            )
        except ToolRuntimeTimeoutError as exc:
            return self._tool_timeout_response(str(exc))
        snippets, mechanism_matches = _auto_doc_snippets(
            self.doc_retriever,
            query=message,
            analysis_type="species",
            evidence_texts=[
                *_species_mechanism_evidence_texts(anchor, anchor_moves),
                *_species_mechanism_evidence_texts(partner, partner_moves),
            ],
            timeout_seconds=self.per_tool_timeout_seconds,
        )
        anchor_semantics = _analyze_species_semantics_payload(anchor, anchor_moves)
        partner_semantics = _analyze_species_semantics_payload(partner, partner_moves)
        tool_results = [
            AdvisorToolResult(
                tool_name="get_species_profile",
                summary=f"loaded relation anchor {anchor.display_name} ({anchor.primary_type}/{anchor.secondary_type or '-'})",
                payload=anchor.model_dump(mode="json"),
            ),
            AdvisorToolResult(
                tool_name="get_species_profile",
                summary=f"loaded relation partner {partner.display_name} ({partner.primary_type}/{partner.secondary_type or '-'})",
                payload=partner.model_dump(mode="json"),
            ),
            AdvisorToolResult(
                tool_name="get_species_available_moves",
                summary=f"loaded relation move pools anchor={len(anchor_moves)} partner={len(partner_moves)}",
                payload={
                    "anchor_moves": [move.model_dump(mode="json") for move in anchor_moves[:8]],
                    "partner_moves": [move.model_dump(mode="json") for move in partner_moves[:8]],
                },
            ),
            AdvisorToolResult(
                tool_name="retrieve_doc_context",
                summary=_mechanism_tool_summary(snippets, mechanism_matches),
                payload=_mechanism_doc_payload(snippets, mechanism_matches),
            ),
            AdvisorToolResult(
                tool_name="analyze_species_semantics",
                summary=f"anchor={anchor_semantics['summary_line']}; partner={partner_semantics['summary_line']}",
                payload={"anchor": anchor_semantics, "partner": partner_semantics},
            ),
        ]
        facts = [
            AdvisorEvidenceItem(
                source_type=SourceType.FACT,
                source_label=f"species_form:{anchor.species_id}",
                confidence=anchor.confidence,
                content=(
                    f"{anchor.display_name}: type={anchor.primary_type}/{anchor.secondary_type or '-'} "
                    f"bst={anchor.base_stats.bst} ability={anchor.ability_name or 'unknown'}"
                ),
                retrieval_reason="sql_species_profile",
            ),
            AdvisorEvidenceItem(
                source_type=SourceType.FACT,
                source_label=f"species_form:{partner.species_id}",
                confidence=partner.confidence,
                content=(
                    f"{partner.display_name}: type={partner.primary_type}/{partner.secondary_type or '-'} "
                    f"bst={partner.base_stats.bst} ability={partner.ability_name or 'unknown'}"
                ),
                retrieval_reason="sql_species_profile",
            ),
        ]
        if anchor_moves:
            facts.append(
                AdvisorEvidenceItem(
                    source_type=SourceType.FACT,
                    source_label=f"species_move_pool:{anchor.species_id}",
                    confidence=ConfidenceTier.CONFIRMED,
                    content="moves=" + ",".join(move.move_name for move in anchor_moves[:6]),
                    retrieval_reason="sql_move_pool_lookup",
                )
            )
        if partner_moves:
            facts.append(
                AdvisorEvidenceItem(
                    source_type=SourceType.FACT,
                    source_label=f"species_move_pool:{partner.species_id}",
                    confidence=ConfidenceTier.CONFIRMED,
                    content="moves=" + ",".join(move.move_name for move in partner_moves[:6]),
                    retrieval_reason="sql_move_pool_lookup",
                )
            )
        evidence = ContextBuilder().build(facts=facts, mechanics=snippets)
        self._update_state_after_analysis(
            route,
            state,
            ToolTrace(species_display_name=anchor.display_name, species_id=anchor.species_id),
        )
        answer = (
            f"如果你说的是 `{anchor.display_name}` 配合 `{partner.display_name}` 做主C轴，"
            f"我不会把焦点改成只分析 `{partner.display_name}`。按当前资料看，"
            f"`{anchor.display_name}` 更像先手/功能或副攻入口：{anchor_semantics['interpretation']}；"
            f"`{partner.display_name}` 的主C成立条件还要看技能、队伍牺牲顺序和补盲：{partner_semantics['interpretation']}。"
            " 所以这更像一个待验证的双核/前置铺垫关系，而不是已经证明成熟的固定核心。"
        )
        return AdvisorResponse(
            backend=self.backend,
            answer_summary=answer,
            tool_results=tool_results,
            evidence_summary=evidence,
            confidence_notes=[
                "relation_query: 已保留上一轮主体和本轮新物种的关系，不把焦点单向覆盖到新物种。",
                "relation_query: 当前只按已知技能、属性和队伍语境判断关系强弱，不把它说成固定成熟核心。",
            ],
            followup_options=[
                f"继续问：{anchor.display_name} 首发怎么给 {partner.display_name} 铺路",
                f"继续问：{partner.display_name} 主C怕什么属性",
                "继续问：把我的完整队伍也纳入判断",
            ],
        )

    def _help_response(self) -> AdvisorResponse:
        return self._simple_response(
            "可用命令：`/set-team`、`/show-team`、`/analyze`、`/species <名称>`、`/clear`、`/exit`。自然语言也支持队伍结构问题和已入库精灵查询。",
            followup_options=["/set-team 草 地 龙 翼 火 水", "/species 豆丁鱼", "分析这队联防"],
            runtime_path=RuntimePath.STATIC_CONTROL_RESPONSE,
        )

    def _future_or_live_meta_refusal_response(self) -> AdvisorResponse:
        return self._simple_response(
            (
                "当前 MVP 没有 web/live 官方平衡公告 feed，也没有实时环境数据；"
                "因此不能预测未来加强/削弱、明天官方改动，或 live meta 变化。"
                " 我现在能做的是：分析当前队伍结构、查询 battle-dex 已入库事实，"
                "以及基于当前事实讨论某只精灵的打法定位。"
            ),
            followup_options=["分析 草 地 龙 翼 火 水 这队联防", "/species 豆丁鱼", "豆丁鱼适合干什么"],
            runtime_path=RuntimePath.DETERMINISTIC_DEGRADED_FALLBACK,
        )

    def _show_team_response(self, state: AdvisorSessionState) -> AdvisorResponse:
        slots = tuple(self._slots_from_state(state))
        if not slots:
            return self._simple_response(
                "当前会话里还没有队伍。",
                followup_options=["/set-team 草 地 龙 翼 火 水"],
                runtime_path=RuntimePath.STATIC_CONTROL_RESPONSE,
            )
        return self._simple_response(
            f"当前队伍：{self._format_team(slots)}。",
            followup_options=["/analyze", "补洞方向是什么"],
            runtime_path=RuntimePath.STATIC_CONTROL_RESPONSE,
        )

    def _general_chat_degraded_response(self, message: str) -> AdvisorResponse:
        return self._simple_response(
            (
                "我可以接这个问题，但当前没有可用 native Agent runtime，所以这里只能做保守降级。"
                "你可以补充具体精灵、队伍，或开启模型运行时后让我继续。"
            ),
            followup_options=["分析这队联防", "查询某只精灵的定位", "开启模型后继续这个问题"],
            runtime_path=RuntimePath.DETERMINISTIC_DEGRADED_FALLBACK,
        )

    def _simple_response(
        self,
        answer: str,
        *,
        followup_options: list[str],
        runtime_path: RuntimePath = RuntimePath.DETERMINISTIC_DEGRADED_FALLBACK,
    ) -> AdvisorResponse:
        return AdvisorResponse(
            backend=self.backend,
            runtime_path=runtime_path,
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
            (
                f"{slot.slot_index}:"
                f"{slot.nickname + ' ' if slot.nickname else ''}"
                f"{slot.primary_type}{'/' + slot.secondary_type if slot.secondary_type else ''}"
            )
            for slot in slots
        )

    def _team_answer_summary(
        self,
        report: Any,
        guard: TeamSemanticGuard,
        slots: tuple[TeamSlot, ...] | list[TeamSlot] = (),
    ) -> str:
        return _team_answer_summary(report, guard, slots)

    def _species_answer_summary(
        self,
        route: RouteDecision,
        profile: Any,
        moves: list[Any],
        semantics: dict[str, Any],
        mechanism_matches: list[MechanismMatch],
    ) -> str:
        if route.intent == Intent.COUNTERPLAY:
            return _counterplay_answer_summary(profile, moves, semantics, mechanism_matches)
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
