from __future__ import annotations

from typing import Iterable

from battle_engine.contracts import AnalysisGoals, TeamAnalysisRequest, TeamSlot
from battle_engine.team_structure import TeamStructureAnalyzer
from reporting.contracts import Phase15AnalysisResult
from reporting.generator import DeterministicReportGenerator, PydanticAIReportGenerator
from reporting.knowledge import CuratedKnowledgeRetriever
from reporting.validator import ReportValidator


class Phase15ReportService:
    def __init__(
        self,
        analyzer: TeamStructureAnalyzer | None = None,
        retriever: CuratedKnowledgeRetriever | None = None,
        validator: ReportValidator | None = None,
    ) -> None:
        self.analyzer = analyzer or TeamStructureAnalyzer()
        self.retriever = retriever or CuratedKnowledgeRetriever()
        self.validator = validator or ReportValidator()

    def analyze(
        self,
        slots_or_request: TeamAnalysisRequest | Iterable[TeamSlot],
        *,
        backend: str = "deterministic",
        model_name: str | None = None,
        goals: AnalysisGoals | None = None,
    ) -> Phase15AnalysisResult:
        if isinstance(slots_or_request, TeamAnalysisRequest):
            request = slots_or_request
        else:
            request = TeamAnalysisRequest(slots=tuple(slots_or_request), goals=goals or AnalysisGoals())

        structure_report = self.analyzer.analyze(request)
        snippets = self.retriever.retrieve(structure_report)

        if backend == "deterministic":
            narrative_report = DeterministicReportGenerator().generate(structure_report, snippets)
        elif backend == "pydantic_ai":
            if not model_name:
                raise ValueError("model_name is required when backend='pydantic_ai'")
            narrative_report = PydanticAIReportGenerator(model_name=model_name).generate(
                structure_report,
                snippets,
            )
        else:
            raise ValueError(f"Unsupported backend: {backend}")

        self.validator.validate(narrative_report, structure_report)
        return Phase15AnalysisResult.from_reports(
            backend=backend,
            structure_report=structure_report,
            narrative_report=narrative_report,
            retrieved_snippets=snippets,
        )

