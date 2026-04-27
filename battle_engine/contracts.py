from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class RoleTag(StrEnum):
    PRIMARY_BREAKER = "primary_breaker"
    SECONDARY_BREAKER = "secondary_breaker"
    CLEANER = "cleaner"
    BULKY_PIVOT = "bulky_pivot"
    WALL = "wall"
    SUPPORT = "support"
    SPEED_CONTROL = "speed_control"
    HAZARD_SETTER = "hazard_setter"
    HAZARD_CONTROL = "hazard_control"
    STATUS_SPREADER = "status_spreader"
    SETUP_SWEEPER = "setup_sweeper"
    REVENGE_KILLER = "revenge_killer"
    TECH_SLOT = "tech_slot"


class Archetype(StrEnum):
    STALL = "stall"
    BALANCE = "balance"
    BULKY_OFFENSE = "bulky_offense"
    HYPER_OFFENSE = "hyper_offense"
    PIVOT_OFFENSE = "pivot_offense"
    ANTI_META = "anti_meta"


@dataclass(frozen=True)
class BaseStats:
    hp: int
    atk: int
    defense: int
    spa: int
    spd: int
    spe: int

    @property
    def bst(self) -> int:
        return self.hp + self.atk + self.defense + self.spa + self.spd + self.spe


@dataclass(frozen=True)
class DerivedMoveFeatures:
    recovery: bool = False
    hazard_setter: bool = False
    hazard_control: bool = False
    pivot_move: bool = False
    priority_move: bool = False
    setup_move: bool = False
    reliable_status: bool = False
    burst_damage: bool = False
    sustained_damage: bool = False
    anti_setup: bool = False
    speed_control: bool = False


@dataclass(frozen=True)
class SpeciesProfile:
    species_key: str
    dex_no: str
    base_name: str
    form_name: str | None
    primary_type: str
    secondary_type: str | None
    base_stats: BaseStats
    abilities: tuple[str, ...] = ()
    move_ids: tuple[str, ...] = ()
    derived_features: DerivedMoveFeatures = field(default_factory=DerivedMoveFeatures)


@dataclass(frozen=True)
class TeamSlot:
    slot_index: int
    species_key: str | None
    primary_type: str
    secondary_type: str | None = None
    selected_ability: str | None = None
    selected_moves: tuple[str, ...] = ()
    item: str | None = None
    nickname: str | None = None


@dataclass(frozen=True)
class AnalysisGoals:
    preserve_bulk: bool = False
    preserve_speed: bool = False
    prefer_pivot_play: bool = False
    prefer_status_game: bool = False
    avoid_duplicate_weakness: bool = True


@dataclass(frozen=True)
class TeamAnalysisRequest:
    slots: tuple[TeamSlot, ...]
    goals: AnalysisGoals = field(default_factory=AnalysisGoals)
    target_archetypes: tuple[Archetype, ...] = ()
    threat_watchlist: tuple[str, ...] = ()
    meta_snapshot_id: str | None = None
    team_id: str | None = None


@dataclass(frozen=True)
class RoleScore:
    role_tag: RoleTag
    score: float
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class PressureProfile:
    offense: float
    bulk: float
    speed: float
    utility: float
    sustain: float


@dataclass(frozen=True)
class SpeciesRoleReport:
    species_key: str
    primary_role: RoleTag
    secondary_roles: tuple[RoleScore, ...]
    pressure_profile: PressureProfile
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class DefensiveCoverageEntry:
    defending_type: str
    weak_slots: int
    resist_slots: int
    neutral_slots: int


@dataclass(frozen=True)
class OffensiveCoverageEntry:
    attacker_type: str
    super_effective_targets: tuple[str, ...]
    resisted_targets: tuple[str, ...]


@dataclass(frozen=True)
class TeamStructureReport:
    structural_score: float
    repeated_weaknesses: tuple[str, ...]
    missing_resistances: tuple[str, ...]
    offensive_coverage: tuple[OffensiveCoverageEntry, ...]
    defensive_coverage: tuple[DefensiveCoverageEntry, ...]
    primary_patch_types: tuple[str, ...] = ()
    conditional_dual_patch_types: tuple[str, ...] = ()
    overlap_notes: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArchetypeScore:
    archetype: Archetype
    score: float


@dataclass(frozen=True)
class TeamArchetypeReport:
    primary_archetype: Archetype
    archetype_scores: tuple[ArchetypeScore, ...]
    tempo_score: float
    sustain_score: float
    pivot_score: float
    setup_score: float
    anti_setup_score: float
    explanation_evidence: tuple[str, ...] = ()


def to_payload(value: Any) -> Any:
    """Convert dataclass and enum contracts into plain JSON-serializable payloads."""
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [to_payload(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_payload(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: to_payload(item) for key, item in value.items()}
    return value
