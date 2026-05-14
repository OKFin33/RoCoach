from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from reporting.contracts import ConfidenceTier


class SourceType(StrEnum):
    ENGINE = "engine"
    FACT = "fact"
    DOC = "doc"
    CASE = "case"


class ToolStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    REFUSED = "refused"
    FAILED = "failed"


class RuntimePath(StrEnum):
    NATIVE_LLM_TERMINAL = "native_llm_terminal"
    DETERMINISTIC_DEGRADED_FALLBACK = "deterministic_degraded_fallback"
    STATIC_CONTROL_RESPONSE = "static_control_response"


class TopicSourceType(StrEnum):
    USER_MENTION = "user_mention"
    TEAM_SETTING = "team_setting"
    TOOL_RESOLUTION = "tool_resolution"
    SUMMARY = "summary"
    ACTIVE_FOCUS = "active_focus"


class TopicFocusType(StrEnum):
    NONE = "none"
    SINGLE_SPECIES = "single_species"
    RELATION = "relation"
    TEAM_CORE = "team_core"
    AMBIGUOUS = "ambiguous"


class GroundingIntent(StrEnum):
    GENERAL_CHAT = "general_chat"
    SPECIES_QUERY = "species_query"
    COUNTERPLAY = "counterplay"
    RELATION_QUERY = "relation_query"
    TEAM_ANALYSIS = "team_analysis"
    CLARIFICATION = "clarification"
    STATIC_CONTROL = "static_control"


class SubjectResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    PARTIAL = "partial"
    AMBIGUOUS = "ambiguous"
    MISSING = "missing"


class GroundingToolCallStatus(StrEnum):
    OK = "ok"
    REFUSED = "refused"
    FAILED = "failed"
    SKIPPED = "skipped"


class MissingEvidenceKind(StrEnum):
    SUBJECT = "subject"
    TEAM_CONTEXT = "team_context"
    MECHANISM_DOC = "mechanism_doc"
    CASE_LAYER = "case_layer"
    PROVIDER = "provider"


class MissingEvidenceSeverity(StrEnum):
    INFO = "info"
    DEGRADE = "degrade"
    CLARIFY = "clarify"
    FAIL_CLOSED = "fail_closed"


class ConfidenceFloor(StrEnum):
    CONFIRMED = "confirmed"
    PROVISIONAL = "provisional"
    UNSUPPORTED = "unsupported"


class ClarificationState(StrEnum):
    NOT_NEEDED = "not_needed"
    NEEDED = "needed"
    ASKED = "asked"


class DexBaseStats(BaseModel):
    hp: int
    atk: int
    defense: int
    spa: int
    spd: int
    spe: int

    @property
    def bst(self) -> int:
        return self.hp + self.atk + self.defense + self.spa + self.spd + self.spe


class SpeciesDexRecord(BaseModel):
    species_id: str
    display_name: str
    initial_species_name: str | None = None
    form_name: str | None = None
    regional_form_name: str | None = None
    evolution_stage: str | None = None
    primary_type: str
    secondary_type: str | None = None
    base_stats: DexBaseStats
    ability_name: str | None = None
    ability_effect_text: str | None = None
    confidence: ConfidenceTier
    canonical_source_layer: str
    source_page_id: str
    import_run_id: str


class SpeciesSearchHit(BaseModel):
    species_id: str
    display_name: str
    initial_species_name: str | None = None
    form_name: str | None = None
    regional_form_name: str | None = None
    primary_type: str
    secondary_type: str | None = None


class MoveDexRecord(BaseModel):
    move_id: str
    move_name: str
    move_type: str | None = None
    category_raw: str | None = None
    power: int | None = None
    energy_cost: int | None = None
    effect_text: str | None = None
    description_text: str | None = None
    confidence: ConfidenceTier
    canonical_source_layer: str


class AbilityDexRecord(BaseModel):
    ability_id: str
    ability_name: str
    effect_text: str
    confidence: ConfidenceTier
    canonical_source_layer: str
    derivation_status: str | None = None


class SpeciesMoveRecord(BaseModel):
    species_id: str
    move_id: str | None = None
    move_name: str
    move_type: str | None = None
    category_raw: str | None = None
    access_channel: str
    unlock_level: int | None = None
    power: int | None = None
    effect_text: str | None = None


