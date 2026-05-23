"""Meta Graph retrieval for advisor runtime.

Provides read-only access to the Meta Graph knowledge base.
Wire this into the advisor runtime to inject species_set context
into Agent prompts before reasoning.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from tools.v2_meta_graph_contracts import (
    META_GRAPH_DIR,
    GraphOrigin,
    load_all_cards,
)


class MetaGraphRetriever:
    """Read-only retrieval interface for the Meta Graph.

    Usage in advisor runtime::

        mg = MetaGraphRetriever()
        context = mg.query_by_species_ids(["species_abc", "species_xyz"])
        # context is a formatted string for prompt injection
    """

    def __init__(
        self,
        *,
        graph_dir: Path = META_GRAPH_DIR,
        shadow_graph_enabled: bool = False,
    ):
        self._graph_dir = Path(graph_dir)
        self._shadow_enabled = shadow_graph_enabled
        self._cards: list[dict] | None = None
        self._edge_index: dict | None = None
        self._speed_index: dict | None = None

    # ── Lazy load ──

    @property
    def cards(self) -> list[dict]:
        if self._cards is None:
            self._cards = load_all_cards(self._graph_dir / "species_sets")
        return self._cards

    @property
    def edge_index(self) -> dict:
        if self._edge_index is None:
            self._edge_index = self._load_yaml(self._graph_dir / "edge_index.yaml")
        return self._edge_index

    @property
    def speed_index(self) -> dict:
        if self._speed_index is None:
            self._speed_index = self._load_yaml(self._graph_dir / "speed_index.yaml")
        return self._speed_index

    def _load_yaml(self, path: Path) -> dict:
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}

    def reload(self) -> None:
        """Clear caches and reload from disk."""
        self._cards = None
        self._edge_index = None
        self._speed_index = None

    # ── Filters ──

    def _card_is_active(self, card: dict) -> bool:
        """Filter out superseded, shadow (if disabled), and unreviewed cards."""
        if card.get("review_status") != "reviewed":
            return False
        origin = card.get("graph_origin", "human")
        if origin == GraphOrigin.SHADOW and not self._shadow_enabled:
            return False
        return True

    def _active_cards(self) -> list[dict]:
        return [c for c in self.cards if self._card_is_active(c)]

    # ── Query APIs ──

    def get_species_sets_by_canonical_id(
        self, canonical_species_id: str
    ) -> list[dict]:
        """Return all active species_set cards for a given Battle Dex species_id."""
        return [
            c for c in self._active_cards()
            if c.get("canonical_species_id") == canonical_species_id
        ]

    def get_species_sets_by_name(self, species_name: str) -> list[dict]:
        """Return all active species_set cards matching a display name."""
        return [
            c for c in self._active_cards()
            if c.get("canonical_species_name") == species_name
        ]

    def get_species_sets_by_tag(self, tag: str) -> list[dict]:
        """Return all active cards with a given archetype tag."""
        return [
            c for c in self._active_cards()
            if tag in (c.get("team_context", {}) or {}).get("archetype_tags", [])
        ]

    def get_species_sets_by_role(self, role: str) -> list[dict]:
        """Return all active cards with a given role label."""
        return [
            c for c in self._active_cards()
            if role in (c.get("role_labels") or [])
        ]

    def get_card_by_id(self, species_set_id: str) -> dict | None:
        for c in self._active_cards():
            if c.get("id") == species_set_id:
                return c
        return None

    def get_related_to(self, species_set_id: str) -> list[dict]:
        """Get all relationships claimed BY this species_set."""
        card = self.get_card_by_id(species_set_id)
        if not card:
            return []
        return card.get("related_to") or []

    def get_edges_for_target(self, species_set_id: str) -> list[dict]:
        """Get all edges whose target is this species_set (inbound references)."""
        result = []
        for edge in self.edge_index.get("edges", []):
            if edge.get("target_species_set_id") == species_set_id:
                result.append(edge)
        return result

    def get_outbound_edges(self, species_set_id: str) -> list[dict]:
        """Get all edges whose source is this species_set."""
        result = []
        for edge in self.edge_index.get("edges", []):
            if edge.get("source_species_set_id") == species_set_id:
                result.append(edge)
        return result

    def get_speed_tier(self, species_set_id: str) -> int | None:
        """Return speed_tier value for a species_set."""
        card = self.get_card_by_id(species_set_id)
        if not card:
            return None
        return card.get("speed_tier")

    def does_outspeed(
        self, a_id: str, b_id: str
    ) -> tuple[bool, int | None]:
        """Check if config A outspeeds config B. Returns (bool, margin)."""
        spd_a = self.get_speed_tier(a_id)
        spd_b = self.get_speed_tier(b_id)
        if spd_a is None or spd_b is None:
            return False, None
        return spd_a > spd_b, spd_a - spd_b

    def get_faster_than(self, species_set_id: str) -> list[dict]:
        """Return all configs slower than this one."""
        spd = self.get_speed_tier(species_set_id)
        if spd is None:
            return []
        result = []
        for tier_val, entries in (self.speed_index.get("speed_tiers") or {}).items():
            if int(tier_val) < spd:
                result.extend(entries)
        return result

    def get_slower_than(self, species_set_id: str) -> list[dict]:
        """Return all configs faster than this one."""
        spd = self.get_speed_tier(species_set_id)
        if spd is None:
            return []
        result = []
        for tier_val, entries in (self.speed_index.get("speed_tiers") or {}).items():
            if int(tier_val) > spd:
                result.extend(entries)
        return result

    # ── Context block assembly ──

    def query_by_species_ids(
        self,
        species_ids: list[str],
        *,
        include_speed: bool = True,
        include_relations: bool = True,
    ) -> str:
        """Build a context block for prompt injection.

        Given a list of Battle Dex species_ids (from A-layer resolution),
        find all matching species_sets and assemble a formatted context.
        """
        matched_cards: list[dict] = []
        for sid in species_ids:
            matched_cards.extend(self.get_species_sets_by_canonical_id(sid))

        if not matched_cards:
            return ""

        lines = ["[Meta Graph Context]"]
        graph_hint = "[H]=社区高分玩家"
        if self._shadow_enabled:
            graph_hint += " | [S]=Agent先前推理"
        lines.append(f"来源: {graph_hint}")
        lines.append("")

        # Configs section
        lines.append("涉及的配置:")
        for card in matched_cards:
            origin_tag = "[H]" if card.get("graph_origin") == "human" else "[S]"
            name = card.get("canonical_species_name", "?")
            nature = f", {card['nature']}" if card.get("nature") else ""
            spd = f", speed={card['speed_tier']}" if card.get("speed_tier") else ""
            roles = ", ".join(card.get("role_labels", []))
            conf = card.get("confidence", "?")
            lines.append(
                f"- {origin_tag} {name} ({card.get('ability','?')}{nature}{spd}): "
                f"技能={card.get('moves',[])}, 定位={roles}, "
                f"置信度={conf}"
            )
        lines.append("")

        # Relations section
        if include_relations:
            all_relations: list[dict] = []
            for card in matched_cards:
                for rel in card.get("related_to") or []:
                    all_relations.append({
                        "source_id": card["id"],
                        "source_name": card.get("canonical_species_name", "?"),
                        **rel,
                    })

            if all_relations:
                lines.append("关联关系:")
                for rel in all_relations:
                    origin_tag = "[H]"  # relations inherit from source card
                    target_id = rel.get("target_species_set_id", "?")
                    target_card = self.get_card_by_id(target_id)
                    target_name = (
                        target_card.get("canonical_species_name", target_id)
                        if target_card else target_id
                    )
                    lines.append(
                        f"- {origin_tag} {rel['source_name']} "
                        f"→ {rel.get('edge_type','?')} → {target_name}: "
                        f"{rel.get('description','')}"
                    )
                    rq = rel.get("reasoning_quality", "")
                    if rq == "claim_only":
                        lines[-1] += " [仅结论，无因果链]"
                    conf = rel.get("confidence", "")
                    if conf:
                        lines[-1] += f" (置信度: {conf})"

        # Speed section
        if include_speed and len(matched_cards) >= 2:
            speed_ids = [c["id"] for c in matched_cards if c.get("speed_tier")]
            if len(speed_ids) >= 2:
                lines.append("")
                lines.append("速度对比:")
                for i, a_id in enumerate(speed_ids):
                    for b_id in speed_ids[i + 1:]:
                        faster, margin = self.does_outspeed(a_id, b_id)
                        if margin is not None:
                            name_a = self.get_card_by_id(a_id)
                            name_b = self.get_card_by_id(b_id)
                            a_name = name_a.get("canonical_species_name", a_id) if name_a else a_id
                            b_name = name_b.get("canonical_species_name", b_id) if name_b else b_id
                            if faster:
                                lines.append(f"- {a_name} 快过 {b_name} (领先{margin})")
                            else:
                                faster2, margin2 = self.does_outspeed(b_id, a_id)
                                if margin2 is not None:
                                    lines.append(f"- {b_name} 快过 {a_name} (领先{margin2})")

        return "\n".join(lines)


# ── Module-level singleton (like the existing _NATIVE_AGENT pattern) ──

_retriever: MetaGraphRetriever | None = None


def get_meta_graph_retriever(
    *,
    shadow_enabled: bool = False,
    reload: bool = False,
) -> MetaGraphRetriever:
    global _retriever
    if _retriever is None or reload:
        _retriever = MetaGraphRetriever(shadow_graph_enabled=shadow_enabled)
    return _retriever
