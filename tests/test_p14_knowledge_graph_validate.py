import tempfile
import unittest
from pathlib import Path

import yaml

from tools.p14_validate_knowledge_graph import validate_knowledge_graph
from tools.v2_meta_graph_contracts import META_GRAPH_DIR


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _write_ledgers(root: Path) -> None:
    _write_yaml(root / "runtime_manifest.yaml", {
        "schema_version": "p14.knowledge_graph_runtime_manifest.v0",
        "schema_compatibility": {
            "migration_log_ref": "migration_log.yaml",
        },
    })
    _write_yaml(root / "migration_log.yaml", {
        "schema_version": "p14.kg_migration_log.v0",
    })
    review_state = root / "review_state"
    for filename in [
        "reviewer_ledger.yaml",
        "family_review_ledger.yaml",
        "error_ledger.yaml",
        "source_reliability_ledger.yaml",
        "promotion_audit_log.yaml",
        "affected_asset_index.yaml",
    ]:
        payload = {"schema_version": "test.v0"}
        if filename == "family_review_ledger.yaml":
            payload["entries"] = []
        if filename == "source_reliability_ledger.yaml":
            payload["sources"] = []
        _write_yaml(review_state / filename, payload)


def _card(mechanism_refs: list[str]) -> dict:
    return {
        "schema_version": "p14.species_set_card.v0",
        "id": "species_set/test/main_2026-s1",
        "kg_item_projection": {
            "schema_version": "p14.kg_item.v0",
            "kg_item_type": "set_family",
            "crosswalk_ref": "docs/specs/p14_species_set_kg_item_crosswalk_v0.md",
            "projection_status": "complete",
        },
        "canonical_species_id": "species_test",
        "canonical_species_name": "测试精灵",
        "moves": ["测试技能"],
        "ability": "测试特性",
        "meta_snapshot": "2026-s1",
        "graph_origin": "human",
        "source_refs": [{"source_type": "community_video", "source_ref": "x", "claim": "x", "date": "2026-05-18"}],
        "confidence": "observed",
        "review_status": "reviewed",
        "mechanism_refs": mechanism_refs,
        "field_provenance": {
            "species": [{"support_type": "explicit", "source_span_ids": ["span/test/S0001"]}],
            "moves": [{"support_type": "explicit", "source_span_ids": ["span/test/S0002"]}],
            "nature": [{"support_type": "not_applicable", "source_span_ids": []}],
            "iv": [{"support_type": "not_applicable", "source_span_ids": []}],
            "bloodline": [{"support_type": "not_applicable", "source_span_ids": []}],
            "role": [{"support_type": "explicit", "source_span_ids": ["span/test/S0003"]}],
            "teammate_relations": [{"support_type": "not_applicable", "source_span_ids": []}],
            "counter_relations": [{"support_type": "not_applicable", "source_span_ids": []}],
            "mechanism_dependencies": [{"support_type": "not_applicable", "source_span_ids": []}],
        },
        "review_identity": {
            "extractor_agent_id": "test_agent",
            "extractor_run_id": "test_run",
            "reviewer_agent_id": "test_reviewer",
            "reviewer_run_id": "test_review_run",
        },
        "related_to": [],
    }


