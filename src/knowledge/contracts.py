from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from engine.contracts import TeamStructureReport, to_payload


class RiskSeverity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceTier(StrEnum):
    CONFIRMED = "confirmed"
    PROVISIONAL = "provisional"
    LOW_CONFIDENCE = "low_confidence"


class ReportRisk(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    title: str
    severity: RiskSeverity
    explanation: str
    grounded_in: list[str]


class ReportTakeaway(BaseModel):
    theme: str
    explanation: str
    grounded_in: list[str]


class PatchGuidance(BaseModel):
    primary_patch_types: list[str]
    conditional_dual_patch_types: list[str]
    explanation: str
    constraints: list[str]


class ConfidenceNote(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    claim_scope: str
    confidence: ConfidenceTier
    note: str


class KnowledgeSnippet(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    source_path: str
    topic: str
    confidence: ConfidenceTier
    content: str


class TeamNarrativeReport(BaseModel):
    summary: str
    major_risks: list[ReportRisk]
    defensive_takeaways: list[ReportTakeaway]
    offensive_takeaways: list[ReportTakeaway]
    patch_guidance: PatchGuidance
    evidence_summary: list[str]
    confidence_notes: list[ConfidenceNote]


class Phase15AnalysisResult(BaseModel):
    backend: str
    structure_report: dict[str, Any] = Field(description="Serialized TeamStructureReport payload.")
    narrative_report: TeamNarrativeReport
    retrieved_snippets: list[KnowledgeSnippet]

    @classmethod
    def from_reports(
        cls,
        *,
        backend: str,
        structure_report: TeamStructureReport,
        narrative_report: TeamNarrativeReport,
        retrieved_snippets: list[KnowledgeSnippet],
    ) -> "Phase15AnalysisResult":
        return cls(
            backend=backend,
            structure_report=to_payload(structure_report),
            narrative_report=narrative_report,
            retrieved_snippets=retrieved_snippets,
        )

