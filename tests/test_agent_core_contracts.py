from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from advisor.contracts import (
    AdvisorEvidenceItem,
    AdvisorResponse,
    AdvisorToolResult,
    SourceType,
    ToolStatus,
)
from agent_core.contracts import (
    AgentResponse,
    AgentResponseStatus,
    AnalysisType,
    AnalyticalSubstrate,
    DetailSection,
    DetailSectionContentKind,
    DetailSectionVisibility,
    PresentationMetadata,
    PresentationResult,
    SynthesisResult,
    SynthesisWarning,
    SynthesisWarningSeverity,
    PersonaEnvelope,
    VisibleWarning,
)
from agent_core.adapters.advisor import (
    agent_response_from_advisor,
    analytical_substrate_from_advisor,
)
from reporting.contracts import ConfidenceTier


ROOT = Path(__file__).resolve().parent.parent


class AgentCoreContractTests(unittest.TestCase):
    def test_contract_module_import_does_not_load_advisor_contracts(self) -> None:
        code = (
            "import sys\n"
            "import agent_core.contracts\n"
            "assert 'advisor.contracts' not in sys.modules, sys.modules.keys()\n"
        )
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(completed.stdout, "")

    def test_contract_source_has_no_advisor_import(self) -> None:
        source = (ROOT / "agent_core" / "contracts.py").read_text(encoding="utf-8")

        self.assertNotIn("advisor.contracts", source)
        self.assertNotIn("from advisor", source)
        self.assertNotIn("import advisor", source)

    def test_advisor_adapter_lives_under_adapter_module(self) -> None:
        self.assertEqual(agent_response_from_advisor.__module__, "agent_core.adapters.advisor")

    def test_tool_status_enum_is_contract_bound(self) -> None:
        self.assertEqual(
            {status.value for status in AgentResponseStatus},
            {"ok", "degraded", "refused", "failed"},
        )

    def test_required_fields_and_evidence_refs_for_team_response(self) -> None:
        agent_response = agent_response_from_advisor(_team_advisor_response())
        payload = agent_response.model_dump(mode="json")

        self.assertEqual(
            set(payload),
            {
                "schema_version",
                "status",
                "backend",
                "analysis_type",
                "answer",
                "tool_results",
                "evidence",
                "confidence_notes",
                "followup_options",
                "synthesis",
                "presentation",
                "persona",
            },
        )
        self.assertEqual(payload["schema_version"], "agent_response.v1")
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["analysis_type"], "team_analysis")
        self.assertEqual(payload["answer"], "当前队伍结构分为 0.800。")
        self.assertIsNone(payload["synthesis"])
        self.assertIsNone(payload["presentation"])
        self.assertEqual(payload["evidence"][0]["id"], "ev_001")
        self.assertEqual(payload["evidence"][0]["source_type"], "engine")
        self.assertEqual(payload["evidence"][1]["source_type"], "doc")

        tool_by_name = {tool["tool_name"]: tool for tool in payload["tool_results"]}
        self.assertEqual(tool_by_name["analyze_team_structure"]["evidence_refs"], ["ev_001"])
        self.assertEqual(tool_by_name["retrieve_doc_context"]["evidence_refs"], ["ev_002"])
        self.assertTrue(all("evidence_refs" in tool for tool in payload["tool_results"]))

    def test_species_response_has_structured_confidence_notes(self) -> None:
        agent_response = agent_response_from_advisor(_species_advisor_response())
        payload = agent_response.model_dump(mode="json")

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["analysis_type"], "species_analysis")
        self.assertTrue(payload["confidence_notes"])
        self.assertTrue(all(isinstance(note, dict) for note in payload["confidence_notes"]))
        self.assertTrue(all("claim_scope" in note for note in payload["confidence_notes"]))
        self.assertTrue(all("confidence" in note for note in payload["confidence_notes"]))
        self.assertTrue(all("note" in note for note in payload["confidence_notes"]))
        self.assertEqual(payload["confidence_notes"][0]["confidence"], "confirmed")
        self.assertEqual(payload["confidence_notes"][1]["confidence"], "provisional")

        profile_tool = payload["tool_results"][0]
        self.assertEqual(profile_tool["tool_name"], "get_species_profile")
        self.assertEqual(profile_tool["evidence_refs"], ["ev_001"])

    def test_normalized_analytical_substrate_preserves_grounding(self) -> None:
        substrate = analytical_substrate_from_advisor(_team_advisor_response())

        self.assertIsInstance(substrate, AnalyticalSubstrate)
        self.assertEqual(substrate.answer_summary, "当前队伍结构分为 0.800。")
        self.assertEqual([item.id for item in substrate.evidence], ["ev_001", "ev_002"])
        self.assertEqual(substrate.followup_options[0].label, "继续问：补洞方向是什么")
        self.assertEqual(substrate.tool_results[0].evidence_refs, ["ev_001"])
        self.assertEqual(substrate.tool_results[1].evidence_refs, ["ev_002"])

    def test_refusal_response_is_structured_without_raw_confidence_strings(self) -> None:
        agent_response = agent_response_from_advisor(_future_meta_refusal_response())
        payload = agent_response.model_dump(mode="json")

        self.assertEqual(payload["status"], "refused")
        self.assertEqual(payload["analysis_type"], "unsupported")
        self.assertEqual(payload["tool_results"], [])
        self.assertEqual(payload["evidence"], [])
        self.assertEqual(payload["confidence_notes"], [])
        self.assertIn("没有 web/live 官方平衡公告 feed", payload["answer"])

    def test_auto_fallback_response_is_degraded(self) -> None:
        agent_response = agent_response_from_advisor(_fallback_advisor_response())
        payload = agent_response.model_dump(mode="json")

        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["backend"], "auto_fallback_deterministic")
        self.assertEqual(payload["analysis_type"], "team_analysis")
        self.assertEqual(payload["confidence_notes"][0]["claim_scope"], "runtime_backend")
        self.assertEqual(payload["confidence_notes"][0]["confidence"], "low_confidence")

    def test_json_serialization_is_stable_and_persona_cannot_override_facts(self) -> None:
        agent_response = agent_response_from_advisor(
            _team_advisor_response(),
            persona=PersonaEnvelope(
                persona_id="mobile_default",
                display_style="compact",
                rendered_answer="Persona-rendered copy.",
            ),
        )
        payload = json.loads(agent_response.model_dump_json())

        self.assertEqual(payload["answer"], "当前队伍结构分为 0.800。")
        self.assertEqual(payload["persona"]["rendered_answer"], "Persona-rendered copy.")
        self.assertTrue(payload["persona"]["facts_locked"])
        self.assertEqual(payload["persona"]["fact_policy"], "persona_may_not_alter_facts")
        self.assertTrue(payload["persona"]["public_safe"])
        self.assertFalse(payload["persona"]["sanitized"])
        self.assertIsNone(payload["persona"]["render_contract"])

    def test_optional_synthesis_payload_serializes(self) -> None:
        response = agent_response_from_advisor(_team_advisor_response()).model_copy(
            update={
                "synthesis": SynthesisResult(
                    synthesis_version="p1a_synthesis.v1",
                    synthesized_judgement="硬结论：当前队伍结构分为 0.800。",
                    why_summary="基于 grounded evidence 的压缩判断。",
                    surfaced_warnings=[
                        SynthesisWarning(
                            code="provisional_only",
                            severity=SynthesisWarningSeverity.MEDIUM,
                            message="Only provisional interpretation is available.",
                        )
                    ],
                    followup_directions=["继续问：补洞方向是什么"],
                    grounding_refs=["ev_001", "ev_002"],
                    doctrine_refs=["generic_battle_doctrine_pack"],
                )
            }
        )
        payload = response.model_dump(mode="json")

        self.assertEqual(payload["synthesis"]["synthesized_judgement"], "硬结论：当前队伍结构分为 0.800。")
        self.assertEqual(payload["synthesis"]["surfaced_warnings"][0]["severity"], "medium")
        self.assertEqual(payload["synthesis"]["grounding_refs"], ["ev_001", "ev_002"])
        self.assertEqual(payload["synthesis"]["doctrine_refs"], ["generic_battle_doctrine_pack"])

    def test_optional_presentation_payload_serializes(self) -> None:
        response = agent_response_from_advisor(_team_advisor_response()).model_copy(
            update={
                "presentation": PresentationResult(
                    presentation_version="p1b_presentation.v1",
                    reply="答复：当前队伍结构分为 0.800。",
                    why="边界提示：Only provisional interpretation is available. 基于 grounded evidence 的压缩判断。",
                    visible_warnings=[
                        VisibleWarning(
                            code="provisional_only",
                            severity=SynthesisWarningSeverity.MEDIUM,
                            message="Only provisional interpretation is available.",
                        )
                    ],
                    detail_sections=[
                        DetailSection(
                            section_id="analytical_base",
                            label="分析基底",
                            default_visibility=DetailSectionVisibility.EXPANDED,
                            content_kind=DetailSectionContentKind.ANALYTICAL_BASE,
                            content="当前队伍结构分为 0.800。",
                        )
                    ],
                    followup_prompts=["继续问：补洞方向是什么"],
                    presentation_metadata=PresentationMetadata(
                        persona_id=None,
                        facts_locked=True,
                        fact_policy="persona_may_not_alter_facts",
                        source_contract="specs/presentation_response_contract.yaml",
                    ),
                )
            }
        )
        payload = response.model_dump(mode="json")

        self.assertEqual(payload["presentation"]["reply"], "答复：当前队伍结构分为 0.800。")
        self.assertEqual(payload["presentation"]["visible_warnings"][0]["severity"], "medium")
        self.assertEqual(payload["presentation"]["detail_sections"][0]["content_kind"], "analytical_base")
        self.assertEqual(
            payload["presentation"]["presentation_metadata"]["source_contract"],
            "specs/presentation_response_contract.yaml",
        )


