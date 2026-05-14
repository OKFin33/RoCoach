#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from advisor.battle_dex import BattleDexRepository, DEFAULT_RUNTIME_DB  # noqa: E402
from api.runtime_headers import redact_runtime_text  # noqa: E402


ARTIFACT_ROOT = ROOT / "artifacts" / "p10h_prebattle_ablation"
D_PACK_DIR = ROOT / "artifacts" / "p10h_intuition_demo_pack"
WIKI_CHUNKS = ROOT / "wiki" / "compiled" / "chunks.jsonl"
D_SELECTION_MANIFEST = ARTIFACT_ROOT / "d_layer_selection_manifest.yaml"

LEVELS = ("L0", "L1", "L2", "L3-exact", "L3-transfer")
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_PROVIDER_BASE_URL = "https://api.deepseek.com"

ANSWER_SHAPE = """## 首发建议
- 我方首发:
- 理由:
- 备选首发:

## 关键对位
1. 我方 X vs 对方 Y: 优势/劣势/中立
   - 理由:
2. ...
3. ...

## 前两层博弈树
- 如果对方首发 A:
  - 我方应对:
  - 如果对方下一步切/点 B:
    - 我方下一步:
- 如果对方首发 C:
  - 我方应对:
  - 如果对方下一步切/点 D:
    - 我方下一步:

## 风险与不确定性
- 隐藏配置/技能/愿力可能导致结论变化:
- 当前信息不足:
"""


@dataclass(frozen=True)
class RunConfig:
    output_dir: Path
    case_dir: Path
    levels: tuple[str, ...]
    repeats: int
    seed: int
    provider_base_url: str
    model: str
    api_key_env: str
    reasoning_mode: str
    reasoning_effort: str
    temperature: float
    dry_run: bool
    max_calls: int | None


