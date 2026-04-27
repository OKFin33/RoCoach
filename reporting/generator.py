from __future__ import annotations

from typing import TYPE_CHECKING

from battle_engine.contracts import (
    DefensiveCoverageEntry,
    OffensiveCoverageEntry,
    TeamStructureReport,
    to_payload,
)
from reporting.contracts import (
    ConfidenceNote,
    ConfidenceTier,
    PatchGuidance,
    ReportRisk,
    ReportTakeaway,
    RiskSeverity,
    TeamNarrativeReport,
)

if TYPE_CHECKING:
    from reporting.contracts import KnowledgeSnippet


HIGH_STRUCTURE_THRESHOLD = 0.70
MID_STRUCTURE_THRESHOLD = 0.50
TOP_RISK_LIMIT = 3
TOP_TAKEAWAY_LIMIT = 2
TOP_ATTACKER_LIMIT = 2


class DeterministicReportGenerator:
    """Deterministic Phase 1.5 MVP report builder."""

    def generate(
        self,
        structure_report: TeamStructureReport,
        retrieved_snippets: list["KnowledgeSnippet"],
    ) -> TeamNarrativeReport:
        return TeamNarrativeReport(
            summary=self._build_summary(structure_report),
            major_risks=self._build_major_risks(structure_report),
            defensive_takeaways=self._build_defensive_takeaways(structure_report),
            offensive_takeaways=self._build_offensive_takeaways(structure_report),
            patch_guidance=self._build_patch_guidance(structure_report),
            evidence_summary=list(structure_report.evidence[:8]),
            confidence_notes=self._build_confidence_notes(retrieved_snippets),
        )

    def _build_summary(self, report: TeamStructureReport) -> str:
        structure_band = self._describe_structure_band(report.structural_score)
        risk_fragments = []
        critical = self._extract_overlap_values(report.overlap_notes, "critical_weaknesses")
        if critical:
            risk_fragments.append(f"关键承压点集中在{','.join(critical)}")
        if report.missing_resistances:
            risk_fragments.append(f"全队对{','.join(report.missing_resistances)}缺少稳定抗性")

        summary = (
            f"这支队伍当前的属性结构{structure_band}，structural score 为 {report.structural_score:.3f}。"
        )
        if risk_fragments:
            summary += " 主要问题是" + "；".join(risk_fragments) + "。"
        else:
            summary += " 当前没有出现特别突出的结构性断层。"
        return summary

    def _build_major_risks(self, report: TeamStructureReport) -> list[ReportRisk]:
        risks: list[ReportRisk] = []
        critical = self._extract_overlap_values(report.overlap_notes, "critical_weaknesses")
        thin = self._extract_overlap_values(report.overlap_notes, "thin_resistances")

        for attack_type in critical:
            risks.append(
                ReportRisk(
                    title=f"{attack_type}系关键弱点",
                    severity=RiskSeverity.HIGH,
                    explanation=f"{attack_type}系会对这队形成集中承压，当前换入空间偏紧。",
                    grounded_in=self._groundings_for(report, "critical_weaknesses"),
                )
            )
        for attack_type in report.missing_resistances:
            severity = RiskSeverity.HIGH if attack_type in critical else RiskSeverity.MEDIUM
            risks.append(
                ReportRisk(
                    title=f"{attack_type}系无抗性",
                    severity=severity,
                    explanation=f"当前结构对{attack_type}系没有稳定抗性，处理时更依赖主动节奏或对攻。",
                    grounded_in=self._groundings_for(report, "missing_resistances"),
                )
            )
        if thin:
            risks.append(
                ReportRisk(
                    title="抗性分布偏薄",
                    severity=RiskSeverity.MEDIUM,
                    explanation=f"{','.join(thin)}只有单点抗性，长线轮换时容错偏低。",
                    grounded_in=self._groundings_for(report, "thin_resistances"),
                )
            )

        if not risks and report.repeated_weaknesses:
            risks.append(
                ReportRisk(
                    title="重复弱点偏多",
                    severity=RiskSeverity.MEDIUM,
                    explanation=f"这队在{','.join(report.repeated_weaknesses[:4])}等方向存在重复承压。",
                    grounded_in=self._groundings_for(report, "repeated_weaknesses"),
                )
            )

        return risks[:TOP_RISK_LIMIT]

    def _build_defensive_takeaways(self, report: TeamStructureReport) -> list[ReportTakeaway]:
        takeaways: list[ReportTakeaway] = []
        stable_profiles = [
            entry.defending_type
            for entry in report.defensive_coverage
            if entry.resist_slots >= 3 and entry.weak_slots == 0
        ]
        if stable_profiles:
            takeaways.append(
                ReportTakeaway(
                    theme="稳定抗性区间",
                    explanation=f"对{','.join(stable_profiles[:4])}的承伤结构相对稳，作为轮换支点更容易找到安全落点。",
                    grounded_in=[self._format_coverage_entry(entry) for entry in report.defensive_coverage if entry.defending_type in stable_profiles[:4]],
                )
            )

        if report.repeated_weaknesses:
            takeaways.append(
                ReportTakeaway(
                    theme="联防洞口集中",
                    explanation=f"重复弱点覆盖到{','.join(report.repeated_weaknesses[:6])}，说明联防不是单点问题，而是整体承压链条偏脆。",
                    grounded_in=self._groundings_for(report, "repeated_weaknesses"),
                )
            )

        return takeaways[:TOP_TAKEAWAY_LIMIT]

    def _build_offensive_takeaways(self, report: TeamStructureReport) -> list[ReportTakeaway]:
        takeaways: list[ReportTakeaway] = []
        covered_targets = self._extract_offensive_targets(report)
        if covered_targets:
            takeaways.append(
                ReportTakeaway(
                    theme="STAB 打击面",
                    explanation=(
                        f"当前队伍的 STAB 属性至少能对 {len(covered_targets)} 个属性形成有效压制，"
                        "基础进攻覆盖不算窄。"
                    ),
                    grounded_in=self._groundings_for(report, "offensive_targets_covered"),
                )
            )

        strongest_attackers = sorted(
            report.offensive_coverage,
            key=lambda entry: (len(entry.super_effective_targets), -len(entry.resisted_targets)),
            reverse=True,
        )[:TOP_ATTACKER_LIMIT]
        if strongest_attackers:
            top_labels = ", ".join(
                f"{entry.attacker_type}({len(entry.super_effective_targets)})" for entry in strongest_attackers
            )
            takeaways.append(
                ReportTakeaway(
                    theme="主要压制属性",
                    explanation=f"从纯 STAB 视角看，当前最能提供覆盖的属性是 {top_labels}。",
                    grounded_in=[self._format_offensive_entry(entry) for entry in strongest_attackers],
                )
            )

        return takeaways[:TOP_TAKEAWAY_LIMIT]

    def _build_patch_guidance(self, report: TeamStructureReport) -> PatchGuidance:
        explanation_parts = []
        if report.primary_patch_types:
            explanation_parts.append(
                f"默认先从单属性补洞考虑：{', '.join(report.primary_patch_types)}。"
            )
        if report.conditional_dual_patch_types:
            explanation_parts.append(
                "如果存在合适的双属性精灵，可以再看："
                f"{', '.join(report.conditional_dual_patch_types)}。"
            )
        if not explanation_parts:
            explanation_parts.append("当前没有明显正收益的属性补洞方向。")

        constraints = [
            "Phase 1.5 仅基于属性结构，不包含具体精灵推荐。",
            "双属性方向是条件性建议，不应被视为强制配队结论。",
            "当前进攻覆盖按 STAB-only 口径解释。"
        ]

        return PatchGuidance(
            primary_patch_types=list(report.primary_patch_types),
            conditional_dual_patch_types=list(report.conditional_dual_patch_types),
            explanation=" ".join(explanation_parts),
            constraints=constraints,
        )

    def _build_confidence_notes(self, snippets: list["KnowledgeSnippet"]) -> list[ConfidenceNote]:
        notes = [
            ConfidenceNote(
                claim_scope="structure_analysis",
                confidence=ConfidenceTier.CONFIRMED,
                note="结构性结论直接来自 Phase 1 Engine 的确定性输出。",
            ),
            ConfidenceNote(
                claim_scope="dual_type_rule",
                confidence=ConfidenceTier.PROVISIONAL,
                note="双属性承伤解释仍基于当前项目的 provisional x3 / 1/3 规则。",
            ),
            ConfidenceNote(
                claim_scope="meta_scope",
                confidence=ConfidenceTier.LOW_CONFIDENCE,
                note="本报告不输出当前环境强结论，也不把社区观察视为硬事实。",
            ),
        ]
        if not any(snippet.topic == "dual_type_baseline" for snippet in snippets):
            return [note for note in notes if note.claim_scope != "dual_type_rule"]
        return notes

    def _describe_structure_band(self, score: float) -> str:
        if score >= HIGH_STRUCTURE_THRESHOLD:
            return "较稳"
        if score >= MID_STRUCTURE_THRESHOLD:
            return "中等"
        return "偏脆"

    def _groundings_for(self, report: TeamStructureReport, prefix: str) -> list[str]:
        grounded = [item for item in report.evidence if item.startswith(f"{prefix}=")]
        if grounded:
            return grounded
        grounded = [note for note in report.overlap_notes if note.startswith(f"{prefix}=")]
        return grounded or [f"{prefix}=none"]

    def _extract_overlap_values(self, notes: tuple[str, ...], prefix: str) -> list[str]:
        for note in notes:
            if note.startswith(f"{prefix}="):
                raw = note.split("=", 1)[1]
                return [part for part in raw.split(",") if part]
        return []

    def _extract_offensive_targets(self, report: TeamStructureReport) -> list[str]:
        for item in report.evidence:
            if item.startswith("offensive_targets_covered="):
                raw = item.split("=", 1)[1]
                return [part for part in raw.split(",") if part]
        return []

    def _format_coverage_entry(self, entry: DefensiveCoverageEntry) -> str:
        return (
            f"{entry.defending_type}: weak={entry.weak_slots} "
            f"resist={entry.resist_slots} neutral={entry.neutral_slots}"
        )

    def _format_offensive_entry(self, entry: OffensiveCoverageEntry) -> str:
        return (
            f"{entry.attacker_type}: strong={','.join(entry.super_effective_targets)} "
            f"resisted={','.join(entry.resisted_targets)}"
        )


