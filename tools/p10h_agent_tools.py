from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
D_PACK_DIR = ROOT / "artifacts" / "p10h_intuition_demo_pack"
D_SELECTION_MANIFEST = ROOT / "artifacts" / "p10h_prebattle_ablation" / "d_layer_selection_manifest.yaml"


# ═══════════════════════════════════════════════════════════════
# A-layer tools
# ═══════════════════════════════════════════════════════════════

async def get_species_profile(species_key: str) -> dict[str, Any]:
    """查询物种基础数据。返回类型、特性、种族值。"""
    from advisor.battle_dex import DEFAULT_RUNTIME_DB, BattleDexRepository

    repo = BattleDexRepository(DEFAULT_RUNTIME_DB)
    profile = repo.get_species_profile(species_key)
    if profile is None:
        return {"error": f"species not found: {species_key}"}
    return profile.model_dump(mode="json")


async def get_species_available_moves(species_key: str) -> dict[str, Any]:
    """查询物种完整技能池。返回所有可用技能（名称/类型/威力/效果/获取方式）。"""
    from advisor.battle_dex import DEFAULT_RUNTIME_DB, BattleDexRepository

    repo = BattleDexRepository(DEFAULT_RUNTIME_DB)
    profile = repo.get_species_profile(species_key)
    if profile is None:
        return {"error": f"species not found: {species_key}"}
    moves = repo.get_species_available_moves(species_key, limit=None)
    return {
        "species_id": species_key,
        "species_name": profile.display_name,
        "moves": [m.model_dump(mode="json") for m in moves],
    }


# ═══════════════════════════════════════════════════════════════
# B-layer tool
# ═══════════════════════════════════════════════════════════════

async def retrieve_doc_context(query: str) -> dict[str, Any]:
    """检索 wiki/机制文档中的相关知识片段。"""
    from advisor.retrieval import DocContextRetriever

    retriever = DocContextRetriever()
    results = retriever.retrieve(query=query, analysis_type="team", limit=5)
    if not results:
        return {"snippets": [], "note": "no relevant B-layer context found"}
    return {
        "snippets": [
            {
                "source_path": r.source_path,
                "topic": r.topic,
                "content": r.content,
            }
            for r in results
        ],
    }


# ═══════════════════════════════════════════════════════════════
# D-layer tool
# ═══════════════════════════════════════════════════════════════

async def retrieve_d_layer_demo(case_id: str, mode: str = "exact") -> dict[str, Any]:
    """检索 D 层专家示范。mode=exact 返回同源 demo，mode=transfer 返回异源 demo。
    Demo 是推理方法参考——不是当前任务的答案。不要逐字复制其中的首发、对位或结论。
    """
    manifest = _load_manifest()
    demos = _load_all_demos()
    if not manifest or not demos:
        return {"demos": [], "note": "D-layer data unavailable"}

    level = f"L3-{mode}"
    case_selection = manifest.get("selections", {}).get(case_id, {})
    level_selection = case_selection.get(level, {})
    demo_ids = level_selection.get("demo_ids", [])

    results = []
    for did in demo_ids:
        if did in demos:
            d = demos[did]
            results.append(
                {
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "situation": d.get("situation"),
                    "expert_frame": d.get("expert_frame"),
                    "reasoning_chain": d.get("reasoning_chain"),
                    "decision_boundary": d.get("decision_boundary"),
                    "what_to_imitate": d.get("what_to_imitate"),
                    "not_to_infer": d.get("not_to_infer"),
                }
            )

    return {
        "demos": results,
        "mode": mode,
        "rationale": level_selection.get("rationale", ""),
    }


def _load_manifest() -> dict[str, Any] | None:
    if not D_SELECTION_MANIFEST.exists():
        return None
    data = yaml.safe_load(D_SELECTION_MANIFEST.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else None


def _load_all_demos() -> dict[str, dict[str, Any]]:
    path = D_PACK_DIR / "long_demonstrations.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = data.get("demos", []) if isinstance(data, dict) else []
    return {str(item.get("id", "")): item for item in items if isinstance(item, dict) and item.get("id")}
