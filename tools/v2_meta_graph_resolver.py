"""Meta Graph fuzzy matcher and default config resolver.

Handles:
1. Fuzzy matching community names to Battle Dex species
2. Resolving default species_set configs when only species name is known
3. Ranking configs by "mainstreamness"
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from tools.v2_meta_graph_contracts import (
    Confidence,
    load_all_cards,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"

# ──────────────────────────────────────────
# Fuzzy species matching
# ──────────────────────────────────────────


def _char_overlap(a: str, b: str) -> float:
    """Fraction of characters in the shorter string that appear in the longer."""
    if not a or not b:
        return 0.0
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if not shorter:
        return 0.0
    return sum(1 for ch in shorter if ch in longer) / len(shorter)


@dataclass
class SpeciesCandidate:
    species_id: str
    display_name: str
    form_name: str | None = None
    match_reason: str = ""


def fuzzy_search_species(
    query: str,
    db_path: Path = DEFAULT_DB,
    *,
    limit: int = 5,
) -> list[SpeciesCandidate]:
    """Find Battle Dex species matching a community name (possibly OCR-damaged).

    Returns candidates ordered by match quality.
    """
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT species_id, display_name, form_name FROM species_form"
    )
    all_rows = cur.fetchall()
    conn.close()

    candidates: list[tuple[float, SpeciesCandidate]] = []

    query_clean = query.strip()
    query_len = len(query_clean)

    for row in all_rows:
        name = row["display_name"] or ""
        name_clean = name.strip()

        # Tier 1: exact match
        if query_clean == name_clean:
            candidates.append((
                1.0,
                SpeciesCandidate(
                    species_id=row["species_id"],
                    display_name=name_clean,
                    form_name=row["form_name"],
                    match_reason="exact",
                ),
            ))
            continue

        # Tier 2: one contains the other
        if query_clean in name_clean or name_clean in query_clean:
            score = 0.95 if query_clean in name_clean else 0.85
            candidates.append((
                score,
                SpeciesCandidate(
                    species_id=row["species_id"],
                    display_name=name_clean,
                    form_name=row["form_name"],
                    match_reason="contains",
                ),
            ))
            continue

        # Tier 3: character overlap
        overlap = _char_overlap(query_clean, name_clean)
        if overlap >= 0.6:
            candidates.append((
                overlap * 0.9,
                SpeciesCandidate(
                    species_id=row["species_id"],
                    display_name=name_clean,
                    form_name=row["form_name"],
                    match_reason=f"overlap={overlap:.2f}",
                ),
            ))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in candidates[:limit]]


# ──────────────────────────────────────────
# Default config resolution
# ──────────────────────────────────────────


@dataclass
class ConfigOption:
    card: dict
    mainstream_score: float = 0.0
    is_default: bool = False


@dataclass
class SpeciesConfigResolution:
    species_name: str
    options: list[ConfigOption] = field(default_factory=list)
    default: ConfigOption | None = None
    has_role_conflict: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def fallback_to_default(self) -> bool:
        """True if we have to assume default because no explicit set was given."""
        return len(self.options) == 1 and self.options[0].is_default

    @property
    def needs_clarification(self) -> bool:
        """True if there are conflicting mainstream configs and we can't pick."""
        return self.has_role_conflict


def resolve_species_configs(
    species_name: str,
    cards: list[dict] | None = None,
) -> SpeciesConfigResolution:
    """Given a species name, return all known configs ranked by mainstreamness.

    If cards is None, loads all cards from disk.
    """
    if cards is None:
        cards = load_all_cards()

    # Find cards matching this species
    matched: list[dict] = []
    for card in cards:
        cn = card.get("canonical_species_name", "")
        aliases = card.get("source_aliases", []) or []
        if species_name == cn or species_name in aliases:
            matched.append(card)

    result = SpeciesConfigResolution(species_name=species_name)

    if not matched:
        result.warnings.append(f"未找到 {species_name} 的任何配置卡")
        return result

    # Score each card by mainstreamness:
    # - confidence: observed=3, inferred=2, speculative=1
    # - source_refs count: 1 per source
    # - review_status: reviewed=+2
    confidence_score = {
        Confidence.OBSERVED: 3,
        Confidence.INFERRED: 2,
        Confidence.SPECULATIVE: 1,
    }

    options: list[ConfigOption] = []
    for card in matched:
        score = 0.0
        conf = card.get("confidence", Confidence.SPECULATIVE)
        score += confidence_score.get(conf, 0)
        score += len(card.get("source_refs", []) or []) * 1.0
        if card.get("review_status") == "reviewed":
            score += 2.0
        options.append(ConfigOption(card=card, mainstream_score=score))

    # Sort by mainstream score descending
    options.sort(key=lambda o: o.mainstream_score, reverse=True)

    if options:
        options[0].is_default = True
        result.default = options[0]

    result.options = options

    # Detect role conflicts among top configs
    if len(options) >= 2:
        top_roles = set(options[0].card.get("role_labels", []) or [])
        second_roles = set(options[1].card.get("role_labels", []) or [])
        # If top two configs have completely disjoint role labels,
        # there's likely a role conflict (e.g., attacker vs wall)
        if top_roles and second_roles and not top_roles & second_roles:
            result.has_role_conflict = True
            result.warnings.append(
                f"{species_name} 存在角色冲突的主流配置: "
                f"{top_roles} vs {second_roles}"
            )

    return result


def resolve_species_list(
    names: Sequence[str],
    cards: list[dict] | None = None,
) -> dict[str, SpeciesConfigResolution]:
    """Resolve configs for multiple species at once."""
    if cards is None:
        cards = load_all_cards()
    return {name: resolve_species_configs(name, cards) for name in names}


# ──────────────────────────────────────────
# Full pipeline: raw name → species match → config
# ──────────────────────────────────────────


@dataclass
class ResolvedName:
    raw_name: str
    species_candidates: list[SpeciesCandidate] = field(default_factory=list)
    best_match: SpeciesCandidate | None = None
    config_resolution: SpeciesConfigResolution | None = None
    needs_manual_review: bool = False
    review_reason: str = ""


def resolve_raw_names(
    raw_names: Sequence[str],
    cards: list[dict] | None = None,
    db_path: Path = DEFAULT_DB,
) -> list[ResolvedName]:
    """Full resolution pipeline for raw community species names.

    1. Fuzzy match each name against Battle Dex
    2. For best match, resolve configs
    3. Flag names that need manual review
    """
    if cards is None:
        cards = load_all_cards()

    results: list[ResolvedName] = []
    for name in raw_names:
        rn = ResolvedName(raw_name=name.strip())

        candidates = fuzzy_search_species(name, db_path=db_path)
        rn.species_candidates = candidates

        if not candidates:
            rn.needs_manual_review = True
            rn.review_reason = f"Battle Dex 中未找到匹配: {name}"
            results.append(rn)
            continue

        best = candidates[0]
        rn.best_match = best

        if best.match_reason != "exact":
            rn.needs_manual_review = True
            rn.review_reason = (
                f"{name} → {best.display_name} (匹配方式: {best.match_reason})，请确认"
            )

        rn.config_resolution = resolve_species_configs(
            best.display_name, cards
        )

        if rn.config_resolution.needs_clarification:
            rn.needs_manual_review = True
            if rn.review_reason:
                rn.review_reason += "; "
            rn.review_reason += "存在角色冲突的主流配置"

        results.append(rn)

    return results
