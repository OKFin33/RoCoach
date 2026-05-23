#!/usr/bin/env python3
"""Build P14 mechanism-rule pilot artifacts from evidence foundation bundles.

This tool consumes unreviewed claim atoms and emits reviewable mechanism
clusters. It does not promote runtime graph data.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_ROOT = REPO_ROOT / "artifacts" / "knowledge_ops"
MECHANISM_ATOM_TYPES = {"mechanism_claim", "resource_claim"}
HIGH_IMPACT_MECHANISM_TYPES = {"mark", "weather", "status"}
MECHANISM_LIKE_TERMS = {"天气", "沙暴", "沙涌", "灼烧", "中毒", "恐惧", "睡眠", "麻痹", "冰冻"}


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


@dataclass(frozen=True)
class FoundationBundle:
    source_id: str
    foundation_dir: Path
    manifest: dict[str, Any]
    quality_gate: dict[str, Any]
    claim_atoms: list[dict[str, Any]]


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore")) or {}


def _write_yaml(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(payload, allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper),
        encoding="utf-8",
    )


def _relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _slug(value: str) -> str:
    normalized = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value.strip(), flags=re.UNICODE)
    return normalized.strip("_") or "unknown"


def load_foundation_bundle(foundation_dir: Path) -> FoundationBundle:
    manifest = _load_yaml(foundation_dir / "source_manifest_v2.yaml")
    quality_gate = _load_yaml(foundation_dir / "quality_gate.yaml")
    atom_payload = _load_yaml(foundation_dir / "claim_atoms.yaml")
    source_id = str(atom_payload.get("source_id") or quality_gate.get("source_id") or manifest.get("source_id") or "")
    if not source_id:
        raise ValueError(f"missing source_id in foundation bundle: {foundation_dir}")
    return FoundationBundle(
        source_id=source_id,
        foundation_dir=foundation_dir,
        manifest=manifest,
        quality_gate=quality_gate,
        claim_atoms=list(atom_payload.get("claim_atoms") or []),
    )


def is_mechanism_relevant_atom(atom: dict[str, Any]) -> bool:
    if atom.get("atom_type") in MECHANISM_ATOM_TYPES:
        return True
    mechanisms = [str(value) for value in atom.get("mentioned_mechanisms") or [] if value]
    return any("印记" in value or value in MECHANISM_LIKE_TERMS for value in mechanisms)


def _mechanism_topic(atom: dict[str, Any]) -> str:
    mechanisms = [str(value) for value in atom.get("mentioned_mechanisms") or [] if value]
    if mechanisms:
        return mechanisms[0]
    if atom.get("object") == "mark":
        return "未指明印记"
    subject = str(atom.get("subject") or "")
    if subject:
        return subject
    obj = atom.get("object")
    if isinstance(obj, str):
        return obj
    return str(atom.get("predicate") or "unknown")


def _mechanism_type(atom: dict[str, Any], topic: str) -> str:
    atom_type = str(atom.get("atom_type") or "")
    obj = atom.get("object")
    if atom_type == "resource_claim" or obj == "energy_window":
        return "resource_energy"
    if obj == "mark" or "印记" in topic:
        return "mark"
    if obj == "weather" or topic in {"天气", "沙暴", "沙涌"}:
        return "weather"
    if topic in {"灼烧", "中毒", "恐惧", "睡眠", "麻痹", "冰冻"}:
        return "status"
    return str(obj or atom.get("predicate") or "mechanism")


def _cluster_key(atom: dict[str, Any]) -> tuple[str, str]:
    topic = _mechanism_topic(atom)
    return (_mechanism_type(atom, topic), topic)


def _claim_view(atom: dict[str, Any]) -> dict[str, Any]:
    evidence = atom.get("evidence") or {}
    return {
        "claim_id": atom.get("claim_id"),
        "source_id": atom.get("source_id"),
        "segment_id": atom.get("segment_id"),
        "atom_type": atom.get("atom_type"),
        "subject": atom.get("subject"),
        "subject_resolution_status": atom.get("subject_resolution_status"),
        "predicate": atom.get("predicate"),
        "object": atom.get("object"),
        "mentioned_species": atom.get("mentioned_species") or [],
        "mentioned_moves": atom.get("mentioned_moves") or [],
        "mentioned_abilities": atom.get("mentioned_abilities") or [],
        "mentioned_mechanisms": atom.get("mentioned_mechanisms") or [],
        "quality_gate": atom.get("quality_gate"),
        "evidence": {
            "start_ms": evidence.get("start_ms"),
            "end_ms": evidence.get("end_ms"),
            "quote": evidence.get("quote"),
        },
        "review_status": atom.get("review_status", "unreviewed"),
        "runtime_allowed": False,
    }


def _risk_flags(claims: list[dict[str, Any]], source_count: int, mechanism_type: str, topic: str) -> list[str]:
    flags: set[str] = set()
    if source_count < 2:
        flags.add("single_source")
    if len(claims) < 2:
        flags.add("sparse_claims")
    if mechanism_type == "resource_energy":
        flags.add("battle_state_snapshot_not_rule")
    if mechanism_type == "mark" and topic == "未指明印记":
        flags.add("no_explicit_mechanism_anchor")
    for claim in claims:
        status = str(claim.get("subject_resolution_status") or "")
        quote = str((claim.get("evidence") or {}).get("quote") or "")
        if "ambiguous" in status or "missing" in status:
            flags.add("subject_resolution_uncertain")
        if claim.get("quality_gate") != "claim_ready":
            flags.add("quality_caution")
        if re.search(r"\d+|[一二三四五六七八九十百]+层", quote):
            flags.add("numeric_or_stack_claim")
        if not (claim.get("mentioned_species") or claim.get("mentioned_moves") or claim.get("mentioned_mechanisms")):
            flags.add("weak_a_b_anchor")
    return sorted(flags)


def _recommendation(mechanism_type: str, risk_flags: list[str], claim_count: int, source_count: int) -> str:
    if mechanism_type == "resource_energy":
        return "auto_defer"
    if "no_explicit_mechanism_anchor" in risk_flags:
        return "auto_defer"
    if "subject_resolution_uncertain" in risk_flags and claim_count <= 1:
        return "auto_defer"
    if mechanism_type == "status" and source_count < 2:
        return "auto_defer"
    if mechanism_type in HIGH_IMPACT_MECHANISM_TYPES and claim_count >= 2:
        return "decision_needed"
    if source_count >= 2 and not risk_flags:
        return "batch_approve_candidate"
    return "auto_defer"


def _normalized_candidate(topic: str, mechanism_type: str, claims: list[dict[str, Any]]) -> str:
    quotes = " ".join(str((claim.get("evidence") or {}).get("quote") or "") for claim in claims)
    if mechanism_type == "mark":
        fragments = [f"{topic} 是印记/叠层相关机制。"]
        if any(token in quotes for token in ("叠", "叠加")):
            fragments.append("来源片段提到叠加或叠层。")
        if "引爆" in quotes:
            fragments.append("来源片段提到引爆。")
        if any(token in quotes for token in ("吃掉", "献祭", "送掉")):
            fragments.append("来源片段提到承接、吃掉或献祭处理。")
        fragments.append("触发源、作用对象、层数公式和收益/伤害都必须经过 PM/source review 后才能写入 runtime rule。")
        return "".join(fragments)
    if mechanism_type == "weather":
        return f"{topic} 是天气相关机制候选。天气来源、持续、能耗/属性影响和适用对象需要 source review。"
    if mechanism_type == "status":
        return f"{topic} 是状态相关机制候选。当前只记录来源提及，不足以形成 runtime guardrail。"
    if mechanism_type == "resource_energy":
        return "来源片段提到某精灵当前能量/能耗窗口；这更像对局状态证据，不应直接归纳为机制规则。"
    return f"{topic} 是机制相关候选；当前证据不足以自动归纳为 guardrail。"


def build_mechanism_claim_payload(bundle: FoundationBundle, atoms: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "p14.mechanism_claims.v0",
        "source_id": bundle.source_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "source": {
            "title": ((bundle.manifest.get("source") or {}).get("title")),
            "url": ((bundle.manifest.get("source") or {}).get("url")),
            "source_type": ((bundle.manifest.get("source") or {}).get("source_type")),
        },
        "quality": {
            "segment_count": bundle.quality_gate.get("segment_count"),
            "claim_atom_count": bundle.quality_gate.get("claim_atom_count"),
            "quality_gate_counts": bundle.quality_gate.get("quality_gate_counts") or {},
            "repair_required_segments": bundle.quality_gate.get("repair_required_segments") or [],
        },
        "claims": atoms,
    }


def build_clusters(batch_id: str, bundles: list[FoundationBundle]) -> dict[str, Any]:
    by_source: dict[str, list[dict[str, Any]]] = {}
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    input_claim_count = 0

    for bundle in bundles:
        selected = [_claim_view(atom) for atom in bundle.claim_atoms if is_mechanism_relevant_atom(atom)]
        by_source[bundle.source_id] = selected
        input_claim_count += len(bundle.claim_atoms)
        for claim in selected:
            grouped[_cluster_key(claim)].append(claim)

    clusters: list[dict[str, Any]] = []
    for (mechanism_type, topic), claims in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        source_ids = sorted({str(claim.get("source_id")) for claim in claims if claim.get("source_id")})
        risk_flags = _risk_flags(claims, len(source_ids), mechanism_type, topic)
        recommendation = _recommendation(mechanism_type, risk_flags, len(claims), len(source_ids))
        clusters.append(
            {
                "cluster_id": f"mechanism_cluster/{_slug(mechanism_type)}/{_slug(topic)}",
                "m_level": "M2_candidate_rule",
                "mechanism_type": mechanism_type,
                "topic": topic,
                "normalized_rule_candidate": _normalized_candidate(topic, mechanism_type, claims),
                "source_count": len(source_ids),
                "claim_count": len(claims),
                "source_ids": source_ids,
                "review_recommendation": recommendation,
                "risk_flags": risk_flags,
                "source_claims": claims,
                "runtime_allowed": False,
            }
        )

    return {
        "schema_version": "p14.mechanism_rule_clusters.v0",
        "batch_id": batch_id,
        "generated_at": date.today().isoformat(),
        "runtime_allowed": False,
        "input_foundations": [_relpath(bundle.foundation_dir) for bundle in bundles],
        "summary": {
            "source_count": len(bundles),
            "input_claim_atom_count": input_claim_count,
            "mechanism_relevant_claim_count": sum(len(claims) for claims in by_source.values()),
            "cluster_count": len(clusters),
            "recommendation_counts": dict(Counter(cluster["review_recommendation"] for cluster in clusters)),
        },
        "clusters": clusters,
        "_claims_by_source": by_source,
    }


def _ms_to_stamp(ms: Any) -> str:
    if ms is None:
        return "?:??"
    total = int(ms) // 1000
    minutes, seconds = divmod(total, 60)
    return f"{minutes:02d}:{seconds:02d}"


def _cluster_line(cluster: dict[str, Any]) -> str:
    sample = (cluster.get("source_claims") or [{}])[0]
    evidence = sample.get("evidence") or {}
    stamp = _ms_to_stamp(evidence.get("start_ms"))
    return (
        f"- `{cluster['topic']}` / `{cluster['mechanism_type']}`: "
        f"{cluster['claim_count']} 条 claim，{cluster['source_count']} 个 source，"
        f"建议 `{cluster['review_recommendation']}`。例：{stamp} "
        f"“{evidence.get('quote', '')}”"
    )


def _compact_cluster_line(cluster: dict[str, Any]) -> str:
    sample = (cluster.get("source_claims") or [{}])[0]
    evidence = sample.get("evidence") or {}
    stamp = _ms_to_stamp(evidence.get("start_ms"))
    return (
        f"- {cluster['topic']}：{cluster['claim_count']} 段，{cluster['source_count']} 个来源。"
        f"例 {stamp}：“{evidence.get('quote', '')}”"
    )


def render_review_packet(batch_id: str, clusters_payload: dict[str, Any], bundles: list[FoundationBundle]) -> str:
    clusters = clusters_payload["clusters"]
    decision = [c for c in clusters if c["review_recommendation"] == "decision_needed"]
    defer = [c for c in clusters if c["review_recommendation"] == "auto_defer"]
    quality_lines = []
    for bundle in bundles:
        title = (bundle.manifest.get("source") or {}).get("title") or bundle.source_id
        counts = bundle.quality_gate.get("quality_gate_counts") or {}
        repair = bundle.quality_gate.get("repair_required_segments") or []
        quality_lines.append(
            f"- {title}：字幕段 {bundle.quality_gate.get('segment_count')}，"
            f"抽到 {bundle.quality_gate.get('claim_atom_count')} 条原始证据，"
            f"需要修音频/人工补听的段落 {len(repair)} 个。质量分布：{counts}"
        )
    mechanism_claim_count = clusters_payload["summary"]["mechanism_relevant_claim_count"]
    if mechanism_claim_count >= 30:
        next_step_line = "这个 batch 已经够做第一轮机制 pilot。下一步不要继续堆同源片段，而是补 2-3 条星陨/翼王/沙暴源，看看同一机制在不同视频里是否说法一致。"
    else:
        next_step_line = "下一步先补抽取器和来源，把机制相关证据拉到 30-50 条再让你看。"
    decision_topic = decision[0]["topic"] if decision else "无"
    decision_claims = decision[0]["claim_count"] if decision else 0
    decision_sources = decision[0]["source_count"] if decision else 0

    lines = [
        f"# Phase 1 Mechanism Pilot PM Brief: {batch_id}",
        "",
        "这份东西没有写入 runtime，也没有批准任何规则。它只是告诉你：我抓到的视频证据够不够继续往下做。",
        "",
        "## 你只要判断这一句",
        f"我建议把 `{decision_topic}` 当作第一批机制规则的主线继续补源。现在有 {decision_claims} 段相关证据，来自 {decision_sources} 个视频。",
        "",
        "你不需要确认它的完整机制。现在还不到那一步。",
        "",
        "你只需要判断：这个方向值得我继续抓更多来源吗？",
        "",
        "我的默认动作：继续。因为它已经明显影响星陨队、对位处理、印记层数、引爆和承接方式；但证据还不够写成 runtime rule。",
        "",
        "## 现在不能批准什么",
        "- 不批准任何机制规则进 runtime。",
        "- 不把“几层”“伤害多少”“谁没能量了”直接写成规则。",
        "- 不把 ASR 里含糊的“星云/星陨”当成事实；只接受窄口径修复和带来源片段的证据。",
        "",
        "## 我已经自动挡掉的东西",
    ]
    if defer:
        lines.extend(_compact_cluster_line(cluster) for cluster in defer)
    else:
        lines.append("- 无。")
    lines.extend(
        [
            "",
            "这些不用你看。它们要么只是当前对局状态，要么只有单源证据，要么机制名不明确。",
            "",
            "## 这次输入质量",
            f"- 视频来源：{len(bundles)} 条。",
            f"- 原始证据：{clusters_payload['summary']['input_claim_atom_count']} 条。",
            f"- 机制相关证据：{clusters_payload['summary']['mechanism_relevant_claim_count']} 条。",
            f"- 候选机制簇：{clusters_payload['summary']['cluster_count']} 个。",
            *quality_lines,
            "",
            "## 下一步",
            next_step_line,
            "",
            "下一轮我给你的 review 面应该只剩三类：稳定说法、来源冲突、必须你裁的机制边界。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_mechanism_pilot(
    *,
    foundation_dirs: list[Path],
    out_root: Path = DEFAULT_OUT_ROOT,
    batch_id: str | None = None,
) -> dict[str, Any]:
    if not foundation_dirs:
        raise ValueError("at least one foundation dir is required")
    resolved_batch_id = batch_id or f"phase1_mechanism_pilot_{date.today().isoformat()}"
    bundles = [load_foundation_bundle(path) for path in foundation_dirs]
    clusters_payload = build_clusters(resolved_batch_id, bundles)
    claims_by_source = clusters_payload.pop("_claims_by_source")

    mechanism_claim_paths: dict[str, str] = {}
    for bundle in bundles:
        payload = build_mechanism_claim_payload(bundle, claims_by_source[bundle.source_id])
        path = out_root / "mechanism_claims" / f"{bundle.source_id}.yaml"
        _write_yaml(path, payload)
        mechanism_claim_paths[bundle.source_id] = _relpath(path)

    cluster_path = out_root / "mechanism_rules" / "candidate_clusters" / f"{resolved_batch_id}.yaml"
    review_packet_path = out_root / "review_packets" / f"{resolved_batch_id}_review.md"
    _write_yaml(cluster_path, clusters_payload)
    review_packet_path.parent.mkdir(parents=True, exist_ok=True)
    review_packet_path.write_text(
        render_review_packet(resolved_batch_id, clusters_payload, bundles),
        encoding="utf-8",
    )

    return {
        "batch_id": resolved_batch_id,
        "runtime_allowed": False,
        "paths": {
            "mechanism_claims": mechanism_claim_paths,
            "candidate_clusters": _relpath(cluster_path),
            "review_packet": _relpath(review_packet_path),
        },
        "summary": clusters_payload["summary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--foundation-dir", action="append", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--batch-id")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = build_mechanism_pilot(
        foundation_dirs=args.foundation_dir,
        out_root=args.out_root,
        batch_id=args.batch_id,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"mechanism pilot: {result['batch_id']}")
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