def main() -> int:
    parser = argparse.ArgumentParser(description="P10h controlled L0-L3 prebattle ablation harness.")
    sub = parser.add_subparsers(dest="command", required=True)

    scaffold = sub.add_parser("scaffold", help="Create directories and case template files.")
    scaffold.add_argument("--output-dir", type=Path, default=ARTIFACT_ROOT)
    scaffold.add_argument("--overwrite", action="store_true")

    build = sub.add_parser("build", help="Validate cases and build grounding packs/prompts/run order.")
    _add_common_args(build)
    build.add_argument("--allow-incomplete-answer-key", action="store_true")

    run = sub.add_parser("run", help="Run model calls from prepared prompts.")
    _add_common_args(run)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--max-calls", type=int)

    blind = sub.add_parser("blind", help="Build blind review packet from outputs.")
    blind.add_argument("--output-dir", type=Path, default=ARTIFACT_ROOT)
    blind.add_argument("--seed", type=int, default=1009)

    args = parser.parse_args()
    if args.command == "scaffold":
        return scaffold_cases(args.output_dir, overwrite=args.overwrite)
    if args.command == "build":
        cfg = _config_from_args(args, dry_run=True)
        return build_artifacts(cfg, allow_incomplete_answer_key=args.allow_incomplete_answer_key)
    if args.command == "run":
        cfg = _config_from_args(args, dry_run=args.dry_run)
        return run_generation(cfg)
    if args.command == "blind":
        return build_blind_packet(args.output_dir, seed=args.seed)
    raise AssertionError(args.command)


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir", type=Path, default=ARTIFACT_ROOT)
    parser.add_argument("--case-dir", type=Path)
    parser.add_argument("--level", choices=LEVELS, action="append")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1009)
    parser.add_argument("--provider-base-url", default=DEFAULT_PROVIDER_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key-env", default="ROCO_OPENAI_API_KEY")
    parser.add_argument("--reasoning-mode", choices=["disabled", "enabled"], default="enabled")
    parser.add_argument("--reasoning-effort", choices=["none", "high", "max"], default="high")
    parser.add_argument("--temperature", type=float, default=0.3)


def _config_from_args(args: argparse.Namespace, *, dry_run: bool) -> RunConfig:
    output_dir = args.output_dir
    return RunConfig(
        output_dir=output_dir,
        case_dir=args.case_dir or output_dir / "inputs",
        levels=tuple(args.level or LEVELS),
        repeats=max(1, args.repeats),
        seed=args.seed,
        provider_base_url=args.provider_base_url,
        model=args.model,
        api_key_env=args.api_key_env,
        reasoning_mode=args.reasoning_mode,
        reasoning_effort=args.reasoning_effort,
        temperature=args.temperature,
        dry_run=dry_run,
        max_calls=getattr(args, "max_calls", None),
    )


def scaffold_cases(output_dir: Path, *, overwrite: bool) -> int:
    input_dir = output_dir / "inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    for case in _default_case_templates():
        path = input_dir / f"{case['case_id']}.yaml"
        if path.exists() and not overwrite:
            continue
        path.write_text(yaml.safe_dump(case, allow_unicode=True, sort_keys=False), encoding="utf-8")

    (output_dir / "README.md").write_text(_experiment_readme(), encoding="utf-8")
    print(f"scaffolded {input_dir}")
    return 0


def build_artifacts(cfg: RunConfig, *, allow_incomplete_answer_key: bool = False) -> int:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    for dirname in ("grounding_packs", "prompts", "outputs", "blind_review", "reveal", "analysis"):
        (cfg.output_dir / dirname).mkdir(parents=True, exist_ok=True)

    cases = _load_cases(cfg.case_dir)
    validation_errors = _validate_cases(cases, allow_incomplete_answer_key=allow_incomplete_answer_key)
    validation_report = {
        "case_count": len(cases),
        "levels": list(cfg.levels),
        "repeats": cfg.repeats,
        "validation_errors": validation_errors,
    }
    _write_yaml(cfg.output_dir / "analysis" / "validation_report.yaml", validation_report)
    if validation_errors and not allow_incomplete_answer_key:
        for error in validation_errors:
            print(f"validation_error: {error}", file=sys.stderr)
        return 2

    repo = BattleDexRepository(DEFAULT_RUNTIME_DB)
    all_runs: list[dict[str, Any]] = []
    for case in cases:
        case_id = case["case_id"]
        for level in cfg.levels:
            grounding = build_grounding_pack(case, level=level, repo=repo)
            grounding_path = cfg.output_dir / "grounding_packs" / case_id / f"{level}.md"
            prompt_path = cfg.output_dir / "prompts" / case_id / f"{level}.md"
            grounding_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            grounding_path.write_text(grounding, encoding="utf-8")
            prompt = build_prompt(case, grounding=grounding)
            prompt_path.write_text(prompt, encoding="utf-8")
            for repeat in range(1, cfg.repeats + 1):
                run_id = _run_id(case_id, level, repeat)
                all_runs.append(
                    {
                        "run_id": run_id,
                        "case_id": case_id,
                        "case_label": case.get("case_label"),
                        "case_order": case.get("case_order"),
                        "level": level,
                        "repeat": repeat,
                        "prompt_path": str(prompt_path.relative_to(cfg.output_dir)),
                        "grounding_path": str(grounding_path.relative_to(cfg.output_dir)),
                    }
                )

    rng = random.Random(cfg.seed)
    rng.shuffle(all_runs)
    _write_json(cfg.output_dir / "run_order.json", all_runs)
    _write_yaml(
        cfg.output_dir / "run_manifest.yaml",
        {
            "plan_source": "artifacts/p10h_prebattle_ablation_experiment_plan_2026_05_01.md",
            "model": cfg.model,
            "provider_base_url": cfg.provider_base_url,
            "reasoning_mode": cfg.reasoning_mode,
            "reasoning_effort": cfg.reasoning_effort,
            "temperature": cfg.temperature,
            "levels": list(cfg.levels),
            "repeats": cfg.repeats,
            "seed": cfg.seed,
            "call_count": len(all_runs),
        },
    )
    print(f"built prompts for cases={len(cases)} calls={len(all_runs)} at {cfg.output_dir}")
    return 0


def run_generation(cfg: RunConfig) -> int:
    build_code = build_artifacts(cfg)
    if build_code != 0:
        return build_code

    run_order_path = cfg.output_dir / "run_order.json"
    run_order = json.loads(run_order_path.read_text(encoding="utf-8"))
    if cfg.max_calls is not None:
        run_order = run_order[: max(0, cfg.max_calls)]

    if cfg.dry_run:
        print(f"dry-run: would execute {len(run_order)} calls")
        return 0

    api_key = os.getenv(cfg.api_key_env, "").strip()
    if not api_key:
        print(f"missing API key env {cfg.api_key_env}", file=sys.stderr)
        return 2

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=cfg.provider_base_url, timeout=180.0)
    raw_results: list[dict[str, Any]] = []
    for item in run_order:
        prompt = (cfg.output_dir / item["prompt_path"]).read_text(encoding="utf-8")
        started = time.time()
        status = "ok"
        answer = ""
        error = None
        usage = None
        try:
            kwargs: dict[str, Any] = {"temperature": cfg.temperature}
            marker = f"{cfg.model} {cfg.provider_base_url}".casefold()
            if "deepseek" in marker:
                kwargs["extra_body"] = {
                    "thinking": {"type": "enabled" if cfg.reasoning_mode == "enabled" else "disabled"}
                }
                if cfg.reasoning_mode == "enabled" and cfg.reasoning_effort != "none":
                    kwargs["reasoning_effort"] = cfg.reasoning_effort
            response = client.chat.completions.create(
                model=cfg.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are evaluating Roco prebattle preview reasoning. "
                            "Return only the requested final answer. Do not reveal hidden chain-of-thought."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                **kwargs,
            )
            answer = response.choices[0].message.content or ""
            usage = response.usage.model_dump(mode="json") if response.usage is not None else None
        except Exception as exc:  # noqa: BLE001 - artifact records provider errors safely
            status = "failed"
            error = exc.__class__.__name__

        latency = time.time() - started
        safe_answer = redact_runtime_text(
            answer,
            provider_key=api_key,
            provider_base_url=cfg.provider_base_url,
            model=cfg.model,
        )
        result = {
            **item,
            "status": status,
            "latency_seconds": round(latency, 3),
            "model": cfg.model,
            "provider_base_url": "[REDACTED]",
            "reasoning_mode": cfg.reasoning_mode,
            "reasoning_effort": cfg.reasoning_effort,
            "temperature": cfg.temperature,
            "answer": safe_answer,
            "usage": usage,
            "error": error,
        }
        raw_results.append(result)
        out_path = cfg.output_dir / "outputs" / f"{item['run_id']}.json"
        _write_json(out_path, result)
        print(f"{item['run_id']} {status} {latency:.1f}s")

    _write_json(cfg.output_dir / "outputs" / "raw_results.json", raw_results)
    return build_blind_packet(cfg.output_dir, seed=cfg.seed)


