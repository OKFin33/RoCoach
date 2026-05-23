"""Shared transcript quality heuristics for Roco source ingestion."""

from __future__ import annotations

import re


NOISE_MARKERS = {
    "邓回哥": "unresolved_asr",
    "牵野手": "unresolved_asr",
    "无际斩杀线": "suspect_asr",
    "你也手打": "suspect_asr",
    "仿前玩家": "suspect_asr",
    "韩一球": "suspect_asr",
    "韩一蛇": "suspect_asr",
    "韩医蛇": "suspect_asr",
    "韩一生": "suspect_asr",
    "韩英雄": "suspect_asr",
    "水人一王": "suspect_asr",
    "水刃一王": "suspect_asr",
    "水人遗王": "suspect_asr",
    "贝伍斯": "suspect_asr",
    "被古斯": "suspect_asr",
}


def transcript_quality_flags(text: str, *, long_threshold: int = 230) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    flags: list[str] = []
    for marker, kind in NOISE_MARKERS.items():
        if marker in compact:
            flags.append(f"{kind}:{marker}")
    if len(compact) >= long_threshold:
        flags.append("long_excerpt")
    return flags


def transcript_quality_label(flags: list[str]) -> str:
    suspect_count = sum(1 for flag in flags if flag.startswith("suspect_asr"))
    if any(flag.startswith("unresolved_asr") for flag in flags) or suspect_count >= 2:
        return "needs_repair"
    if suspect_count == 1:
        return "usable_with_caution"
    if "long_excerpt" in flags:
        return "usable_long"
    return "good"
