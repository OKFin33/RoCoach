from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from tools.p10h_agent_tools import (
    get_species_available_moves,
    get_species_profile,
    retrieve_d_layer_demo,
    retrieve_doc_context,
)

LEVEL_TOOLS: dict[str, list[Any]] = {
    "L0": [],
    "L1": [get_species_profile, get_species_available_moves],
    "L2": [
        get_species_profile,
        get_species_available_moves,
        retrieve_doc_context,
    ],
    "L3-exact": [
        get_species_profile,
        get_species_available_moves,
        retrieve_doc_context,
        retrieve_d_layer_demo,
    ],
    "L3-transfer": [
        get_species_profile,
        get_species_available_moves,
        retrieve_doc_context,
        retrieve_d_layer_demo,
    ],
}


def create_agent(
    level: str,
    *,
    model_name: str = "deepseek-v4-pro",
    provider_base_url: str = "https://api.deepseek.com",
    provider_api_key: str | None = None,
    reasoning_effort: str = "high",
) -> Agent[None, str]:
    if level not in LEVEL_TOOLS:
        raise ValueError(f"unknown level: {level} (expected one of {list(LEVEL_TOOLS)})")

    tools = LEVEL_TOOLS[level]

    provider = OpenAIProvider(
        base_url=provider_base_url,
        api_key=provider_api_key or "placeholder",
    )
    model = OpenAIModel(
        model_name,
        provider=provider,
        settings=OpenAIModelSettings(
            extra_body={"thinking": {"type": "enabled"}},
            openai_reasoning_effort=reasoning_effort,
        ),
    )

    system_prompt = _build_system_prompt(level)

    return Agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        retries=1,
    )


def _build_system_prompt(level: str) -> str:
    constitution = _load_constitution()
    sections = []

    # Core constitution
    sections.append(constitution)

    # Level-specific override
    if level in ("L3-exact", "L3-transfer"):
        sections.append(
            "\n## 实验模式\n"
            "本对话是受控实验。你可以使用 D 层专家示范（retrieve_d_layer_demo）。\n"
            "D 层材料是推理方法参考——不要逐字复制其中的首发选择、对位结论或伤害判断。\n"
            "只能迁移分析方法：先识别队伍/资源引擎，再检查默认路线是否有例外，再做分支树，再声明不确定性。\n"
            "当前任务结论必须由当前队伍、工具返回的 A/B 层数据和任务输入决定。"
        )
    elif level == "L0":
        sections.append(
            "\n## 实验模式\n"
            "本对话是受控实验。当前无可用的数据查询工具。\n"
            "如果你需要确认某个事实（如技能名、种族值），但你无法查询——请标注'未知'，不要编造。"
        )

    return "\n\n".join(sections)


def _load_constitution() -> str:
    path = ROOT / "specs" / "roco_agent_constitution.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""