def build_blind_packet(output_dir: Path, *, seed: int) -> int:
    outputs_dir = output_dir / "outputs"
    result_files = sorted(path for path in outputs_dir.glob("*.json") if path.name != "raw_results.json")
    results = [json.loads(path.read_text(encoding="utf-8")) for path in result_files]
    rng = random.Random(seed)
    blind_items = []
    reveal = []
    for result in results:
        blind_id = hashlib.sha256(f"{result['run_id']}:{seed}".encode()).hexdigest()[:10]
        blind_items.append(
            {
                "blind_id": blind_id,
                "case_id": result["case_id"],
                "case_label": result.get("case_label"),
                "case_order": result.get("case_order"),
                "answer": result.get("answer", ""),
                "status": result.get("status"),
            }
        )
        reveal.append(
            {
                "blind_id": blind_id,
                "run_id": result["run_id"],
                "case_id": result["case_id"],
                "case_label": result.get("case_label"),
                "case_order": result.get("case_order"),
                "level": result["level"],
                "repeat": result["repeat"],
            }
        )
    rng.shuffle(blind_items)
    _write_json(output_dir / "reveal" / "reveal_map.json", reveal)
    _write_json(output_dir / "blind_review" / "blind_review_packet.json", blind_items)
    (output_dir / "blind_review" / "blind_review_packet.md").write_text(
        _blind_markdown(blind_items),
        encoding="utf-8",
    )
    _write_score_template(output_dir / "blind_review" / "score_sheet_template.csv", blind_items)
    _write_failure_log_template(output_dir / "blind_review" / "primitive_failure_log_template.csv", blind_items)
    print(f"wrote blind packet items={len(blind_items)}")
    return 0


def build_grounding_pack(case: dict[str, Any], *, level: str, repo: BattleDexRepository) -> str:
    lines = [
        "# Grounding Pack",
        "",
        f"Case: {case['case_id']}",
        f"Level: {level}",
        "",
        "## Domain Boundary",
        "",
        "- 洛克王国世界语境，不使用宝可梦/EV/道具/Tera/可选特性假设。",
        "- 预览阶段双方队伍可见，但技能、性格、个体、愿力/血脉通常未知，除非输入明确给出。",
    ]
    if level == "L0":
        return "\n".join(lines) + "\n"

    lines.extend(["", "## A-Layer Species Cards", ""])
    for side_key, side_label in (("our_team", "我方"), ("opponent_team", "对方")):
        for slot in case.get(side_key, []):
            lines.append(_species_card(repo, slot, side_label=side_label))

    if level == "L1":
        return "\n".join(lines) + "\n"

    lines.extend(["", "## B-Layer Snippets", ""])
    for snippet in _select_b_snippets(case):
        lines.append(snippet)

    if level == "L2":
        return "\n".join(lines) + "\n"

    lines.extend(["", f"## D-Layer Material ({level})", ""])
    lines.extend(_d_layer_use_rule(level))
    for snippet in _select_d_material(case, level=level):
        lines.append(snippet)
    return "\n".join(lines) + "\n"


