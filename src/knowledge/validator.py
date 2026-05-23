from __future__ import annotations

from engine.contracts import TeamStructureReport
from knowledge.contracts import ConfidenceTier, TeamNarrativeReport


class ReportValidationError(ValueError):
    """Raised when a generated report violates report-layer policy."""


class ReportValidator:
    def validate(self, report: TeamNarrativeReport, structure_report: TeamStructureReport) -> None:
        evidence_set = set(structure_report.evidence) | set(structure_report.overlap_notes)

        for risk in report.major_risks:
            if not risk.grounded_in:
                raise ReportValidationError(f"Risk `{risk.title}` is missing grounding.")
            for grounding in risk.grounded_in:
                if grounding not in evidence_set and not grounding.endswith(": none"):
                    raise ReportValidationError(
                        f"Risk `{risk.title}` references unknown grounding `{grounding}`."
                    )

        all_text = " ".join(
            [
                report.summary,
                *[item.explanation for item in report.major_risks],
                *[item.explanation for item in report.defensive_takeaways],
                *[item.explanation for item in report.offensive_takeaways],
                report.patch_guidance.explanation,
                *report.patch_guidance.constraints,
                *[item.note for item in report.confidence_notes],
            ]
        )

        forbidden_species_tokens = ("替换成", "must replace", "推荐精灵", "species")
        if any(token in all_text for token in forbidden_species_tokens):
            raise ReportValidationError("Phase 1.5 report must not make species-level recommendations.")

        if "meta" in all_text.lower() or "环境" in all_text:
            low_confidence_notes = [
                item for item in report.confidence_notes if item.confidence == ConfidenceTier.LOW_CONFIDENCE
            ]
            if not low_confidence_notes:
                raise ReportValidationError("Meta-scoped language requires an explicit low-confidence note.")

