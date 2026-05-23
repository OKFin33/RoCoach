#!/usr/bin/env python3
"""Generate Bailian ASR hotwords from local Roco A/B-layer terms."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = REPO_ROOT / "data" / "runtime" / "battle_dex.sqlite"
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "transcript_refinement" / "bailian"
DEFAULT_MECHANICS_ROOT = REPO_ROOT / "wiki" / "pages" / "mechanics"
DEFAULT_MECHANISM_REGISTRY = REPO_ROOT / "docs" / "governance" / "meta" / "wiki" / "mechanism_registry_2026-04-21.md"
DEFAULT_NAME = "roco_asr_core_v3"
FINAL_STAGES = ("最终形态", "最终阶段")
SHORT_MOVE_ALLOWLIST = {
    "水刃",
    "示弱",
    "沙涌",
    "扬沙",
    "撕咬",
    "偷袭",
    "电弧",
}
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]+")
INLINE_CODE_RE = re.compile(r"`([^`\n]{2,32})`")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
TABLE_TOKEN_RE = re.compile(r"^\|\s*`?([^`|\s][^`|]*?)`?\s*\|")
GENERIC_SKIP_TERMS = {
    "使用",
    "技能",
    "精灵",
    "队伍",
    "体系",
    "机制",
    "回合",
    "资源",
    "效果",
    "状态",
    "普通",
    "属性",
    "当前",
    "未来",
    "独立",
    "默认",
}
HIGH_PRIORITY_MECHANISMS = (
    "愿力冲击",
    "愿力强化",
    "共鸣魔法",
    "血脉",
    "血脉技能",
    "聚能",
    "应对",
    "打断",
    "迸发",
    "蓄力",
    "入场",
    "离场",
    "换人",
    "替换上场",
    "主动离场",
    "蓄势印记",
    "光合印记",
    "星陨印记",
    "龙噬印记",
    "蓄电印记",
    "中毒印记",
    "降灵印记",
    "棘刺印记",
    "攻击印记",
    "湿润印记",
    "减速印记",
    "风起印记",
    "沙暴",
    "雨天",
    "雪天",
    "暴风雪",
    "润泽印记",
)
TACTICAL_TERMS = (
    "联防",
    "联防位",
    "轮换",
    "首发",
    "打手",
    "清线手",
    "强化手",
    "斩杀线",
    "主C",
    "副C",
    "C位",
    "配队",
    "阵容",
    "一图流",
    "意图流",
    "顶分",
    "登顶",
)
CURATED_MECHANISMS = set(HIGH_PRIORITY_MECHANISMS) | set(TACTICAL_TERMS)


@dataclass(frozen=True)
class HotwordSource:
    kind: str
    term: str
    weight: int


def _fetch_terms(conn: sqlite3.Connection, sql: str, params: Iterable[object] = ()) -> list[str]:
    terms = [str(row[0]).strip() for row in conn.execute(sql, tuple(params)).fetchall() if row[0]]
    return sorted({term for term in terms if term})


def load_hotwords(db_path: Path) -> tuple[list[str], list[str]]:
    with sqlite3.connect(db_path) as conn:
        species = _fetch_terms(
            conn,
            """
            SELECT DISTINCT display_name
            FROM species_form
            WHERE evolution_stage IN (?, ?)
            """,
            FINAL_STAGES,
        )
        placeholders = ",".join("?" for _ in SHORT_MOVE_ALLOWLIST)
        moves = _fetch_terms(
            conn,
            f"""
            SELECT DISTINCT move_name
            FROM move
            WHERE length(move_name) >= 4
               OR move_name IN ({placeholders})
            """,
            sorted(SHORT_MOVE_ALLOWLIST),
        )
    return species, moves


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _looks_like_domain_term(term: str) -> bool:
    term = term.strip()
    if len(term) < 2 or len(term) > 12:
        return False
    if term in GENERIC_SKIP_TERMS:
        return False
    if term.startswith(("data/", "docs/", "wiki/", "specs/")) or term.endswith(".md"):
        return False
    if term not in CURATED_MECHANISMS and (re.search(r"[A-Za-z0-9]", term) or re.search(r"[/\\:：\s]", term)):
        return False
    return bool(CHINESE_RE.search(term))


def _extract_mark_terms(text: str) -> list[str]:
    terms: list[str] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip(" `") for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] in {"Mark", "Token / Mechanism", "---"}:
            continue
        term = cells[0].strip()
        if _looks_like_domain_term(term):
            terms.append(term)
    return terms


def load_mechanism_terms(mechanics_root: Path, registry_path: Path, *, max_terms: int) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    def add(term: str) -> None:
        term = term.strip()
        if not _looks_like_domain_term(term) or term in seen:
            return
        seen.add(term)
        ordered.append(term)

    for term in HIGH_PRIORITY_MECHANISMS:
        add(term)
    for term in TACTICAL_TERMS:
        add(term)

    if registry_path.exists():
        text = _read_text(registry_path)
        for match in TABLE_TOKEN_RE.finditer(text):
            add(match.group(1))

    if mechanics_root.exists():
        for path in sorted(mechanics_root.glob("*.md")):
            text = _read_text(path)
            for term in _extract_mark_terms(text):
                add(term)
            for match in INLINE_CODE_RE.finditer(text):
                add(match.group(1))
            for match in HEADING_RE.finditer(text):
                heading = re.sub(r"[*_`#]", "", match.group(1)).strip()
                for chunk in CHINESE_RE.findall(heading):
                    add(chunk)

    return ordered[:max_terms]


def build_hotword_payload(
    species: list[str],
    moves: list[str],
    mechanisms: list[str],
    *,
    species_weight: int,
    move_weight: int,
    mechanism_weight: int,
    high_priority_weight: int,
) -> list[dict[str, object]]:
    by_term: dict[str, HotwordSource] = {}
    for term in species:
        by_term[term] = HotwordSource("species", term, species_weight)
    for term in moves:
        current = by_term.get(term)
        if not current or move_weight > current.weight:
            by_term[term] = HotwordSource("move", term, move_weight)
    high_priority = set(HIGH_PRIORITY_MECHANISMS)
    for term in mechanisms:
        weight = high_priority_weight if term in high_priority else mechanism_weight
        current = by_term.get(term)
        if not current or weight > current.weight:
            by_term[term] = HotwordSource("mechanism", term, weight)

    payload: list[dict[str, object]] = []
    for term in [*species, *moves, *mechanisms]:
        source = by_term.pop(term, None)
        if not source:
            continue
        payload.append({"text": source.term, "weight": source.weight, "lang": "zh"})
    for source in by_term.values():
        payload.append({"text": source.term, "weight": source.weight, "lang": "zh"})
    return payload


def write_summary(
    path: Path,
    *,
    name: str,
    species: list[str],
    moves: list[str],
    mechanisms: list[str],
    payload: list[dict[str, object]],
    species_weight: int,
    move_weight: int,
    mechanism_weight: int,
    high_priority_weight: int,
) -> None:
    lines = [
        f"# {name}",
        "",
        f"- generated_at: `{date.today().isoformat()}`",
        "- target_model: `fun-asr`",
        "- usage: Bailian ASR hotword vocabulary only; not runtime knowledge.",
        f"- final_species_display_names: {len(species)}",
        f"- selected_moves: {len(moves)}",
        f"- selected_mechanisms: {len(mechanisms)}",
        f"- total_hotwords: {len(payload)}",
        f"- weights: species={species_weight}, moves={move_weight}, mechanisms={mechanism_weight}, high_priority_mechanisms={high_priority_weight}",
        "- selection_rule: final-form display names where `evolution_stage in (最终形态, 最终阶段)` plus move names with length >= 4, a short high-value move allowlist, and capped B-layer mechanism/tactical terms.",
        "- short_move_allowlist: " + ", ".join(sorted(SHORT_MOVE_ALLOWLIST)),
        "- high_priority_mechanisms: " + ", ".join(HIGH_PRIORITY_MECHANISMS),
        "",
        "## Species Sample",
        "",
        ", ".join(species[:80]),
        "",
        "## Move Sample",
        "",
        ", ".join(moves[:120]),
        "",
        "## Mechanism Sample",
        "",
        ", ".join(mechanisms[:160]),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--mechanics-root", type=Path, default=DEFAULT_MECHANICS_ROOT)
    parser.add_argument("--mechanism-registry", type=Path, default=DEFAULT_MECHANISM_REGISTRY)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--species-weight", type=int, default=4)
    parser.add_argument("--move-weight", type=int, default=4)
    parser.add_argument("--mechanism-weight", type=int, default=3)
    parser.add_argument("--high-priority-mechanism-weight", type=int, default=5)
    parser.add_argument("--max-mechanisms", type=int, default=110)
    args = parser.parse_args()

    for field in ("species_weight", "move_weight", "mechanism_weight", "high_priority_mechanism_weight"):
        if getattr(args, field) < 1 or getattr(args, field) > 5:
            raise SystemExit(f"--{field.replace('_', '-')} must be in [1, 5]")

    species, moves = load_hotwords(args.db_path)
    mechanisms = load_mechanism_terms(args.mechanics_root, args.mechanism_registry, max_terms=args.max_mechanisms)
    payload = build_hotword_payload(
        species,
        moves,
        mechanisms,
        species_weight=args.species_weight,
        move_weight=args.move_weight,
        mechanism_weight=args.mechanism_weight,
        high_priority_weight=args.high_priority_mechanism_weight,
    )
    if len(payload) > 500:
        raise SystemExit(f"Hotword payload has {len(payload)} terms; Bailian limit is 500.")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    hotwords_path = args.out_dir / f"{args.name}.hotwords.json"
    terms_path = args.out_dir / f"{args.name}.terms.tsv"
    summary_path = args.out_dir / f"{args.name}.summary.md"

    hotwords_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    terms_path.write_text(
        "kind\tterm\n"
        + "\n".join(
            [
                *(f"species\t{term}" for term in species),
                *(f"move\t{term}" for term in moves),
                *(f"mechanism\t{term}" for term in mechanisms),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_summary(
        summary_path,
        name=args.name,
        species=species,
        moves=moves,
        mechanisms=mechanisms,
        payload=payload,
        species_weight=args.species_weight,
        move_weight=args.move_weight,
        mechanism_weight=args.mechanism_weight,
        high_priority_weight=args.high_priority_mechanism_weight,
    )

    print(
        json.dumps(
            {
                "hotwords_path": str(hotwords_path),
                "terms_path": str(terms_path),
                "summary_path": str(summary_path),
                "final_species_display_names": len(species),
                "selected_moves": len(moves),
                "selected_mechanisms": len(mechanisms),
                "total_hotwords": len(payload),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