def _d_layer_use_rule(level: str) -> list[str]:
    if level == "L3-transfer":
        return [
            "### D3 Transfer Use Rule",
            "",
            "- 以下 D3 examples 来自相关但不同的场景；它们不是当前任务的答案。",
            "- 不要复制其中的精灵选择、首发结论、伤害判断或 matchup 结论。",
            "- 只能迁移分析方法：先识别队伍/资源引擎，再检查默认路线是否有例外，再做分支树，再声明隐藏配置和不确定性。",
            "- 当前任务结论必须由当前队伍、A-layer facts、B-layer mechanics 和任务输入决定。",
            "",
        ]
    if level == "L3-exact":
        return [
            "### D3 Exact Use Rule",
            "",
            "- 以下 D3 examples 与当前任务高度相关，可作为专家示范，但仍不能照抄。",
            "- 必须根据当前任务输入重构答案，并保留隐藏配置、技能、性格、个体、愿力/血脉未知的边界。",
            "",
        ]
    return []


def build_prompt(case: dict[str, Any], *, grounding: str) -> str:
    return "\n\n".join(
        [
            "你是洛克王国世界对战教练。请基于给定任务和参考资料回答，不要使用未给出的隐藏配置。",
            (
                "答案必须像直接给玩家的对战建议。禁止提及内部实验/软件元信息，包括但不限于: "
                "grounding、参考资料、A-layer、B-layer、D-layer、B+、L0/L1/L2/L3、"
                "检索、模型、prompt、source、素材、源素材、标准答案。"
            ),
            "先完成主任务。若任务输入包含 What-If 子问题，在主任务之后用 `## What-If 检查` 逐题回答。",
            "主任务输出必须使用以下结构：",
            ANSWER_SHAPE,
            "## 任务输入",
            _case_task_markdown(case),
            "## 内部参考资料（只能用于作答，不可在答案中提及此标题或来源）",
            grounding,
        ]
    )


def _case_task_markdown(case: dict[str, Any]) -> str:
    lines = [
        f"- 任务: {case.get('task', 'prebattle_preview')}",
        f"- 场景: {case.get('visible_context', {}).get('rank_or_scene', 'unknown')}",
        "",
        "我方队伍:",
    ]
    for slot in case.get("our_team", []):
        lines.append(f"- {slot.get('display_name')} ({slot.get('species_id', 'unknown')})")
    lines.append("")
    lines.append("对方队伍:")
    for slot in case.get("opponent_team", []):
        lines.append(f"- {slot.get('display_name')} ({slot.get('species_id', 'unknown')})")
    what_if_questions = (case.get("answer_key") or {}).get("what_if_questions") or []
    if what_if_questions:
        lines.extend(["", "What-If 子问题:"])
        for index, item in enumerate(what_if_questions, start=1):
            question = item.get("question") if isinstance(item, dict) else str(item)
            if question:
                lines.append(f"{index}. {question}")
    return "\n".join(lines)


def _species_card(repo: BattleDexRepository, slot: dict[str, Any], *, side_label: str) -> str:
    query = slot.get("species_id") or slot.get("display_name")
    if not query:
        return f"- {side_label}: unresolved slot {slot}"
    profile = repo.get_species_profile(str(query))
    if profile is None:
        return f"- {side_label} {slot.get('display_name', query)}: A-layer lookup failed; treat exact facts as unresolved."
    moves = repo.get_species_available_moves(profile.species_id, limit=12)
    move_text = "；".join(
        f"{move.move_name}({move.move_type or '-'}, {move.category_raw or '-'}, power={move.power or '?'}, effect={move.effect_text or '-'})"
        for move in moves[:8]
    )
    stats = profile.base_stats
    return (
        f"### {side_label} {profile.display_name}\n"
        f"- species_id: {profile.species_id}\n"
        f"- type: {profile.primary_type}/{profile.secondary_type or '-'}\n"
        f"- ability: {profile.ability_name or 'unknown'} - {profile.ability_effect_text or 'unknown'}\n"
        f"- base_stats: HP={stats.hp}, 物攻={stats.atk}, 物防={stats.defense}, 魔攻={stats.spa}, 魔防={stats.spd}, 速度={stats.spe}, BST={stats.bst}\n"
        f"- known available moves sample: {move_text or 'none'}\n"
        f"- hidden preview variables: selected moves/nature/individual bonuses/wish-force are unknown unless task states otherwise.\n"
    )


def _select_b_snippets(case: dict[str, Any]) -> list[str]:
    query = " ".join(_case_terms(case))
    chunks = []
    if WIKI_CHUNKS.exists():
        for line in WIKI_CHUNKS.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            chunk = json.loads(line)
            text = f"{chunk.get('title','')} {chunk.get('section','')} {chunk.get('text','')}"
            score = _text_overlap_score(query, text)
            if score > 0:
                chunks.append((score, chunk))
    chunks.sort(key=lambda item: (-item[0], item[1].get("chunk_id", "")))
    selected = []
    for _score, chunk in chunks[:4]:
        selected.append(
            f"### {chunk.get('title')} / {chunk.get('section')}\n"
            f"source: wiki/{chunk.get('page')}\n\n"
            f"{chunk.get('text')}\n"
        )

    # Add draft Bplus candidates as B-context in controlled L2/L3, because the
    # current plan explicitly separates concrete archetype knowledge from D2.
    bplus_path = D_PACK_DIR / "b_layer_archetype_prior_candidates.yaml"
    for item in _rank_yaml_items(bplus_path, query, key="items")[:3]:
        selected.append("### Bplus candidate: " + _compact_yaml_item(item))
    return selected or ["No relevant B-layer snippets selected."]