class PydanticAIReportGenerator:
    """Optional LLM-backed generator using PydanticAI."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def generate(
        self,
        structure_report: TeamStructureReport,
        retrieved_snippets: list["KnowledgeSnippet"],
    ) -> TeamNarrativeReport:
        try:
            from pydantic_ai import Agent
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "pydantic-ai is not installed. Install `pydantic-ai` or "
                "`pydantic-ai-slim[openai]` before using the PydanticAI backend."
            ) from exc

        agent = Agent(
            self.model_name,
            output_type=TeamNarrativeReport,
            instructions=(
                "You are generating a grounded Roco World Phase 1.5 team report. "
                "Use only the provided Engine facts and curated snippets. "
                "Do not recommend specific species. "
                "Treat dual-type interpretation as provisional where relevant. "
                "Do not make hard meta claims."
            ),
        )
        prompt = self._build_prompt(structure_report, retrieved_snippets)
        result = agent.run_sync(prompt)
        return result.output

    def _build_prompt(
        self,
        structure_report: TeamStructureReport,
        retrieved_snippets: list["KnowledgeSnippet"],
    ) -> str:
        snippet_lines = "\n".join(
            f"- [{snippet.confidence}] {snippet.topic} ({snippet.source_path}): {snippet.content}"
            for snippet in retrieved_snippets
        )
        return (
            "Generate a structured Phase 1.5 team analysis report.\n\n"
            f"Engine payload:\n{to_payload(structure_report)}\n\n"
            f"Curated snippets:\n{snippet_lines}\n"
        )
