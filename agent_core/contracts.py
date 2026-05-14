from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from reporting.contracts import ConfidenceTier


class AgentResponseStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    REFUSED = "refused"
    FAILED = "failed"


class AgentRuntimePath(StrEnum):
    NATIVE_LLM_TERMINAL = "native_llm_terminal"
    DETERMINISTIC_DEGRADED_FALLBACK = "deterministic_degraded_fallback"
    STATIC_CONTROL_RESPONSE = "static_control_response"


class AnalysisType(StrEnum):
    CHAT_RESPONSE = "chat_response"
    TEAM_ANALYSIS = "team_analysis"
    SPECIES_ANALYSIS = "species_analysis"
    SESSION_COMMAND = "session_command"
    UNSUPPORTED = "unsupported"
    RUNTIME_FAILURE = "runtime_failure"
    UNKNOWN = "unknown"


class EvidenceItem(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    source_type: str
    source_label: str
    confidence: ConfidenceTier
    content: str
    retrieval_reason: str


class AgentToolResult(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    tool_name: str
    status: AgentResponseStatus
    summary: str
    evidence_refs: list[str]
    payload: dict[str, Any] | None = None


class ConfidenceNote(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    claim_scope: str
    confidence: ConfidenceTier
    note: str


class FollowupOption(BaseModel):
    id: str
    label: str
    action: str | None = None


class SynthesisWarningSeverity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SynthesisWarning(BaseModel):
    code: str
    severity: SynthesisWarningSeverity
    message: str


class DetailSectionVisibility(StrEnum):
    COLLAPSED = "collapsed"
    EXPANDED = "expanded"


class DetailSectionContentKind(StrEnum):
    EVIDENCE = "evidence"
    CONFIDENCE = "confidence"
    TOOL_TRACE = "tool_trace"
    ANALYTICAL_BASE = "analytical_base"
    FOLLOWUP = "followup"
    RAW = "raw"


class DoctrineMentalModel(BaseModel):
    name: str
    description: str
    use_when: list[str]


class DoctrineDecisionHeuristic(BaseModel):
    rule: str
    rationale: str
    preferred_scope: list[str]


class DoctrineHonestyBoundary(BaseModel):
    trigger: str
    required_behavior: str


class DoctrinePack(BaseModel):
    doctrine_id: str
    mental_models: list[DoctrineMentalModel]
    decision_heuristics: list[DoctrineDecisionHeuristic]
    anti_patterns: list[str]
    honesty_boundaries: list[DoctrineHonestyBoundary]


class AnalyticalSubstrate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    schema_version: str = "analytical_substrate.v1"
    status: AgentResponseStatus
    backend: str
    analysis_type: AnalysisType
    answer_summary: str
    tool_results: list[AgentToolResult]
    evidence: list[EvidenceItem]
    confidence_notes: list[ConfidenceNote]
    followup_options: list[FollowupOption]


class SynthesisInput(BaseModel):
    analytical_substrate: AnalyticalSubstrate
    doctrine_pack: DoctrinePack


class SynthesisResult(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    synthesis_version: str
    synthesized_judgement: str
    why_summary: str
    surfaced_warnings: list[SynthesisWarning]
    followup_directions: list[str]
    grounding_refs: list[str]
    doctrine_refs: list[str]


class ExpressionDNA(BaseModel):
    tone: str
    pacing: str
    wording_preferences: list[str]
    signature_moves: list[str]
    taboo_phrases: list[str]


class PersonaRenderingFlavorRule(BaseModel):
    id: str
    trigger_terms: list[str] = Field(default_factory=list)
    allowed_effects: list[str] = Field(default_factory=list)
    forbidden_effects: list[str] = Field(default_factory=list)
    style_hint: str


class PersonaMentalModel(BaseModel):
    name: str
    description: str
    use_when: list[str]


class PersonaDecisionHeuristic(BaseModel):
    rule: str
    rationale: str
    preferred_scope: list[str]


class PersonaHonestyBoundary(BaseModel):
    trigger: str
    required_behavior: str


class PersonaIPSafetyProfile(BaseModel):
    public_safe: bool
    forbidden_markers: list[str]


class PersonaProfile(BaseModel):
    persona_id: str
    display_name: str
    expression_dna: ExpressionDNA
    rendering_flavor_rules: list[PersonaRenderingFlavorRule] = Field(default_factory=list)
    mental_models: list[PersonaMentalModel]
    decision_heuristics: list[PersonaDecisionHeuristic]
    anti_patterns: list[str]
    honesty_boundaries: list[PersonaHonestyBoundary]
    facts_locked: bool = True
    fact_policy: str = "persona_may_not_alter_facts"
    ip_safety_profile: PersonaIPSafetyProfile


class PersonaSourceAdapterKind(StrEnum):
    DISTILL_FROM_EXISTING_SUBJECT = "distill_from_existing_subject"
    DESIGN_FROM_ZERO = "design_from_zero"


class PersonaSourceRunMode(StrEnum):
    INTERNAL_ONLY = "internal_only"
    REVIEW_CANDIDATE = "review_candidate"


class PersonaSourceArtifactKind(StrEnum):
    DISTILLATION_OR_DESIGN_MEMO = "distillation_or_design_memo"
    NORMALIZED_PERSONA_DOCTRINE_DRAFT = "normalized_persona_doctrine_draft"
    MAPPING_OR_USAGE_NOTE = "mapping_or_usage_note"
    PROVENANCE_METADATA = "provenance_metadata"


class PersonaSourceAdapterRequest(BaseModel):
    target_subject: str
    public_source_scope: list[str] = Field(min_length=1)
    run_mode: PersonaSourceRunMode = PersonaSourceRunMode.INTERNAL_ONLY
    stage_label: str = "P1d Persona Source Adapter"


class PersonaSourceProvenance(BaseModel):
    adapter_id: str
    adapter_kind: PersonaSourceAdapterKind
    run_mode: PersonaSourceRunMode
    source_summary: list[str] = Field(min_length=1)
    target_subject: str
    public_source_scope: list[str] = Field(min_length=1)
    stage_label: str
    source_material_refs: list[str] = Field(min_length=1)


class PersonaSourceArtifactRef(BaseModel):
    artifact_kind: PersonaSourceArtifactKind
    path: Path
    contract_target: str | None = None


class PersonaSourceArtifactBundle(BaseModel):
    bundle_version: str = "persona_source_bundle.v1"
    adapter_id: str
    adapter_kind: PersonaSourceAdapterKind
    run_mode: PersonaSourceRunMode
    output_root: Path
    memo: PersonaSourceArtifactRef
    doctrine_draft: PersonaSourceArtifactRef
    mapping_note: PersonaSourceArtifactRef
    provenance_metadata: PersonaSourceArtifactRef
    provenance: PersonaSourceProvenance
    runtime_activation_requested: bool = False
    registry_write_requested: bool = False


class PersonaArtifactAdmissionStatus(StrEnum):
    REJECTED = "rejected"
    REVIEW_REQUIRED = "review_required"
    INTERNAL_ONLY = "internal_only"
    REVIEW_READY = "review_ready"
    PUBLIC_SAFE = "public_safe"


class PersonaArtifactValidationStep(StrEnum):
    SCHEMA_VALIDATION = "schema_validation"
    PROVENANCE_PRESENCE_CHECK = "provenance_presence_check"
    REASONING_RENDERING_SPLIT_CHECK = "reasoning_rendering_split_check"
    HONESTY_BOUNDARY_PRESENCE_CHECK = "honesty_boundary_presence_check"
    FACT_POLICY_CHECK = "fact_policy_check"
    IP_SAFETY_REVIEW = "ip_safety_review"
    RUNTIME_SCOPE_REVIEW = "runtime_scope_review"


class PersonaArtifactValidationFinding(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    step: PersonaArtifactValidationStep
    code: str
    message: str
    blocking: bool


class PersonaArtifactRegistryMetadata(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    persona_id: str
    version: str
    status: PersonaArtifactAdmissionStatus
    source_adapter_id: str
    doctrine_ref: str
    provenance_ref: str
    mapping_note_ref: str
    supported_analysis_types: list[str]
    public_safe: bool


class PersonaArtifactIngestionResult(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    ingestion_version: str = "persona_artifact_ingestion.v1"
    status: PersonaArtifactAdmissionStatus
    registry_metadata: PersonaArtifactRegistryMetadata
    findings: list[PersonaArtifactValidationFinding]
    admitted: bool
    public_safe_approved: bool = False


class PersonaRegistryReviewState(StrEnum):
    REJECTED = "rejected"
    REVIEW_REQUIRED = "review_required"
    INTERNAL_ONLY = "internal_only"
    REVIEW_READY = "review_ready"
    PUBLIC_SAFE = "public_safe"


class PersonaRegistryCandidate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    candidate_version: str = "persona_registry_candidate.v1"
    persona_id: str
    version: str
    admission_status: PersonaArtifactAdmissionStatus
    review_state: PersonaRegistryReviewState
    source_adapter_id: str
    doctrine_ref: str
    provenance_ref: str
    mapping_note_ref: str
    supported_analysis_types: list[str]
    ingestion_version: str
    ingestion_admitted: bool
    public_safe: bool
    public_safe_approved: bool
    internal_only: bool
    runtime_selectable: bool = False
    review_finding_codes: list[str]


class PersonaRegistryStoredRecord(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    record_version: str = "persona_registry_record.v1"
    persona_id: str
    version: str
    revision: int = Field(ge=1)
    candidate: PersonaRegistryCandidate
    ingestion_evidence: PersonaArtifactIngestionResult
    admission_status: PersonaArtifactAdmissionStatus
    review_state: PersonaRegistryReviewState
    public_safe: bool
    public_safe_approved: bool
    runtime_selectable: bool = False
    review_finding_codes: list[str]


class PersonaRegistryLedger(BaseModel):
    registry_version: str = "persona_registry_ledger.v1"
    records: list[PersonaRegistryStoredRecord] = Field(default_factory=list)


class PersonaRuntimeActivationStatus(StrEnum):
    ELIGIBLE = "eligible"
    BLOCKED = "blocked"


class PersonaRuntimeActivationScope(StrEnum):
    INTERNAL_ONLY_RUNTIME = "internal_only_runtime"
    PUBLIC_SAFE_RELEASE = "public_safe_release"


class PersonaRuntimeActivationEvidenceRefs(BaseModel):
    source_adapter_id: str
    doctrine_ref: str
    provenance_ref: str
    mapping_note_ref: str
    ingestion_version: str
    review_finding_codes: list[str]


class PersonaRuntimeActivationDecision(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    activation_version: str = "persona_runtime_activation_gate.v1"
    persona_id: str
    version: str
    revision: int = Field(ge=1)
    requested_scope: PersonaRuntimeActivationScope
    status: PersonaRuntimeActivationStatus
    admission_status: PersonaArtifactAdmissionStatus
    review_state: PersonaRegistryReviewState
    public_safe: bool
    public_safe_approved: bool
    internal_only: bool
    eligible_for_internal_runtime: bool
    eligible_for_public_release: bool
    runtime_selectable: bool = False
    evidence_refs: PersonaRuntimeActivationEvidenceRefs
    blocked_reasons: list[str]


class PersonaRuntimeActivationReport(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    activation_version: str = "persona_runtime_activation_gate.v1"
    requested_scope: PersonaRuntimeActivationScope
    decisions: list[PersonaRuntimeActivationDecision] = Field(default_factory=list)


class PersonaActivationProjectionEntry(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    projection_entry_version: str = "persona_activation_projection_entry.v1"
    persona_id: str
    version: str
    revision: int = Field(ge=1)
    activation_scope: PersonaRuntimeActivationScope
    admission_status: PersonaArtifactAdmissionStatus
    review_state: PersonaRegistryReviewState
    public_safe: bool
    public_safe_approved: bool
    internal_only: bool
    eligible_for_internal_runtime: bool
    eligible_for_public_release: bool
    projected_runtime_entry: bool = True
    evidence_refs: PersonaRuntimeActivationEvidenceRefs


class PersonaActivationProjectionBlockedSummary(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    persona_id: str
    version: str
    revision: int = Field(ge=1)
    activation_scope: PersonaRuntimeActivationScope
    admission_status: PersonaArtifactAdmissionStatus
    review_state: PersonaRegistryReviewState
    public_safe: bool
    public_safe_approved: bool
    internal_only: bool
    evidence_refs: PersonaRuntimeActivationEvidenceRefs
    blocked_reasons: list[str]


class PersonaActivationRegistryProjection(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    projection_version: str = "persona_activation_registry_projection.v1"
    activation_version: str
    requested_scope: PersonaRuntimeActivationScope
    entries: list[PersonaActivationProjectionEntry] = Field(default_factory=list)
    blocked_decision_summaries: list[PersonaActivationProjectionBlockedSummary] = Field(default_factory=list)


class MaterializedPersonaSynthesisProfile(BaseModel):
    mental_models: list[PersonaMentalModel]
    decision_heuristics: list[PersonaDecisionHeuristic]
    anti_patterns: list[str]
    honesty_boundaries: list[PersonaHonestyBoundary]
    facts_locked: bool
    fact_policy: str


class MaterializedPersonaRenderingProfile(BaseModel):
    display_name: str
    expression_dna: ExpressionDNA
    rendering_flavor_rules: list[PersonaRenderingFlavorRule] = Field(default_factory=list)


class MaterializedPersonaPolicyProfile(BaseModel):
    public_safe: bool
    public_safe_approved: bool
    internal_only: bool
    eligible_for_internal_runtime: bool
    eligible_for_public_release: bool
    ip_safety_profile: PersonaIPSafetyProfile


class MaterializedPersonaProfileArtifact(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    materialized_profile_version: str = "persona_materialized_profile.v1"
    persona_id: str
    version: str
    revision: int = Field(ge=1)
    activation_scope: PersonaRuntimeActivationScope
    projection_entry_version: str
    synthesis_profile: MaterializedPersonaSynthesisProfile
    rendering_profile: MaterializedPersonaRenderingProfile
    policy_profile: MaterializedPersonaPolicyProfile
    evidence_refs: PersonaRuntimeActivationEvidenceRefs


class PersonaProjectionProfileMaterialization(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    materialization_version: str = "persona_projection_profile_materialization.v1"
    projection_version: str
    requested_scope: PersonaRuntimeActivationScope
    profiles: list[MaterializedPersonaProfileArtifact] = Field(default_factory=list)
    blocked_decision_summaries: list[PersonaActivationProjectionBlockedSummary] = Field(default_factory=list)


class PersonaProfileResolutionSource(StrEnum):
    BUILT_IN = "built_in"
    MATERIALIZED_PROFILE = "materialized_profile"
    PUBLIC_SAFE_FALLBACK = "public_safe_fallback"


class PersonaProfileResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    FALLBACK_SANITIZED = "fallback_sanitized"


class PersonaProfileResolverResult(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    resolution_version: str = "persona_profile_resolver.v1"
    requested_selector: str | None = None
    requested_persona_id: str | None = None
    requested_version: str | None = None
    requested_revision: int | None = None
    resolved_persona_id: str
    source: PersonaProfileResolutionSource
    status: PersonaProfileResolutionStatus
    sanitized: bool
    sanitized_reason: str | None = None
    activation_scope: PersonaRuntimeActivationScope | None = None
    profile: PersonaProfile


class PresentationInput(BaseModel):
    analytical_substrate: AnalyticalSubstrate
    synthesis: SynthesisResult


class VisibleWarning(BaseModel):
    code: str
    severity: SynthesisWarningSeverity
    message: str


class DetailSection(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    section_id: str
    label: str
    default_visibility: DetailSectionVisibility
    content_kind: DetailSectionContentKind
    content: str


class PresentationMetadata(BaseModel):
    persona_id: str | None = None
    facts_locked: bool
    fact_policy: str
    source_contract: str


class PresentationResult(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    presentation_version: str
    reply: str
    why: str
    visible_warnings: list[VisibleWarning]
    detail_sections: list[DetailSection]
    followup_prompts: list[str]
    presentation_metadata: PresentationMetadata


class PersonaRenderInput(BaseModel):
    requested_persona_id: str | None = None
    effective_persona: PersonaProfile
    canonical_answer: str
    presentation: PresentationResult | None = None


class PersonaEnvelope(BaseModel):
    persona_id: str | None = None
    display_name: str | None = None
    display_style: str | None = None
    rendered_answer: str | None = None
    rendering_flavor_rule_ids: list[str] = Field(default_factory=list)
    facts_locked: bool = True
    fact_policy: str = "persona_may_not_alter_facts"
    public_safe: bool = True
    sanitized: bool = False
    render_contract: str | None = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    schema_version: str = "agent_response.v1"
    status: AgentResponseStatus
    backend: str
    runtime_path: AgentRuntimePath = AgentRuntimePath.DETERMINISTIC_DEGRADED_FALLBACK
    continuity_persisted: bool = True
    analysis_type: AnalysisType
    answer: str
    tool_results: list[AgentToolResult]
    evidence: list[EvidenceItem]
    confidence_notes: list[ConfidenceNote]
    followup_options: list[FollowupOption]
    synthesis: SynthesisResult | None = Field(
        default=None,
        description="Optional synthesis payload that carries the reasoning layer result.",
    )
    presentation: PresentationResult | None = Field(
        default=None,
        description="Optional presentation payload that carries the product-facing response surface.",
    )
    persona: PersonaEnvelope | None = Field(
        default=None,
        description="Optional presentation envelope. It must not alter factual response fields.",
    )