def _team_advisor_response() -> AdvisorResponse:
    return AdvisorResponse(
        backend="deterministic",
        answer_summary="当前队伍结构分为 0.800。",
        tool_results=[
            AdvisorToolResult(
                tool_name="analyze_team_structure",
                status=ToolStatus.OK,
                summary="structural_score=0.800",
                payload={"structural_score": 0.8},
            ),
            AdvisorToolResult(
                tool_name="retrieve_doc_context",
                status=ToolStatus.OK,
                summary="retrieved 1 approved doc snippets",
                payload={"topics": ["mvp_scope"]},
            ),
        ],
        evidence_summary=[
            AdvisorEvidenceItem(
                source_type=SourceType.ENGINE,
                source_label="battle_engine.team_structure",
                confidence=ConfidenceTier.CONFIRMED,
                content="engine fact",
                retrieval_reason="deterministic_structure_output",
            ),
            AdvisorEvidenceItem(
                source_type=SourceType.DOC,
                source_label="docs/agent_framework_decision.md",
                confidence=ConfidenceTier.PROVISIONAL,
                content="doc fact",
                retrieval_reason="bounded_doc_retrieval",
            ),
        ],
        confidence_notes=[
            "结构结论属于 confirmed，因为它们直接来自 deterministic Engine 输出。",
        ],
        followup_options=["继续问：补洞方向是什么"],
    )


