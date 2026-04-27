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
    answer_summary: str
    tool_results: list[AdvisorToolResult]
    evidence_summary: list[AdvisorEvidenceItem]
    confidence_notes: list[str]
    followup_options: list[str]


class AdvisorSessionState(BaseModel):
    current_team: list[dict[str, Any]] = Field(default_factory=list)
    current_species_context: str | None = None
    user_constraints: list[str] = Field(default_factory=list)
    last_analysis_type: str | None = None
    last_result_ref: str | None = None
    pending_followup_targets: list[str] = Field(default_factory=list)