def _select_d_material(case: dict[str, Any], *, level: str) -> list[str]:
    source_ref = str(case.get("source_ref", ""))
    query = " ".join(_case_terms(case))
    demos = _load_yaml_items(D_PACK_DIR / "long_demonstrations.yaml", key="demos")
    manifest_ids = _select_manifest_demo_ids(case, level=level)
    if manifest_ids:
        demos_by_id = {str(item.get("id")): item for item in demos if item.get("id")}
        selected = [demos_by_id[demo_id] for demo_id in manifest_ids if demo_id in demos_by_id]
        missing = [demo_id for demo_id in manifest_ids if demo_id not in demos_by_id]
        snippets = ["### D3 demo: " + _compact_yaml_item(item) for item in selected]
        snippets.extend(f"### D3 demo missing: id: {demo_id}" for demo_id in missing)
        return snippets or ["No D-layer material selected."]
    if level == "L3-exact":
        selected = [
            item for item in demos if source_ref and source_ref in " ".join(map(str, item.get("source_scope", [])))
        ]
    else:
        selected = [
            item for item in _rank_items(demos, query)
            if not source_ref or source_ref not in " ".join(map(str, item.get("source_scope", [])))
        ][:2]
    if not selected:
        selected = _rank_items(demos, query)[:2]
    return ["### D3 demo: " + _compact_yaml_item(item) for item in selected] or ["No D-layer material selected."]


def _select_manifest_demo_ids(case: dict[str, Any], *, level: str) -> list[str]:
    if not D_SELECTION_MANIFEST.exists():
        return []
    data = yaml.safe_load(D_SELECTION_MANIFEST.read_text(encoding="utf-8")) or {}
    selections = data.get("selections") if isinstance(data, dict) else {}
    case_selection = selections.get(str(case.get("case_id", "")), {}) if isinstance(selections, dict) else {}
    level_selection = case_selection.get(level, {}) if isinstance(case_selection, dict) else {}
    demo_ids = level_selection.get("demo_ids") if isinstance(level_selection, dict) else []
    return [str(demo_id) for demo_id in demo_ids or []]


def _rank_yaml_items(path: Path, query: str, *, key: str) -> list[dict[str, Any]]:
    return _rank_items(_load_yaml_items(path, key=key), query)


