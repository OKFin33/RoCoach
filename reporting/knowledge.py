from __future__ import annotations

from battle_engine.contracts import TeamStructureReport
from reporting.contracts import ConfidenceTier, KnowledgeSnippet


CURATED_SNIPPETS = {
    "phase1_scope": KnowledgeSnippet(
        source_path="docs/domain_primer.md",
        topic="phase1_scope",
        confidence=ConfidenceTier.CONFIRMED,
        content=(
            "Phase 1 only covers attribute structure: defensive coverage, repeated weaknesses, "
            "missing resistances, STAB-only offensive coverage, and type-level patch directions."
        ),
    ),
    "patch_semantics": KnowledgeSnippet(
        source_path="specs/scoring_system.md",
        topic="patch_semantics",
        confidence=ConfidenceTier.CONFIRMED,
        content=(
            "Primary patch types are default single-attribute recommendations. "
            "Conditional dual patch types are follow-up options only if a suitable dual-type species exists."
        ),
    ),
    "dual_type_baseline": KnowledgeSnippet(
        source_path="docs/domain_primer.md",
        topic="dual_type_baseline",
        confidence=ConfidenceTier.PROVISIONAL,
        content=(
            "The project currently uses a provisional dual-type rule where double strength resolves to x3, "
            "double resistance resolves to 1/3, and opposing modifiers cancel to x1."
        ),
    ),
    "confidence_guard": KnowledgeSnippet(
        source_path="specs/report_confidence_policy.md",
        topic="confidence_guard",
        confidence=ConfidenceTier.CONFIRMED,
        content=(
            "High-confidence report claims must be grounded in deterministic Engine output. "
            "Meta and community statements must not be presented as confirmed fact."
        ),
    ),
    "switch_in_space": KnowledgeSnippet(
        source_path="docs/domain_primer.md",
        topic="switch_in_space",
        confidence=ConfidenceTier.PROVISIONAL,
        content=(
            "Repeated weaknesses and thin resistances generally imply limited switch-in space "
            "under the current project baseline."
        ),
    ),
}


class CuratedKnowledgeRetriever:
    """Small curated retrieval layer for the Phase 1.5 MVP."""

    def retrieve(self, report: TeamStructureReport) -> list[KnowledgeSnippet]:
        topics = {"phase1_scope", "confidence_guard"}
        if report.primary_patch_types or report.conditional_dual_patch_types:
            topics.add("patch_semantics")
        if report.repeated_weaknesses or report.missing_resistances:
            topics.add("switch_in_space")
        if report.conditional_dual_patch_types:
            topics.add("dual_type_baseline")

        return [CURATED_SNIPPETS[topic] for topic in sorted(topics)]