class P14KnowledgeGraphValidateTests(unittest.TestCase):
    def test_default_meta_graph_dir_prefers_knowledge_graph_root(self) -> None:
        self.assertTrue(str(META_GRAPH_DIR).endswith("data/knowledge_graph/v0/set_graph"))

    def test_promoted_card_blocks_non_runtime_mechanism_ref(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kg"
            set_graph = root / "set_graph"
            _write_ledgers(root)
            _write_yaml(set_graph / "species_sets" / "test.yaml", _card(["mechanism/test/2026-s1"]))
            _write_yaml(root / "mechanism_rules" / "rules" / "test.yaml", {
                "id": "mechanism/test/2026-s1",
                "normalized_rule": "测试规则",
                "review": {"review_status": "candidate"},
                "runtime": {"runtime_allowed": False},
            })

            errors = validate_knowledge_graph(
                knowledge_root=root,
                set_graph_root=set_graph,
                mechanism_rules_dir=root / "mechanism_rules",
                review_state_dir=root / "review_state",
            )

        self.assertTrue(any("non-runtime mechanism rule" in e for e in errors))

    def test_promoted_card_allows_runtime_mechanism_ref(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kg"
            set_graph = root / "set_graph"
            _write_ledgers(root)
            _write_yaml(set_graph / "species_sets" / "test.yaml", _card(["mechanism/test/2026-s1"]))
            _write_yaml(root / "mechanism_rules" / "rules" / "test.yaml", {
                "id": "mechanism/test/2026-s1",
                "normalized_rule": "测试规则",
                "review": {"review_status": "pm_reviewed"},
                "runtime": {"runtime_allowed": True},
            })

            errors = validate_knowledge_graph(
                knowledge_root=root,
                set_graph_root=set_graph,
                mechanism_rules_dir=root / "mechanism_rules",
                review_state_dir=root / "review_state",
            )

        self.assertEqual(errors, [])

    def test_reviewed_card_requires_kg_projection_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kg"
            set_graph = root / "set_graph"
            _write_ledgers(root)
            card = _card([])
            card.pop("field_provenance")
            _write_yaml(set_graph / "species_sets" / "test.yaml", card)

            errors = validate_knowledge_graph(
                knowledge_root=root,
                set_graph_root=set_graph,
                mechanism_rules_dir=root / "mechanism_rules",
                review_state_dir=root / "review_state",
            )

        self.assertTrue(any("field_provenance.species" in e for e in errors))

    def test_post_policy_family_review_rejects_legacy_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kg"
            set_graph = root / "set_graph"
            _write_ledgers(root)
            _write_yaml(root / "review_state" / "family_review_ledger.yaml", {
                "schema_version": "p14.family_review_ledger.v0",
                "entries": [
                    {
                        "review_id": "family_review/test_post_policy",
                        "review_scope": "set_family",
                        "source_candidate": {
                            "species_name": "圣羽翼王",
                            "canonical_species_id": "species_test",
                            "source_family_id": "family_02",
                            "extractor_agent_id": "legacy_unknown",
                            "extractor_run_id": "legacy_unknown",
                            "identity_status": "legacy_pre_2026-05-23_identity_policy",
                        },
                        "proposed_card": {
                            "core_moves": ["水刃", "闪击"],
                        },
                        "evidence": {
                            "primary_source_ids": ["source_a", "source_b"],
                        },
                        "species_card_boundary": {
                            "species_level_card_status": "split_blocked",
                        },
                        "review": {
                            "review_status": "pm_reviewed",
                            "reviewer": "pm",
                            "reviewer_agent_id": "pm",
                            "reviewer_run_id": "legacy_unknown",
                            "identity_status": "legacy_pre_2026-05-23_identity_policy",
                            "review_date": "2026-05-24",
                        },
                        "promotion_gate": {
                            "allowed_scope": "set_family_only",
                            "promotion_ready": True,
                            "runtime_allowed": False,
                        },
                    }
                ],
            })
            _write_yaml(root / "review_state" / "source_reliability_ledger.yaml", {
                "schema_version": "p14.source_reliability.v0",
                "sources": [{"source_id": "source_a"}, {"source_id": "source_b"}],
            })
            _write_yaml(set_graph / "species_sets" / "test.yaml", _card([]))

            errors = validate_knowledge_graph(
                knowledge_root=root,
                set_graph_root=set_graph,
                mechanism_rules_dir=root / "mechanism_rules",
                review_state_dir=root / "review_state",
            )

        self.assertTrue(any("post-2026-05-23" in e and "legacy identity" in e for e in errors))

    def test_post_policy_reviewed_card_rejects_legacy_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kg"
            set_graph = root / "set_graph"
            _write_ledgers(root)
            card = _card([])
            card["review_identity"] = {
                "extractor_agent_id": "legacy_unknown",
                "extractor_run_id": "legacy_unknown",
                "reviewer_agent_id": "pm",
                "reviewer_run_id": "legacy_unknown",
                "identity_status": "legacy_pre_2026-05-23_identity_policy",
                "review_date": "2026-05-24",
            }
            _write_yaml(set_graph / "species_sets" / "test.yaml", card)

            errors = validate_knowledge_graph(
                knowledge_root=root,
                set_graph_root=set_graph,
                mechanism_rules_dir=root / "mechanism_rules",
                review_state_dir=root / "review_state",
            )

        self.assertTrue(any("post-2026-05-23 reviewed card uses legacy identity" in e for e in errors))

    def test_strict_requires_review_ledgers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kg"
            set_graph = root / "set_graph"
            _write_yaml(set_graph / "species_sets" / "test.yaml", _card([]))

            errors = validate_knowledge_graph(
                knowledge_root=root,
                set_graph_root=set_graph,
                mechanism_rules_dir=root / "mechanism_rules",
                review_state_dir=root / "review_state",
                strict=True,
            )

        self.assertTrue(any("review_state" in e for e in errors))

    def test_family_review_ledger_requires_known_primary_sources(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kg"
            set_graph = root / "set_graph"
            _write_ledgers(root)
            _write_yaml(root / "review_state" / "family_review_ledger.yaml", {
                "schema_version": "p14.family_review_ledger.v0",
                "entries": [
                    {
                        "review_id": "family_review/test",
                        "review_scope": "set_family",
                        "source_candidate": {
                            "species_name": "圣羽翼王",
                            "canonical_species_id": "species_test",
                            "source_family_id": "family_02",
                        },
                        "proposed_card": {
                            "core_moves": ["水刃", "闪击"],
                        },
                        "evidence": {
                            "primary_source_ids": ["source_known", "source_missing"],
                        },
                        "species_card_boundary": {
                            "species_level_card_status": "split_blocked",
                        },
                        "review": {
                            "review_status": "review_packeted",
                        },
                        "promotion_gate": {
                            "allowed_scope": "set_family_only",
                            "promotion_ready": False,
                            "runtime_allowed": False,
                        },
                    }
                ],
            })
            _write_yaml(root / "review_state" / "source_reliability_ledger.yaml", {
                "schema_version": "p14.source_reliability.v0",
                "sources": [{"source_id": "source_known"}],
            })
            _write_yaml(set_graph / "species_sets" / "test.yaml", _card([]))

            errors = validate_knowledge_graph(
                knowledge_root=root,
                set_graph_root=set_graph,
                mechanism_rules_dir=root / "mechanism_rules",
                review_state_dir=root / "review_state",
            )

        self.assertTrue(any("source_missing" in e for e in errors))

    def test_family_review_ledger_keeps_split_blocked_scope_family_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "kg"
            set_graph = root / "set_graph"
            _write_ledgers(root)
            _write_yaml(root / "review_state" / "family_review_ledger.yaml", {
                "schema_version": "p14.family_review_ledger.v0",
                "entries": [
                    {
                        "review_id": "family_review/test",
                        "review_scope": "set_family",
                        "source_candidate": {
                            "species_name": "圣羽翼王",
                            "canonical_species_id": "species_test",
                            "source_family_id": "family_02",
                        },
                        "proposed_card": {
                            "core_moves": ["水刃", "闪击"],
                        },
                        "evidence": {
                            "primary_source_ids": ["source_a", "source_b"],
                        },
                        "species_card_boundary": {
                            "species_level_card_status": "split_blocked",
                        },
                        "review": {
                            "review_status": "review_packeted",
                        },
                        "promotion_gate": {
                            "allowed_scope": "species_card",
                            "promotion_ready": False,
                            "runtime_allowed": False,
                        },
                    }
                ],
            })
            _write_yaml(root / "review_state" / "source_reliability_ledger.yaml", {
                "schema_version": "p14.source_reliability.v0",
                "sources": [{"source_id": "source_a"}, {"source_id": "source_b"}],
            })
            _write_yaml(set_graph / "species_sets" / "test.yaml", _card([]))

            errors = validate_knowledge_graph(
                knowledge_root=root,
                set_graph_root=set_graph,
                mechanism_rules_dir=root / "mechanism_rules",
                review_state_dir=root / "review_state",
            )

        self.assertTrue(any("allowed_scope=set_family_only" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