def _rank_items(items: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    scored = [(_text_overlap_score(query, yaml.safe_dump(item, allow_unicode=True)), item) for item in items]
    return [item for score, item in sorted(scored, key=lambda pair: -pair[0]) if score > 0]


def _load_yaml_items(path: Path, *, key: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = data.get(key, [])
    return items if isinstance(items, list) else []


def _compact_yaml_item(item: dict[str, Any]) -> str:
    fields = []
    for key in (
        "id",
        "title",
        "claim",
        "situation",
        "expert_frame",
        "reasoning_chain",
        "decision_boundary",
        "what_to_imitate",
        "not_to_infer",
        "do_not_overclaim",
        "blockers",
    ):
        value = item.get(key)
        if value:
            fields.append(f"{key}: {_compact(value)}")
    return " ".join(fields)[:2400]


def _compact(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "；".join(_compact(item) for item in value)
    if isinstance(value, dict):
        return "；".join(f"{key}={_compact(nested)}" for key, nested in value.items())
    return str(value)


def _case_terms(case: dict[str, Any]) -> list[str]:
    terms = [str(case.get("case_id", "")), str(case.get("source_ref", ""))]
    for side in ("our_team", "opponent_team"):
        for slot in case.get(side, []):
            terms.append(str(slot.get("display_name", "")))
            terms.append(str(slot.get("species_id", "")))
    terms.extend(str(tag) for tag in case.get("visible_context", {}).get("meta_tags", []))
    return [term for term in terms if term]


def _text_overlap_score(query: str, text: str) -> int:
    score = 0
    for term in _terms_for_overlap(query):
        if term and term in text:
            score += 1 + min(len(term), 6)
    return score


def _terms_for_overlap(text: str) -> list[str]:
    raw = text.replace("_", " ").replace("-", " ").replace("/", " ")
    terms = [part.strip() for part in raw.split() if len(part.strip()) >= 2]
    important = [
        "星陨",
        "毒",
        "龙息帕尔",
        "落陨星兔",
        "圣羽翼王",
        "翼王",
        "贝古斯",
        "闪电鳗鱼",
        "星光狮",
        "画间沉铁兽",
        "琉璃水母",
        "厉毒修萝",
        "裘卡",
        "寒音蛇",
        "雷暴",
        "印记",
        "迅捷",
        "水刃",
        "倾泻",
        "首发",
        "平衡",
    ]
    return sorted(set([*terms, *(term for term in important if term in text)]), key=len, reverse=True)


def _load_cases(case_dir: Path) -> list[dict[str, Any]]:
    if not case_dir.exists():
        raise SystemExit(f"case dir not found: {case_dir}. Run scaffold first.")
    cases = []
    for path in sorted(case_dir.glob("*.yaml")):
        cases.append(yaml.safe_load(path.read_text(encoding="utf-8")))
    if not cases:
        raise SystemExit(f"no case YAML files found under {case_dir}")
    return sorted(cases, key=_case_sort_key)


def _case_sort_key(case: dict[str, Any]) -> tuple[int, str]:
    raw_order = case.get("case_order", 999)
    try:
        order = int(raw_order)
    except (TypeError, ValueError):
        order = 999
    return (order, str(case.get("case_id", "")))


def _validate_cases(cases: list[dict[str, Any]], *, allow_incomplete_answer_key: bool) -> list[str]:
    errors = []
    for case in cases:
        case_id = case.get("case_id", "<missing>")
        for key in ("case_id", "source_ref", "task", "our_team", "opponent_team", "answer_key"):
            if not case.get(key):
                errors.append(f"{case_id}: missing {key}")
        answer_key = case.get("answer_key") or {}
        if not _has_valid_answer_key(answer_key):
            errors.append(
                f"{case_id}: answer_key must use structured D1/D2/D3 schema "
                "or legacy lead/matchup/tree/risk schema"
            )
        if not allow_incomplete_answer_key and _contains_todo(answer_key):
            errors.append(f"{case_id}: answer_key contains TODO; generation blocked")
    return errors


def _has_valid_answer_key(answer_key: dict[str, Any]) -> bool:
    if not answer_key:
        return False
    structured_required = (
        "archetype_recognition",
        "d1_attention_order",
        "d2_activated_priors",
        "d3_reasoning_chain",
        "evaluation_checklist",
        "what_if_questions",
    )
    legacy_required = (
        "lead_recommendation",
        "key_matchups",
        "two_layer_game_tree",
        "risk_uncertainty",
        "clear_errors",
    )
    return all(answer_key.get(key) for key in structured_required) or all(
        answer_key.get(key) for key in legacy_required
    )


def _contains_todo(value: Any) -> bool:
    if isinstance(value, str):
        return "TODO" in value or "待填写" in value
    if isinstance(value, list):
        return any(_contains_todo(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_todo(item) for item in value.values())
    return False


def _default_case_templates() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "prebattle_wingking_poison_vs_snake_balance",
            "case_label": "Case A",
            "case_order": 1,
            "source_ref": "wingking_poison_0429",
            "task": "prebattle_preview",
            "visible_context": {
                "rank_or_scene": "高分段预览",
                "visibility_rule": "both_teams_visible_hidden_sets",
                "meta_tags": ["wingking_poison", "poison_team", "balance_team"],
            },
            "our_team": [
                {"display_name": "琉璃水母", "species_id": "species_1b751328ed4051ca"},
                {"display_name": "厉毒修萝", "species_id": "species_8fa3669903f06fc3"},
                {"display_name": "裘卡", "species_id": "species_3b0a4ef29e17e262"},
                {"display_name": "圣羽翼王", "species_id": "species_cfef25aadf9439cf"},
                {"display_name": "棋齐垒", "species_id": "species_4895b8afaed29c16"},
                {"display_name": "翠顶夫人", "species_id": "species_85de0fab1c4adfe0"},
            ],
            "opponent_team": [
                {"display_name": "寒音蛇", "species_id": "species_4498ae70b870d198"},
                {"display_name": "贝古斯", "species_id": "species_087583e1f99ab3b3"},
                {"display_name": "寂灭骨龙", "species_id": "species_be4456493fe259d9"},
                {"display_name": "圆号鱼", "species_id": "species_9866399087db6497"},
                {"display_name": "黑猫巫师", "species_id": "species_4bec80fc4236818a"},
                {"display_name": "化蝶", "species_id": "species_c39a753446943920"},
            ],
            "answer_key": _todo_answer_key(),
        },
        {
            "case_id": "prebattle_poison_vs_starfall",
            "case_label": "Case B",
            "case_order": 2,
            "source_ref": "poison_vs_starfall_0430",
            "task": "prebattle_preview",
            "visible_context": {
                "rank_or_scene": "高分段预览",
                "visibility_rule": "both_teams_visible_hidden_sets",
                "meta_tags": ["poison_team", "starfall"],
            },
            "our_team": [
                {"display_name": "裘卡", "species_id": "species_3b0a4ef29e17e262"},
                {"display_name": "琉璃水母", "species_id": "species_1b751328ed4051ca"},
                {"display_name": "厉毒修萝", "species_id": "species_8fa3669903f06fc3"},
                {"display_name": "圣羽翼王", "species_id": "species_cfef25aadf9439cf"},
                {"display_name": "翠顶夫人", "species_id": "species_85de0fab1c4adfe0"},
                {"display_name": "千棘盔", "species_id": "species_c2ca574029b1723d"},
            ],
            "opponent_team": [
                {"display_name": "落陨星兔", "species_id": "species_ec9c92a138461398"},
                {"display_name": "龙息帕尔", "species_id": "species_19b8ad7a8219bd88"},
                {"display_name": "圣羽翼王", "species_id": "species_cfef25aadf9439cf"},
                {"display_name": "权杖-V", "species_id": "species_3d2f11185009b67c"},
                {"display_name": "怖哭菇", "species_id": "species_9cd1d6697584ef00"},
                {"display_name": "翠顶夫人", "species_id": "species_85de0fab1c4adfe0"},
            ],
            "answer_key": _todo_answer_key(),
        },
        {
            "case_id": "prebattle_thunder_wingking_fast_balance",
            "case_label": "Case C",
            "case_order": 3,
            "source_ref": "thunder_wingking_fast_balance_0402",
            "task": "prebattle_preview",
            "visible_context": {
                "rank_or_scene": "高分段预览",
                "visibility_rule": "both_teams_visible_hidden_sets",
                "meta_tags": ["thunder_wingking", "fast_balance"],
            },
            "our_team": [
                {"display_name": "闪电鳗鱼", "species_id": "species_13271d319ef0f054"},
                {"display_name": "星光狮", "species_id": "species_ca356f37a9548d10"},
                {"display_name": "画间沉铁兽", "species_id": "species_9b87effbfbd81380"},
                {"display_name": "圣羽翼王", "species_id": "species_cfef25aadf9439cf"},
                {"display_name": "贝古斯", "species_id": "species_087583e1f99ab3b3"},
                {"display_name": "岚鸟", "species_id": "species_3736163202b1cc32"},
            ],
            "opponent_team": [
                {"display_name": "翠顶夫人", "species_id": "species_85de0fab1c4adfe0"},
                {"display_name": "圣羽翼王", "species_id": "species_cfef25aadf9439cf"},
                {"display_name": "岚鸟", "species_id": "species_3736163202b1cc32"},
                {"display_name": "秩序鱿墨", "species_id": "species_9f65ccb075363272"},
                {"display_name": "朔夜伊芙", "species_id": "species_7be3f56b8785b921"},
                {"display_name": "圆号鱼", "species_id": "species_9866399087db6497"},
            ],
            "answer_key": _todo_answer_key(),
        },
    ]


def _todo_answer_key() -> dict[str, Any]:
    return {
        "archetype_recognition": {
            "description": "TODO: PM fill before generation",
            "what_expert_knew": ["TODO"],
        },
        "d1_attention_order": {"steps": [{"order": 1, "focus": "TODO", "why": "TODO"}]},
        "d2_activated_priors": {"priors": [{"id": "TODO", "activation": "TODO"}]},
        "d3_reasoning_chain": {"steps": [{"step": 1, "action": "TODO", "reasoning": "TODO"}]},
        "conditional_knowledge": {"items": []},
        "evaluation_checklist": {
            "d1_alignment": [{"check": "TODO", "weight": "critical"}],
            "d2_alignment": [{"check": "TODO", "weight": "critical"}],
            "d3_alignment": [{"check": "TODO", "weight": "critical"}],
            "negative_checks": [{"check": "TODO", "severity": "critical"}],
        },
        "what_if_questions": [
            {
                "question": "TODO",
                "purpose": "TODO",
                "key_points": ["TODO"],
            }
        ],
    }


def _experiment_readme() -> str:
    return """# P10h Prebattle Ablation Harness

This directory is generated by `tools/p10h_prebattle_ablation_harness.py` and
follows `artifacts/p10h_prebattle_ablation_experiment_plan_2026_05_01.md`.

## Purpose

This is the controlled L0-L3 harness, not the app-path L4 smoke harness.

- L0: task + minimal Roco coach/domain boundary only.
- L1: L0 + A-layer Battle Dex species cards.
- L2: L1 + selected B-layer wiki snippets and Bplus archetype-prior candidates.
- L3-exact: L2 + same-source D3 long demonstrations, intentionally upper-bound
  and answer-leakage-prone.
- L3-transfer: L2 + related non-identical D3 long demonstrations, primary
  D-layer ROI condition.
- If `d_layer_selection_manifest.yaml` exists, L3 D material is pinned from that
  manifest before any lexical fallback selection is used.

`tools/p10h_experiment_harness.py` remains the app-path/L4 harness through
`AdvisorService.chat -> AdvisorAgent`. Use it for end-to-end parity checks, not
for clean layer ablation.

## Required Gate

Do not run live generation until every `inputs/*.yaml` has a completed
`answer_key`. The default build/run path blocks TODO answer keys because blind
review needs a human anchor before model outputs exist.

Prompt inspection is allowed with:

```bash
.venv/bin/python tools/p10h_prebattle_ablation_harness.py build \\
  --output-dir artifacts/p10h_prebattle_ablation \\
  --allow-incomplete-answer-key
```

## Commands

Scaffold case templates:

```bash
.venv/bin/python tools/p10h_prebattle_ablation_harness.py scaffold \\
  --output-dir artifacts/p10h_prebattle_ablation --overwrite
```

Do not run scaffold with `--overwrite` after PM/external agents have filled
answer keys unless you intentionally want to reset the cases.

Validate and build after PM answer keys are filled:

```bash
.venv/bin/python tools/p10h_prebattle_ablation_harness.py build \\
  --output-dir artifacts/p10h_prebattle_ablation \\
  --repeats 3
```

Run a limited live smoke after validation passes:

```bash
ROCO_OPENAI_API_KEY=... \\
.venv/bin/python tools/p10h_prebattle_ablation_harness.py run \\
  --output-dir artifacts/p10h_prebattle_ablation \\
  --model deepseek-v4-pro \\
  --reasoning-mode enabled \\
  --reasoning-effort high \\
  --repeats 1 \\
  --max-calls 15
```

Full first-pass generation:

```bash
ROCO_OPENAI_API_KEY=... \\
.venv/bin/python tools/p10h_prebattle_ablation_harness.py run \\
  --output-dir artifacts/p10h_prebattle_ablation \\
  --model deepseek-v4-pro \\
  --reasoning-mode enabled \\
  --reasoning-effort high \\
  --repeats 3
```

## Output Layout

- `inputs/`: PM-filled case YAMLs.
- `grounding_packs/`: exact per-case/per-level grounding shown to the model.
- `prompts/`: final per-case/per-level prompts.
- `d_layer_selection_manifest.yaml`: explicit L3-exact/L3-transfer D demo
  selection for the first-pass controlled run.
- `outputs/`: raw redacted model outputs.
- `blind_review/`: randomized review packet and score sheet.
- `blind_review/primitive_failure_log_template.csv`: row-level diagnostic log
  for failed D1/D2/D3 checklist items and their repair targets.
- `reveal/`: blind id to level/case mapping.
- `analysis/`: validation and later analysis artifacts.
"""


def _run_id(case_id: str, level: str, repeat: int) -> str:
    safe_level = level.lower().replace("-", "_")
    return f"{case_id}__{safe_level}__r{repeat:02d}"


def _blind_markdown(items: list[dict[str, Any]]) -> str:
    lines = ["# P10h Prebattle Blind Review Packet", ""]
    for item in items:
        lines.extend(
            [
                f"## {item['blind_id']}",
                "",
                f"Case: `{item['case_id']}`",
                f"Case label: `{item.get('case_label') or 'unlabeled'}`",
                "",
                item.get("answer") or "[no answer]",
                "",
                "Scores:",
                "",
                "- d1_alignment: 0-2",
                "- d2_alignment: 0-2",
                "- d3_alignment: 0-2",
                "- what_if: 0-2",
                "- answer_usefulness: 0-2",
                "- hard flags: overclaim_hidden_config / pokemon_contamination / literal_copying / no_final_answer",
                "- primitive failures: list failed D1/D2/D3 checklist ids and repair targets",
                "- notes:",
                "",
            ]
        )
    return "\n".join(lines)


def _write_score_template(path: Path, items: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "blind_id",
                "case_id",
                "case_label",
                "d1_alignment",
                "d2_alignment",
                "d3_alignment",
                "what_if",
                "answer_usefulness",
                "overclaim_hidden_config",
                "pokemon_contamination",
                "literal_copying",
                "no_final_answer",
                "failed_checks_count",
                "failed_checks_json",
                "reviewer_notes",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "blind_id": item["blind_id"],
                    "case_id": item["case_id"],
                    "case_label": item.get("case_label"),
                }
            )


def _write_failure_log_template(path: Path, items: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "blind_id",
                "case_id",
                "case_label",
                "layer",
                "primitive_id",
                "check",
                "if_fail",
                "failure_type",
                "repair_target",
                "suggested_fix",
                "confidence",
                "notes",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "blind_id": item["blind_id"],
                    "case_id": item["case_id"],
                    "case_label": item.get("case_label"),
                }
            )


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
