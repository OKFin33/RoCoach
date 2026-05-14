#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from advisor.config import RocoNativeModelConfig
from advisor.experiment_layers import ExperimentLayerConfig, P10hExperimentDocContextRetriever
from agent_core.contracts import PersonaRuntimeActivationScope
from api.runtime_headers import RequestRuntimeConfig, RequestRuntimeMode
from api.services.advisor_service import AdvisorService


DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "p10h_agent_harness_probe"

CONDITIONS: dict[str, ExperimentLayerConfig] = {
    "A_B_C_app": ExperimentLayerConfig(),
    "A_B_C_Bplus": ExperimentLayerConfig(include_b_layer_candidates=True),
    "A_B_C_D1_D2": ExperimentLayerConfig(
        include_d1_attention=True,
        include_d2_general_priors=True,
    ),
    "A_B_C_D3": ExperimentLayerConfig(include_d3_demonstrations=True),
    "A_B_C_Bplus_D1_D2_D3": ExperimentLayerConfig(
        include_b_layer_candidates=True,
        include_d1_attention=True,
        include_d2_general_priors=True,
        include_d3_demonstrations=True,
    ),
}

DEFAULT_PROBES = [
    "毒队遇到星陨队，应该先看什么？",
    "贝古斯只有 4 能量时，毒队为什么可能接翼王水刃？",
    "翼王斩杀线能不能直接套百分比？",
    "雷暴翼王队是不是无脑鳗鱼首发？",
    "有贝古斯的队伍是不是都靠贝古斯当核心？",
    "水刃的技能文本是什么？",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run P10h app-path Agent harness probes.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--condition", choices=sorted(CONDITIONS), action="append")
    parser.add_argument("--probe-file", type=Path)
    parser.add_argument("--native", action="store_true", help="Use same request-scoped native runtime as /chat.")
    parser.add_argument("--provider-base-url")
    parser.add_argument("--model")
    parser.add_argument("--api-key-env", default="ROCO_OPENAI_API_KEY")
    parser.add_argument("--reasoning-mode", choices=["disabled", "enabled"], default="disabled")
    parser.add_argument("--reasoning-effort", choices=["none", "high", "max"], default="none")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    conditions = args.condition or list(CONDITIONS)
    probes = _load_probes(args.probe_file)
    runtime_config = _runtime_config_from_args(args) if args.native else RequestRuntimeConfig(
        mode=RequestRuntimeMode.DETERMINISTIC
    )

    manifest = {
        "purpose": "P10h harness runs the same AdvisorService.chat -> AdvisorAgent path used by app /chat.",
        "same_as_app_path": [
            "api.services.advisor_service.AdvisorService.chat",
            "advisor.runtime.AdvisorAgent",
            "AdvisorAgent retrieve_doc_context tool interface",
            "request-scoped runtime config when --native is used",
        ],
        "layer_mapping": {
            "A": "data/runtime/battle_dex.sqlite via BattleDexRepository and team context validation",
            "B": "wiki/compiled/* via DocContextRetriever",
            "Bplus": "artifacts/p10h_intuition_demo_pack/b_layer_archetype_prior_candidates.yaml via experimental retriever only",
            "C": "AdvisorAgent instructions, confidence notes, runtime headers, persona boundary, provider safety policy",
            "D1": "artifacts/p10h_intuition_demo_pack/tactical_intuition_primitives.yaml",
            "D2": "artifacts/p10h_intuition_demo_pack/expert_tactical_priors.yaml",
            "D3": "artifacts/p10h_intuition_demo_pack/long_demonstrations.yaml",
        },
        "conditions": {name: CONDITIONS[name].__dict__ | {"d_pack_dir": str(CONDITIONS[name].d_pack_dir)} for name in conditions},
        "native": args.native,
        "model": args.model if args.native else None,
        "provider_base_url": args.provider_base_url if args.native else None,
        "reasoning_mode": args.reasoning_mode if args.native else None,
        "reasoning_effort": args.reasoning_effort if args.native else None,
        "probes": probes,
    }
    (args.output_dir / "harness_manifest.yaml").write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    results: list[dict[str, Any]] = []
    for condition_name in conditions:
        service = AdvisorService.from_db_path(
            default_backend="deterministic",
            managed_persona_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
        )
        layer_config = CONDITIONS[condition_name]
        service.doc_retriever_factory = lambda layer_config=layer_config: P10hExperimentDocContextRetriever(
            layer_config
        )
        for idx, probe in enumerate(probes, start=1):
            session_id, response = service.chat(
                message=probe,
                session_id=f"p10h-{condition_name}-{idx}",
                runtime_config=runtime_config,
            )
            results.append(
                {
                    "condition": condition_name,
                    "probe_index": idx,
                    "probe": probe,
                    "session_id": session_id,
                    "status": response.status,
                    "backend": response.backend,
                    "analysis_type": response.analysis_type,
                    "answer": response.answer,
                    "tool_results": [tool.model_dump(mode="json") for tool in response.tool_results],
                    "evidence": [item.model_dump(mode="json") for item in response.evidence],
                    "confidence_notes": [note.model_dump(mode="json") for note in response.confidence_notes],
                    "followup_options": [option.model_dump(mode="json") for option in response.followup_options],
                }
            )

    (args.output_dir / "raw_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.output_dir / "review_packet.md").write_text(_review_packet(results), encoding="utf-8")
    print(f"wrote {args.output_dir}")
    print(f"conditions={len(conditions)} probes={len(probes)} answers={len(results)}")
    return 0


def _runtime_config_from_args(args: argparse.Namespace) -> RequestRuntimeConfig:
    api_key = os.getenv(args.api_key_env, "").strip()
    if not api_key or not args.provider_base_url or not args.model:
        raise SystemExit(
            "--native requires --provider-base-url, --model, and API key in "
            f"{args.api_key_env}"
        )
    return RequestRuntimeConfig(
        mode=RequestRuntimeMode.NATIVE,
        native_model_config=RocoNativeModelConfig(
            api_key=api_key,
            base_url=args.provider_base_url,
            model_name=args.model,
            reasoning_mode=args.reasoning_mode,
            reasoning_effort=None if args.reasoning_effort == "none" else args.reasoning_effort,
        ),
    )


def _load_probes(path: Path | None) -> list[str]:
    if path is None:
        return list(DEFAULT_PROBES)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [str(item) for item in data]
    if isinstance(data, dict) and isinstance(data.get("probes"), list):
        return [str(item) for item in data["probes"]]
    raise SystemExit("probe file must be a YAML list or {probes: [...]}")


def _review_packet(results: list[dict[str, Any]]) -> str:
    lines = [
        "# P10h Agent Harness Review Packet",
        "",
        "This packet is generated from the same AdvisorService.chat -> AdvisorAgent path used by app /chat.",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"## {result['condition']} / Probe {result['probe_index']}",
                "",
                f"Question: {result['probe']}",
                "",
                f"Backend: `{result['backend']}`",
                "",
                "Answer:",
                "",
                result["answer"],
                "",
                "Tool results:",
            ]
        )
        for tool in result["tool_results"]:
            lines.append(f"- `{tool['tool_name']}`: {tool['summary']}")
        lines.extend(["", "Evidence labels:"])
        for item in result["evidence"]:
            lines.append(f"- `{item['source_type']}` `{item['source_label']}`: {item['retrieval_reason']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