def _species_advisor_response() -> AdvisorResponse:
    return AdvisorResponse(
        backend="deterministic",
        answer_summary="豆丁鱼 的已入库事实是 水/-。",
        tool_results=[
            AdvisorToolResult(
                tool_name="get_species_profile",
                status=ToolStatus.OK,
                summary="loaded 豆丁鱼",
                payload={"display_name": "豆丁鱼"},
            ),
            AdvisorToolResult(
                tool_name="analyze_species_semantics",
                status=ToolStatus.OK,
                summary="provisional_tags=utility_access",
                payload={"semantic_roles": ["utility_access"]},
            ),
        ],
        evidence_summary=[
            AdvisorEvidenceItem(
                source_type=SourceType.FACT,
                source_label="species_form:species_test",
                confidence=ConfidenceTier.CONFIRMED,
                content="豆丁鱼: type=水/-",
                retrieval_reason="sql_species_profile",
            )
        ],
        confidence_notes=[
            "物种资料与技能池事实属于 confirmed，因为它们直接来自 SQLite battle-dex。",
            "定位判断仅是 provisional hypothesis。",
        ],
        followup_options=["继续问：豆丁鱼 常见可用技能有哪些"],
    )


def _future_meta_refusal_response() -> AdvisorResponse:
    return AdvisorResponse(
        backend="deterministic",
        answer_summary=(
            "当前 MVP 没有 web/live 官方平衡公告 feed，也没有实时环境数据；"
            "因此不能预测未来加强/削弱、明天官方改动，或 live meta 变化。"
        ),
        tool_results=[],
        evidence_summary=[],
        confidence_notes=[],
        followup_options=["/species 豆丁鱼"],
    )


def _fallback_advisor_response() -> AdvisorResponse:
    response = _team_advisor_response()
    response.backend = "auto_fallback_deterministic"
    response.confidence_notes.insert(
        0,
        "auto backend 已跳过 native runtime：当前 CLI 进程内 native 已标记为不可用；reason=timeout.",
    )
    return response


if __name__ == "__main__":
    unittest.main()
