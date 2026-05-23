"""Meta Graph shared contracts and utilities.

Used by: v2_validate_graph, v2_generate_edge_index, v2_generate_speed_index,
and the runtime retrieval module.
"""

from __future__ import annotations

import re
import os
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE_GRAPH_DIR = REPO_ROOT / "data" / "knowledge_graph" / "v0"
DEFAULT_META_GRAPH_DIR = DEFAULT_KNOWLEDGE_GRAPH_DIR / "set_graph"
COMPAT_META_GRAPH_DIR = REPO_ROOT / "data" / "meta_graph" / "v0"
LEGACY_META_GRAPH_DIR = REPO_ROOT / "artifacts" / "v2_meta_graph"


def _resolve_knowledge_graph_dir() -> Path:
    override = os.environ.get("ROCO_KNOWLEDGE_GRAPH_DIR")
    if override:
        return Path(override).expanduser()
    return DEFAULT_KNOWLEDGE_GRAPH_DIR


def _resolve_meta_graph_dir() -> Path:
    override = os.environ.get("ROCO_META_GRAPH_DIR")
    if override:
        return Path(override).expanduser()
    knowledge_override = os.environ.get("ROCO_KNOWLEDGE_GRAPH_DIR")
    if knowledge_override:
        return Path(knowledge_override).expanduser() / "set_graph"
    if (DEFAULT_META_GRAPH_DIR / "species_sets").exists():
        return DEFAULT_META_GRAPH_DIR
    if (COMPAT_META_GRAPH_DIR / "species_sets").exists():
        return COMPAT_META_GRAPH_DIR
    return LEGACY_META_GRAPH_DIR


KNOWLEDGE_GRAPH_DIR = _resolve_knowledge_graph_dir()
META_GRAPH_DIR = _resolve_meta_graph_dir()
SPECIES_SETS_DIR = META_GRAPH_DIR / "species_sets"
REGISTRY_PATH = META_GRAPH_DIR / "graph_registry.yaml"
EDGE_INDEX_PATH = META_GRAPH_DIR / "edge_index.yaml"
SPEED_INDEX_PATH = META_GRAPH_DIR / "speed_index.yaml"
MECHANISM_RULES_DIR = KNOWLEDGE_GRAPH_DIR / "mechanism_rules"
REVIEW_STATE_DIR = KNOWLEDGE_GRAPH_DIR / "review_state"


class GraphOrigin(StrEnum):
    HUMAN = "human"
    SHADOW = "shadow"


class Confidence(StrEnum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    SPECULATIVE = "speculative"


class ReviewStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    REVIEWED = "reviewed"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"


class EdgeType(StrEnum):
    SYNERGY = "synergy"
    THREAT = "threat"
    COUNTERPLAY = "counterplay"
    BAIT_PUNISH = "bait_punish"
    PIVOT_PATH = "pivot_path"
    KILLLINE = "killline"
    RESOURCE_RACE = "resource_race"
    MINDGAME = "mindgame"
    VOLATILITY = "volatility"


class ReasoningQuality(StrEnum):
    FULL_CHAIN = "full_chain"
    PARTIAL_CHAIN = "partial_chain"
    CLAIM_ONLY = "claim_only"


class SourceType(StrEnum):
    COMMUNITY_VIDEO = "community_video"
    BATTLE_DEX = "battle_dex"
    COMMUNITY_POST = "community_post"
    EXPERT_REVIEW = "expert_review"
    P10H_CASE = "p10h_case"
    MANUAL_TEST = "manual_test"
    AGENT_SYNTHESIS = "agent_synthesis"


class RoleLabel(StrEnum):
    SPEED_CONTROL = "speed_control"
    WALL = "wall"
    PIVOT = "pivot"
    SETUP_CORE = "setup_core"
    KILLLINE_CONVERTER = "killline_converter"
    WEATHER_SETTER = "weather_setter"
    HAZARD_SETTER = "hazard_setter"
    CLERIC = "cleric"
    WALLBREAKER = "wallbreaker"
    REVENGE_KILLER = "revenge_killer"
    STALL_ANCHOR = "stall_anchor"
    SACRIFICE_PIECE = "sacrifice_piece"


# ──────────────────────────────────────────
# Card I/O
# ──────────────────────────────────────────


def list_card_files(species_sets_dir: Path | None = None) -> list[Path]:
    """Return all YAML card files (excluding template)."""
    root = species_sets_dir or SPECIES_SETS_DIR
    if not root.exists():
        return []
    return sorted(
        p for p in root.glob("*.yaml")
        if p.name != "_template.yaml"
    )


def load_card(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_all_cards(species_sets_dir: Path | None = None) -> list[dict[str, Any]]:
    cards = []
    for path in list_card_files(species_sets_dir):
        try:
            card = load_card(path)
            card["_file"] = str(path)
            cards.append(card)
        except Exception as exc:
            raise ValueError(f"Failed to load {path}: {exc}") from exc
    return cards


def load_registry(registry_path: Path | None = None) -> dict[str, Any]:
    path = registry_path or REGISTRY_PATH
    if not path.exists():
        return {"species_sets": []}
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {"species_sets": []}


def save_yaml(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.dump(data, fh, allow_unicode=True, default_flow_style=False, sort_keys=False)


def make_species_set_id(species_name: str, variant: str, snapshot: str) -> str:
    """Derive a stable species_set id from name + variant + snapshot.

    Example:
        make_species_set_id("棋绮后", "max_speed_reap", "2026-s1")
        -> "species_set/棋绮后/max_speed_reap_2026-s1"
    """
    safe_name = re.sub(r"[^a-zA-Z一-鿿0-9]+", "_", species_name).strip("_")
    safe_variant = re.sub(r"[^a-z0-9_]+", "_", variant.lower()).strip("_")
    safe_snap = re.sub(r"[^a-zA-Z0-9\-]+", "_", snapshot)
    return f"species_set/{safe_name}/{safe_variant}_{safe_snap}"


def today_str() -> str:
    return date.today().isoformat()
