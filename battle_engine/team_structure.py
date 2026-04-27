from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

from battle_engine.contracts import (
    AnalysisGoals,
    DefensiveCoverageEntry,
    OffensiveCoverageEntry,
    TeamAnalysisRequest,
    TeamSlot,
    TeamStructureReport,
)
from roco_world_model import RocoWorldTypeChart


@dataclass(frozen=True)
class StructureScoreBreakdown:
    defensive_resilience: float
    offensive_coverage: float
    resistance_redundancy: float
    role_flex_placeholder: float
    weakness_penalty: float
    structural_score: float


class TeamStructureAnalyzer:
    def __init__(self, chart: RocoWorldTypeChart | None = None) -> None:
        self.chart = chart or RocoWorldTypeChart()

    def analyze(
        self,
        slots_or_request: TeamAnalysisRequest | Iterable[TeamSlot],
        goals: AnalysisGoals | None = None,
    ) -> TeamStructureReport:
        if isinstance(slots_or_request, TeamAnalysisRequest):
            request = slots_or_request
        else:
            request = TeamAnalysisRequest(slots=tuple(slots_or_request), goals=goals or AnalysisGoals())

        slots = request.slots
        if not slots:
            raise ValueError("At least one team slot is required")

        defensive_coverage = self._build_defensive_coverage(slots)
        offensive_coverage = self._build_offensive_coverage(slots)

        repeated_weaknesses = tuple(
            entry.defending_type for entry in defensive_coverage if entry.weak_slots >= 2
        )
        critical_weaknesses = tuple(
            entry.defending_type for entry in defensive_coverage if entry.weak_slots >= 3
        )
        missing_resistances = tuple(
            entry.defending_type for entry in defensive_coverage if entry.resist_slots == 0
        )
        thin_resistances = tuple(
            entry.defending_type for entry in defensive_coverage if entry.resist_slots == 1
        )

        breakdown = self._score_structure(
            defensive_coverage=defensive_coverage,
            offensive_coverage=offensive_coverage,
            repeated_weaknesses=repeated_weaknesses,
            critical_weaknesses=critical_weaknesses,
            missing_resistances=missing_resistances,
        )
        primary_patch_types, conditional_dual_patch_types = self._suggest_patch_types(
            repeated_weaknesses=repeated_weaknesses,
            critical_weaknesses=critical_weaknesses,
            missing_resistances=missing_resistances,
            offensive_coverage=offensive_coverage,
        )
        evidence = self._build_evidence(
            repeated_weaknesses=repeated_weaknesses,
            critical_weaknesses=critical_weaknesses,
            missing_resistances=missing_resistances,
            thin_resistances=thin_resistances,
            offensive_coverage=offensive_coverage,
            breakdown=breakdown,
            team_size=len(slots),
        )

        overlap_notes = tuple(
            note
            for note in (
                self._format_type_list("critical_weaknesses", critical_weaknesses),
                self._format_type_list("thin_resistances", thin_resistances),
            )
            if note
        )

        return TeamStructureReport(
            structural_score=breakdown.structural_score,
            repeated_weaknesses=repeated_weaknesses,
            missing_resistances=missing_resistances,
            offensive_coverage=offensive_coverage,
            defensive_coverage=defensive_coverage,
            primary_patch_types=primary_patch_types,
            conditional_dual_patch_types=conditional_dual_patch_types,
            overlap_notes=overlap_notes,
            evidence=evidence,
        )

    def _slot_types(self, slot: TeamSlot) -> tuple[str, ...]:
        if slot.secondary_type:
            return (slot.primary_type, slot.secondary_type)
        return (slot.primary_type,)

    def _build_defensive_coverage(self, slots: tuple[TeamSlot, ...]) -> tuple[DefensiveCoverageEntry, ...]:
        coverage: list[DefensiveCoverageEntry] = []
        for attacking_type in self.chart.types:
            weak_slots = 0
            resist_slots = 0
            neutral_slots = 0
            for slot in slots:
                multiplier = self.chart.combined_multiplier(attacking_type, self._slot_types(slot))
                if multiplier > 1.0:
                    weak_slots += 1
                elif multiplier < 1.0:
                    resist_slots += 1
                else:
                    neutral_slots += 1
            coverage.append(
                DefensiveCoverageEntry(
                    defending_type=attacking_type,
                    weak_slots=weak_slots,
                    resist_slots=resist_slots,
                    neutral_slots=neutral_slots,
                )
            )
        return tuple(coverage)

    def _build_offensive_coverage(self, slots: tuple[TeamSlot, ...]) -> tuple[OffensiveCoverageEntry, ...]:
        represented_types = []
        seen = set()
        for slot in slots:
            for type_name in self._slot_types(slot):
                if type_name not in seen:
                    seen.add(type_name)
                    represented_types.append(type_name)

        entries: list[OffensiveCoverageEntry] = []
        for attacker_type in represented_types:
            relation = self.chart.attack_profile(attacker_type)
            entries.append(
                OffensiveCoverageEntry(
                    attacker_type=attacker_type,
                    super_effective_targets=tuple(sorted(relation.attack_strong)),
                    resisted_targets=tuple(sorted(relation.attack_weak)),
                )
            )
        return tuple(entries)

    def _score_structure(
        self,
        defensive_coverage: tuple[DefensiveCoverageEntry, ...],
        offensive_coverage: tuple[OffensiveCoverageEntry, ...],
        repeated_weaknesses: tuple[str, ...],
        critical_weaknesses: tuple[str, ...],
        missing_resistances: tuple[str, ...],
    ) -> StructureScoreBreakdown:
        type_count = len(defensive_coverage)
        represented_attack_types = len(offensive_coverage)

        defensive_profile_scores = []
        for entry in defensive_coverage:
            score = 1.0
            if entry.weak_slots >= 2:
                score -= 0.20
            if entry.weak_slots >= 3:
                score -= 0.15
            if entry.resist_slots == 0:
                score -= 0.15
            elif entry.resist_slots == 1:
                score -= 0.05
            if entry.resist_slots >= 2 and entry.weak_slots == 0:
                score += 0.05
            defensive_profile_scores.append(self._clamp(score))

        defensive_resilience = sum(defensive_profile_scores) / type_count

        covered_targets = {
            target for entry in offensive_coverage for target in entry.super_effective_targets
        }
        offensive_coverage_score = len(covered_targets) / len(self.chart.types)

        redundant_resists = sum(1 for entry in defensive_coverage if entry.resist_slots >= 2)
        resistance_redundancy = redundant_resists / type_count

        role_flex_placeholder = 0.5
        weakness_penalty = (
            0.05 * len(repeated_weaknesses)
            + 0.08 * len(critical_weaknesses)
            + 0.05 * sum(1 for name in missing_resistances if name in critical_weaknesses)
        )

        structural_score = self._clamp(
            0.45 * defensive_resilience
            + 0.30 * offensive_coverage_score
            + 0.15 * resistance_redundancy
            + 0.10 * role_flex_placeholder
            - weakness_penalty
        )

        return StructureScoreBreakdown(
            defensive_resilience=defensive_resilience,
            offensive_coverage=offensive_coverage_score,
            resistance_redundancy=resistance_redundancy,
            role_flex_placeholder=role_flex_placeholder,
            weakness_penalty=weakness_penalty,
            structural_score=structural_score,
        )

    def _suggest_patch_types(
        self,
        repeated_weaknesses: tuple[str, ...],
        critical_weaknesses: tuple[str, ...],
        missing_resistances: tuple[str, ...],
        offensive_coverage: tuple[OffensiveCoverageEntry, ...],
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        current_covered_targets = {
            target for entry in offensive_coverage for target in entry.super_effective_targets
        }
        represented_types = {entry.attacker_type for entry in offensive_coverage}
        single_candidates = []
        dual_candidates = []

        candidate_type_sets = [(type_name,) for type_name in self.chart.types]
        candidate_type_sets.extend(combinations(self.chart.types, 2))

        for candidate_types in candidate_type_sets:
            covered_missing = sum(
                1
                for attack_type in missing_resistances
                if self.chart.combined_multiplier(attack_type, candidate_types) < 1.0
            )
            covered_repeated = sum(
                1
                for attack_type in repeated_weaknesses
                if self.chart.combined_multiplier(attack_type, candidate_types) < 1.0
            )
            covered_critical = sum(
                1
                for attack_type in critical_weaknesses
                if self.chart.combined_multiplier(attack_type, candidate_types) < 1.0
            )
            risky_on_critical = sum(
                1
                for attack_type in critical_weaknesses
                if self.chart.combined_multiplier(attack_type, candidate_types) > 1.0
            )
            candidate_attack_targets = set()
            for type_name in candidate_types:
                candidate_attack_targets.update(self.chart.attack_profile(type_name).attack_strong)
            new_offensive_targets = len(candidate_attack_targets.difference(current_covered_targets))

            complexity_penalty = 0.35 if len(candidate_types) == 2 else 0.0
            novelty_penalty = 0.15 if all(type_name in represented_types for type_name in candidate_types) else 0.0
            score = (
                2.5 * covered_missing
                + 1.5 * covered_repeated
                + 1.0 * covered_critical
                + 0.35 * new_offensive_targets
                - 1.25 * risky_on_critical
                - complexity_penalty
                - novelty_penalty
            )
            candidate_label = "/".join(candidate_types)
            candidate_record = (
                score,
                covered_missing,
                covered_repeated,
                covered_critical,
                new_offensive_targets,
                candidate_label,
            )
            if len(candidate_types) == 1:
                single_candidates.append(candidate_record)
            else:
                dual_candidates.append(candidate_record)

        single_candidates.sort(key=lambda item: item[:-1], reverse=True)
        dual_candidates.sort(key=lambda item: item[:-1], reverse=True)

        primary_patch_types = tuple(
            candidate_label for score, *_rest, candidate_label in single_candidates[:3] if score > 0
        )
        conditional_dual_patch_types = tuple(
            candidate_label for score, *_rest, candidate_label in dual_candidates[:3] if score > 0
        )
        return primary_patch_types, conditional_dual_patch_types

    def _build_evidence(
        self,
        repeated_weaknesses: tuple[str, ...],
        critical_weaknesses: tuple[str, ...],
        missing_resistances: tuple[str, ...],
        thin_resistances: tuple[str, ...],
        offensive_coverage: tuple[OffensiveCoverageEntry, ...],
        breakdown: StructureScoreBreakdown,
        team_size: int,
    ) -> tuple[str, ...]:
        covered_targets = sorted(
            {target for entry in offensive_coverage for target in entry.super_effective_targets}
        )
        evidence = [
            f"structural_score={breakdown.structural_score:.3f}",
            f"defensive_resilience={breakdown.defensive_resilience:.3f}",
            f"offensive_coverage={breakdown.offensive_coverage:.3f}",
            f"resistance_redundancy={breakdown.resistance_redundancy:.3f}",
            f"team_size={team_size}",
        ]
        if repeated_weaknesses:
            evidence.append(f"repeated_weaknesses={','.join(repeated_weaknesses)}")
        if critical_weaknesses:
            evidence.append(f"critical_weaknesses={','.join(critical_weaknesses)}")
        if missing_resistances:
            evidence.append(f"missing_resistances={','.join(missing_resistances)}")
        if thin_resistances:
            evidence.append(f"thin_resistances={','.join(thin_resistances)}")
        evidence.append(f"offensive_targets_covered={','.join(covered_targets)}")
        return tuple(evidence)

    def _format_type_list(self, label: str, values: tuple[str, ...]) -> str:
        if not values:
            return ""
        return f"{label}={','.join(values)}"

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))