class DocContextSnippet(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    source_path: str
    topic: str
    confidence: ConfidenceTier
    content: str
    retrieval_reason: str
    version: str = "2026-04-15"


class AdvisorEvidenceItem(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    source_type: SourceType
    source_label: str
    confidence: ConfidenceTier
    content: str
    retrieval_reason: str


class AdvisorToolResult(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    tool_name: str
    status: ToolStatus = ToolStatus.OK
    summary: str
    payload: dict[str, Any] | None = None


class TeamCoherenceVerdict(StrEnum):
    COHERENT = "coherent"
    PARTIALLY_COHERENT = "partially_coherent"
    GOODSTUFF_WITHOUT_CLEAR_PLAN = "goodstuff_without_clear_plan"
    INTERNALLY_CONFLICTED = "internally_conflicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class TeamSemanticGuard(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    unknown_quality_team: bool = True
    candidate_plan: str
    supporting_evidence: list[str]
    counterevidence: list[str]
    coherence_verdict: TeamCoherenceVerdict
    coherence_score: float


class AdvisorResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    backend: str
    runtime_path: RuntimePath = RuntimePath.DETERMINISTIC_DEGRADED_FALLBACK
    continuity_persisted: bool = True
    answer_summary: str
    tool_results: list[AdvisorToolResult]
    evidence_summary: list[AdvisorEvidenceItem]
    confidence_notes: list[str]
    followup_options: list[str]


class TopicSourceRecord(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    source_type: TopicSourceType
    turn_id: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: str
    updated_at: str


class ConversationTopicSpecies(BaseModel):
    canonical_species_id: str
    display_name: str
    canonical_name: str | None = None
    aliases: list[str] = Field(default_factory=list)
    role_hints: list[str] = Field(default_factory=list)
    source_records: list[TopicSourceRecord] = Field(default_factory=list)
    mention_count: int = Field(default=1, ge=0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    last_mentioned_at: str


class ConversationTopicRelation(BaseModel):
    relation_edge_id: str
    from_species_id: str
    to_species_id: str
    relation_kind: str = "related"
    from_role_hint: str | None = None
    to_role_hint: str | None = None
    source_records: list[TopicSourceRecord] = Field(default_factory=list)
    mention_count: int = Field(default=1, ge=0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    last_mentioned_at: str


class ConversationActiveFocus(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    focus_type: TopicFocusType = TopicFocusType.NONE
    subject_species_ids: list[str] = Field(default_factory=list)
    subject_display_names: list[str] = Field(default_factory=list)
    relation_edge_id: str | None = None
    from_species_id: str | None = None
    to_species_id: str | None = None
    from_role_hint: str | None = None
    to_role_hint: str | None = None
    anchor_turn_id: str | None = None
    updated_turn_id: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ConversationTopicPool(BaseModel):
    species: list[ConversationTopicSpecies] = Field(default_factory=list)
    relations: list[ConversationTopicRelation] = Field(default_factory=list)
    active_focus: ConversationActiveFocus = Field(default_factory=ConversationActiveFocus)


class GroundingSubject(BaseModel):
    canonical_species_id: str | None = None
    display_name: str | None = None
    resolution_status: SubjectResolutionStatus
    role_hint: str | None = None


class GroundingToolCall(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    tool_name: str
    status: GroundingToolCallStatus
    evidence_ids: list[str] = Field(default_factory=list)


class GroundingEvidenceItem(BaseModel):
    evidence_id: str
    source_type: SourceType
    source_label: str
    content_digest: str
    confidence: ConfidenceTier


class TopicPoolDelta(BaseModel):
    species_ids_added_or_updated: list[str] = Field(default_factory=list)
    relation_edge_ids_added_or_updated: list[str] = Field(default_factory=list)
    active_focus_type: TopicFocusType = TopicFocusType.NONE


class GroundingClaimSupport(BaseModel):
    claim_id: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    support_level: ConfidenceFloor
    provisional_reason: str | None = None


class GroundingMissingEvidence(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    kind: MissingEvidenceKind
    severity: MissingEvidenceSeverity
    repair_path: str


class GroundingPacket(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    intent: GroundingIntent
    subjects: list[GroundingSubject] = Field(default_factory=list)
    evidence_items: list[GroundingEvidenceItem] = Field(default_factory=list)
    tool_calls: list[GroundingToolCall] = Field(default_factory=list)
    claim_support: list[GroundingClaimSupport] = Field(default_factory=list)
    topic_pool_delta: TopicPoolDelta = Field(default_factory=TopicPoolDelta)
    missing_evidence: list[GroundingMissingEvidence] = Field(default_factory=list)
    confidence_floor: ConfidenceFloor = ConfidenceFloor.PROVISIONAL
    clarification_state: ClarificationState = ClarificationState.NOT_NEEDED


class AdvisorTurnSummary(BaseModel):
    turn_id: str
    user_message: str = ""
    user_message_excerpt: str = ""
    user_message_digest: str = ""
    intent_digest: str = ""
    route_intent: str
    resolved_subject: str | None = None
    answer_digest: str
    grounding_refs: list[str] = Field(default_factory=list)
    tool_names: list[str] = Field(default_factory=list)
    backend: str
    created_at: str


class AdvisorSessionState(BaseModel):
    current_team: list[dict[str, Any]] = Field(default_factory=list)
    current_species_context: str | None = None
    user_constraints: list[str] = Field(default_factory=list)
    last_analysis_type: str | None = None
    last_result_ref: str | None = None
    pending_followup_targets: list[str] = Field(default_factory=list)
    recent_turn_summaries: list[AdvisorTurnSummary] = Field(default_factory=list, max_length=12)
    conversation_topic_pool: ConversationTopicPool = Field(default_factory=ConversationTopicPool)
    native_model_messages: list[Any] = Field(default_factory=list, exclude=True)
    native_runtime_fingerprint: str | None = Field(default=None, exclude=True)
