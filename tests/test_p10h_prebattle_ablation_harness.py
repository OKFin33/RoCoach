from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from tools import p10h_prebattle_ablation_harness as harness


class P10hPrebattleAblationHarnessTests(unittest.TestCase):
    def test_scaffold_blocks_generation_until_answer_key_is_filled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(harness.scaffold_cases(root, overwrite=True), 0)
            cfg = harness.RunConfig(
                output_dir=root,
                case_dir=root / "inputs",
                levels=("L0",),
                repeats=1,
                seed=1,
                provider_base_url="https://api.deepseek.com",
                model="deepseek-v4-pro",
                api_key_env="ROCO_OPENAI_API_KEY",
                reasoning_mode="enabled",
                reasoning_effort="high",
                temperature=0.3,
                dry_run=True,
                max_calls=None,
            )

            self.assertEqual(harness.build_artifacts(cfg), 2)

    def test_build_all_levels_after_answer_key_filled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            harness.scaffold_cases(root, overwrite=True)
            for path in (root / "inputs").glob("*.yaml"):
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                data["answer_key"] = _filled_structured_answer_key()
                path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

            cfg = harness.RunConfig(
                output_dir=root,
                case_dir=root / "inputs",
                levels=("L0", "L1", "L2", "L3-exact", "L3-transfer"),
                repeats=1,
                seed=1,
                provider_base_url="https://api.deepseek.com",
                model="deepseek-v4-pro",
                api_key_env="ROCO_OPENAI_API_KEY",
                reasoning_mode="enabled",
                reasoning_effort="high",
                temperature=0.3,
                dry_run=True,
                max_calls=None,
            )

            self.assertEqual(harness.build_artifacts(cfg), 0)
            run_order = root / "run_order.json"
            self.assertTrue(run_order.exists())
            self.assertTrue((root / "grounding_packs").exists())
            self.assertTrue((root / "prompts").exists())

    def test_blind_packet_includes_primitive_failure_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outputs = root / "outputs"
            outputs.mkdir(parents=True)
            (outputs / "run_1.json").write_text(
                json.dumps(
                    {
                        "run_id": "case_a__l3_transfer__r01",
                        "case_id": "case_a",
                        "level": "L3-transfer",
                        "repeat": 1,
                        "status": "ok",
                        "answer": "answer",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            self.assertEqual(harness.build_blind_packet(root, seed=1), 0)
            score_template = (root / "blind_review" / "score_sheet_template.csv").read_text(encoding="utf-8")
            failure_template = (root / "blind_review" / "primitive_failure_log_template.csv").read_text(
                encoding="utf-8"
            )
            self.assertIn("failed_checks_json", score_template)
            self.assertIn("primitive_id", failure_template)
            self.assertIn("repair_target", failure_template)

def _filled_structured_answer_key() -> dict[str, object]:
    return {
        "archetype_recognition": {
            "description": "识别对方队伍体系",
            "what_expert_knew": ["对方核心威胁和资源引擎"],
        },
        "d1_attention_order": {"steps": [{"order": 1, "focus": "核心威胁", "why": "先看资源引擎"}]},
        "d2_activated_priors": {"priors": [{"id": "prior_resource_engine_before_matchup", "activation": "资源优先"}]},
        "d3_reasoning_chain": {"steps": [{"step": 1, "action": "建模体系", "reasoning": "先识别队伍运作方式"}]},
        "conditional_knowledge": {"items": []},
        "evaluation_checklist": {
            "d1_alignment": [{"check": "是否先看资源引擎", "weight": "critical"}],
            "d2_alignment": [{"check": "是否避免确定解过度声明", "weight": "critical"}],
            "d3_alignment": [{"check": "是否展示推理链", "weight": "critical"}],
            "negative_checks": [{"check": "是否出现宝可梦术语", "severity": "major"}],
        },
        "what_if_questions": [
            {
                "question": "如果对方首发变化，路线如何调整？",
                "purpose": "测试例外处理",
                "key_points": ["不要无条件套默认路线"],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
