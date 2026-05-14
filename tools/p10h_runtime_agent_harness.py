#!/usr/bin/env python3
"""P10h Prebattle Ablation — Runtime Agent Harness.

Creates standalone pydantic-ai Agent instances with per-level tool gating.
Does not go through the Roco API — tools access BattleDexRepository directly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p10h_agent_factory import LEVEL_TOOLS, create_agent

ARTIFACT_ROOT = ROOT / "artifacts" / "p10h_prebattle_ablation"
INPUTS_DIR = ARTIFACT_ROOT / "inputs"
LEVELS = ("L0", "L1", "L2", "L3-exact", "L3-transfer")
DEFAULT_MODEL = os.environ.get("ROCO_ADVISOR_MODEL", "deepseek-v4-pro")
DEFAULT_PROVIDER_URL = os.environ.get(
    "ROCO_OPENAI_BASE_URL", "https://api.deepseek.com"
)


def _load_cases(case_dir: Path) -> list[dict[str, Any]]:
    """Load case YAML files, sorted by case_order."""
    cases: list[dict[str, Any]] = []
    for path in sorted(case_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict) and data.get("case_id"):
            cases.append(data)
    cases.sort(key=lambda c: int(c.get("case_order", 0)))
    return cases


def _build_task_message(case: dict[str, Any]) -> str:
    """Build the prebattle preview task message."""
    our = [s["display_name"] for s in case.get("our_team", [])]
    opp = [s["display_name"] for s in case.get("opponent_team", [])]
    return (
        f"你正在进行一场高分段对战预览。双方队伍均为6v6明牌，技能配置/性格/个体值/愿力未知。\n\n"
        f"我方队伍：{'、'.join(our)}\n"
        f"对方队伍：{'、'.join(opp)}\n\n"
        f"请分析这场对战：\n"
        f"1. 首发建议及理由\n"
        f"2. 关键对位分析\n"
        f"3. 前两层博弈树\n"
        f"4. 风险与当前信息不足的标注"
    )


def _build_what_if_message(question: str) -> str:
    return f"补充问题：{question}"


async def _run_call(
    case: dict[str, Any],
    level: str,
    repeat: int,
    *,
    model_name: str,
    provider_url: str,
    api_key: str,
) -> dict[str, Any]:
    """Run a single experiment call: create agent, send task + what-if, collect response."""
    case_id = case["case_id"]
    run_id = f"{case_id}__{level.lower().replace('-', '_')}__r{repeat:02d}"
    t0 = time.monotonic()

    agent = create_agent(
        level,
        model_name=model_name,
        provider_base_url=provider_url,
        provider_api_key=api_key,
    )

    # Main task
    task = _build_task_message(case)
    if level in ("L3-exact", "L3-transfer"):
        task += f"\n\n[内部 case_id: {case_id}]"  # needed for D-layer tool param
    result = await agent.run(task)
    main_answer = result.output if hasattr(result, "output") else str(result)

    # What-if questions
    what_if_answers: list[dict[str, str]] = []
    answer_key = case.get("answer_key", {})
    if isinstance(answer_key, dict):
        for wi in answer_key.get("what_if_questions", []):
            if isinstance(wi, dict) and wi.get("question"):
                wi_msg = _build_what_if_message(wi["question"])
                wi_result = await agent.run(wi_msg)
                wi_answer = wi_result.output if hasattr(wi_result, "output") else str(wi_result)
                what_if_answers.append(
                    {"question": wi["question"], "answer": wi_answer}
                )

    elapsed = time.monotonic() - t0
    return {
        "run_id": run_id,
        "case_id": case_id,
        "case_label": case.get("case_label", ""),
        "case_order": case.get("case_order", 0),
        "level": level,
        "repeat": repeat,
        "status": "ok",
        "latency_seconds": round(elapsed, 1),
        "model": model_name,
        "answer": main_answer,
        "what_if_answers": what_if_answers,
    }


def _build_blind_id(run_id: str) -> str:
    return hashlib.sha256(run_id.encode()).hexdigest()[:10]


async def _run_all(
    cases: list[dict[str, Any]],
    *,
    levels: tuple[str, ...],
    repeats: int,
    model_name: str,
    provider_url: str,
    api_key: str,
    output_dir: Path,
    dry_run: bool,
    max_calls: int,
) -> None:
    """Execute the full experiment grid."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir = output_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Build run plan
    plan: list[tuple[dict[str, Any], str, int]] = []
    for case in cases:
        for level in levels:
            for r in range(1, repeats + 1):
                plan.append((case, level, r))

    if max_calls and max_calls < len(plan):
        plan = plan[:max_calls]

    print(f"run plan: {len(plan)} calls ({len(cases)} cases × {len(levels)} levels × {repeats} repeats)")
    if dry_run:
        for case, level, repeat in plan:
            run_id = f"{case['case_id']}__{level.lower().replace('-', '_')}__r{repeat:02d}"
            print(f"  dry-run: {run_id}")
        print(f"dry-run: would execute {len(plan)} calls")
        return

    results: list[dict[str, Any]] = []
    for i, (case, level, repeat) in enumerate(plan):
        run_id = f"{case['case_id']}__{level.lower().replace('-', '_')}__r{repeat:02d}"
        print(f"[{i+1}/{len(plan)}] {run_id} ...", end=" ", flush=True)
        try:
            result = await _run_call(
                case, level, repeat,
                model_name=model_name,
                provider_url=provider_url,
                api_key=api_key,
            )
            results.append(result)
            status = result.get("status", "?")
            latency = result.get("latency_seconds", 0)
            print(f"{status} {latency:.1f}s")

            # Write individual output
            out_path = outputs_dir / f"{run_id}.json"
            out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"FAIL {exc}")
            results.append({
                "run_id": run_id,
                "case_id": case["case_id"],
                "level": level,
                "repeat": repeat,
                "status": "error",
                "error": str(exc),
            })

    # Write aggregate results
    raw_path = output_dir / "raw_results.json"
    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    # Build blind review packet
    blind_items = []
    for r in results:
        if r.get("status") != "ok":
            continue
        blind_id = _build_blind_id(r["run_id"])
        blind_items.append({
            "blind_id": blind_id,
            "run_id": r["run_id"],
            "case_id": r["case_id"],
            "level": r["level"],
            "repeat": r["repeat"],
            "answer": r.get("answer", ""),
            "what_if_answers": r.get("what_if_answers", []),
        })
    blind_dir = output_dir / "blind_review"
    blind_dir.mkdir(parents=True, exist_ok=True)
    blind_path = blind_dir / "blind_review_packet.json"
    blind_path.write_text(json.dumps(blind_items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote blind packet items={len(blind_items)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="P10h Runtime Agent Harness")
    sub = parser.add_subparsers(dest="command")

    run_cmd = sub.add_parser("run", help="Run experiment calls")
    run_cmd.add_argument("--output-dir", default=str(ARTIFACT_ROOT))
    run_cmd.add_argument("--case-dir", default=str(INPUTS_DIR))
    run_cmd.add_argument("--level", action="append", choices=LEVELS, default=None)
    run_cmd.add_argument("--repeats", type=int, default=3)
    run_cmd.add_argument("--model", default=DEFAULT_MODEL)
    run_cmd.add_argument("--provider-base-url", default=DEFAULT_PROVIDER_URL)
    run_cmd.add_argument("--api-key-env", default="ROCO_OPENAI_API_KEY")
    run_cmd.add_argument("--dry-run", action="store_true")
    run_cmd.add_argument("--max-calls", type=int, default=0)

    args = parser.parse_args()
    if args.command != "run":
        parser.print_help()
        return

    import asyncio

    api_key = os.environ.get(args.api_key_env, "")
    if not api_key:
        print(f"missing API key env {args.api_key_env}", file=sys.stderr)
        sys.exit(2)

    levels = tuple(args.level) if args.level else LEVELS
    cases = _load_cases(Path(args.case_dir))

    asyncio.run(
        _run_all(
            cases,
            levels=levels,
            repeats=args.repeats,
            model_name=args.model,
            provider_url=args.provider_base_url,
            api_key=api_key,
            output_dir=Path(args.output_dir),
            dry_run=args.dry_run,
            max_calls=args.max_calls,
        )
    )


if __name__ == "__main__":
    main()
