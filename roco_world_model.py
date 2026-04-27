from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DATA_PATH = Path(__file__).parent / "data" / "roco_world_type_chart.json"


@dataclass(frozen=True)
class TypeRelations:
    attack_strong: tuple[str, ...]
    attack_weak: tuple[str, ...]
    defense_weak: tuple[str, ...]
    defense_resist: tuple[str, ...]


class RocoWorldTypeChart:
    def __init__(self, data_path: Path | str = DATA_PATH) -> None:
        path = Path(data_path)
        raw = json.loads(path.read_text(encoding="utf-8"))

        self.types: tuple[str, ...] = tuple(raw["types"])
        self.type_set = set(self.types)
        self.status_immunities: dict[str, tuple[str, ...]] = {
            name: tuple(statuses) for name, statuses in raw["status_immunities"].items()
        }
        self.relations: dict[str, TypeRelations] = {}

        for type_name, payload in raw["type_chart"].items():
            self._validate_type(type_name)
            self.relations[type_name] = TypeRelations(
                attack_strong=tuple(payload["attack"]["2x"]),
                attack_weak=tuple(payload["attack"]["0.5x"]),
                defense_weak=tuple(payload["defense"]["2x"]),
                defense_resist=tuple(payload["defense"]["0.5x"]),
            )

        self._validate_model()

    def _validate_type(self, type_name: str) -> None:
        if type_name not in self.type_set:
            raise ValueError(f"Unknown type in dataset: {type_name}")

    def _validate_model(self) -> None:
        missing = self.type_set.difference(self.relations)
        if missing:
            raise ValueError(f"Missing type definitions: {sorted(missing)}")

        for type_name, relation in self.relations.items():
            for target in (
                *relation.attack_strong,
                *relation.attack_weak,
                *relation.defense_weak,
                *relation.defense_resist,
            ):
                self._validate_type(target)

            overlap = set(relation.attack_strong).intersection(relation.attack_weak)
            if overlap:
                raise ValueError(f"{type_name} has contradictory attack entries: {sorted(overlap)}")

            overlap = set(relation.defense_weak).intersection(relation.defense_resist)
            if overlap:
                raise ValueError(f"{type_name} has contradictory defense entries: {sorted(overlap)}")

        for attacker in self.types:
            for defender in self.types:
                expected = self.attack_multiplier(attacker, defender)
                defense_view = self.defense_multiplier(defender, attacker)
                if expected != defense_view:
                    raise ValueError(
                        f"Inconsistent chart: {attacker} -> {defender} is {expected}, "
                        f"but {defender} defense view says {defense_view}"
                    )

    def _normalize_defender_types(self, defender_types: str | Iterable[str]) -> tuple[str, ...]:
        if isinstance(defender_types, str):
            defender_types = (defender_types,)
        normalized = tuple(defender_types)
        if not normalized:
            raise ValueError("At least one defender type is required")
        for type_name in normalized:
            self._validate_type(type_name)
        return normalized

    def attack_profile(self, attacker: str) -> TypeRelations:
        self._validate_type(attacker)
        return self.relations[attacker]

    def defense_profile(self, defender: str) -> TypeRelations:
        self._validate_type(defender)
        return self.relations[defender]

    def attack_multiplier(self, attacker: str, defender: str) -> float:
        self._validate_type(attacker)
        self._validate_type(defender)
        relation = self.relations[attacker]
        if defender in relation.attack_strong:
            return 2.0
        if defender in relation.attack_weak:
            return 0.5
        return 1.0

    def defense_multiplier(self, defender: str, attacker: str) -> float:
        self._validate_type(defender)
        self._validate_type(attacker)
        relation = self.relations[defender]
        if attacker in relation.defense_weak:
            return 2.0
        if attacker in relation.defense_resist:
            return 0.5
        return 1.0

    def combined_multiplier(self, attacker: str, defender_types: str | Iterable[str]) -> float:
        defender_types = self._normalize_defender_types(defender_types)
        if len(defender_types) == 1:
            return self.attack_multiplier(attacker, defender_types[0])

        multipliers = [self.attack_multiplier(attacker, defender) for defender in defender_types]
        strong_count = sum(1 for value in multipliers if value > 1.0)
        weak_count = sum(1 for value in multipliers if value < 1.0)

        if strong_count == weak_count:
            return 1.0
        if strong_count > weak_count:
            return 3.0 if strong_count - weak_count >= 2 else 2.0
        return 1.0 / 3.0 if weak_count - strong_count >= 2 else 0.5

    def effectiveness_label(self, attacker: str, defender_types: str | Iterable[str]) -> str:
        multiplier = self.combined_multiplier(attacker, defender_types)
        if multiplier >= 3.0:
            return "double_super_effective"
        if multiplier > 1.0:
            return "super_effective"
        if multiplier == 1.0:
            return "neutral"
        if multiplier <= 1.0 / 3.0:
            return "double_resisted"
        return "resisted"

    def immune_statuses(self, defender_types: str | Iterable[str]) -> tuple[str, ...]:
        defender_types = self._normalize_defender_types(defender_types)
        statuses: set[str] = set()
        for type_name in defender_types:
            statuses.update(self.status_immunities.get(type_name, ()))
        return tuple(sorted(statuses))

    def summary(self, type_name: str) -> dict[str, tuple[str, ...]]:
        self._validate_type(type_name)
        relation = self.relations[type_name]
        return {
            "attack_strong": relation.attack_strong,
            "attack_weak": relation.attack_weak,
            "defense_weak": relation.defense_weak,
            "defense_resist": relation.defense_resist,
            "status_immunity": self.status_immunities.get(type_name, ()),
        }


if __name__ == "__main__":
    chart = RocoWorldTypeChart()
    samples = [
        ("火", ("草",)),
        ("水", ("火", "地")),
        ("光", ("恶", "幽")),
        ("电", ("地", "翼")),
    ]
    for attacker, defenders in samples:
        print(
            {
                "attacker": attacker,
                "defenders": defenders,
                "multiplier": chart.combined_multiplier(attacker, defenders),
                "label": chart.effectiveness_label(attacker, defenders),
                "immune_statuses": chart.immune_statuses(defenders),
            }
        )
