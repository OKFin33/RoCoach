from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from advisor.runtime import AdvisorAgent
from agent_core.adapters.advisor import AdvisorRuntimeAdapter
from agent_core.contracts import (
    AgentResponse,
    AgentResponseStatus,
    AnalysisType,
    ConfidenceNote,
    EvidenceItem,
    PersonaEnvelope,
    SynthesisResult,
    SynthesisWarning,
    SynthesisWarningSeverity,
)
from agent_core.orchestrator import AgentOrchestrator
from agent_core.persona import (
    DEFAULT_PERSONA_DISPLAY_NAME,
    DEFAULT_PERSONA_ID,
    FACT_POLICY,
    FORBIDDEN_PUBLIC_PERSONA_MARKERS,
    PERSONA_RENDER_CONTRACT,
)
from agent_core.persona_registry import ALTERNATE_PERSONA_DISPLAY_NAME, ALTERNATE_PERSONA_ID
from agent_core.safety import SafetyDecision, SafetyGuard
from reporting.contracts import ConfidenceTier


ROOT = Path(__file__).resolve().parent.parent
PURE_MODULES = (
    "agent_core.contracts",
    "agent_core.tools",
    "agent_core.safety",
    "agent_core.persona",
    "agent_core.orchestrator",
)


class AgentCoreOrchestratorTests(unittest.TestCase):
    def test_pure_agent_core_modules_do_not_import_advisor(self) -> None:
        code = (
            "import importlib, sys\n"
            f"for name in {PURE_MODULES!r}:\n"
            "    importlib.import_module(name)\n"
            "loaded = sorted(name for name in sys.modules if name.startswith('advisor'))\n"
            "assert loaded == [], loaded\n"
        )
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )

        self.assertEqual(completed.stdout, "")

    def test_pure_agent_core_module_sources_have_no_advisor_imports(self) -> None:
        for relative_path in (
            "agent_core/contracts.py",
            "agent_core/tools.py",
            "agent_core/safety.py",
            "agent_core/persona.py",
            "agent_core/orchestrator.py",
        ):
            source = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertNotIn("advisor.", source, relative_path)
            self.assertNotIn("from advisor", source, relative_path)
            self.assertNotIn("import advisor", source, relative_path)

    def test_orchestrator_delegates_and_preserves_factual_fields(self) -> None:
        adapter = _FakeRuntimeAdapter(_sample_response())
        orchestrator = AgentOrchestrator(runtime_adapter=adapter)

        response = orchestrator.handle_message("分析这队联防")

        self.assertEqual(adapter.messages, ["分析这队联防"])
        self.assertEqual(response.answer, "grounded answer。我会先按当前队伍信息给出能落地的判断。")
        self.assertEqual(response.evidence[0].content, "engine evidence")
        self.assertEqual(response.confidence_notes[0].confidence, ConfidenceTier.CONFIRMED)
        self.assertEqual(response.status, AgentResponseStatus.OK)
        self.assertIsNotNone(response.synthesis)
        self.assertIsNotNone(response.presentation)
        assert response.synthesis is not None
        assert response.presentation is not None
        self.assertEqual(response.presentation.reply, response.answer)
        self.assertEqual(
            response.synthesis.synthesized_judgement,
            "硬结论：grounded answer。我会先按当前队伍信息给出能落地的判断。",
        )
        self.assertEqual(response.presentation.why, response.synthesis.why_summary)
        self.assertIsNone(response.presentation.presentation_metadata.persona_id)
        self.assertIsNotNone(response.persona)
        assert response.persona is not None
        self.assertEqual(response.persona.persona_id, DEFAULT_PERSONA_ID)
        self.assertEqual(response.persona.display_name, DEFAULT_PERSONA_DISPLAY_NAME)
        self.assertIn(response.answer, response.persona.rendered_answer or "")
        self.assertEqual(response.persona.render_contract, PERSONA_RENDER_CONTRACT)
        self.assertFalse(response.persona.sanitized)

    def test_synthesis_runs_before_persona_rendering(self) -> None:
        adapter = _FakeRuntimeAdapter(_sample_response())
        boundary = _SpyPersonaBoundary()

        with patch(
            "agent_core.orchestrator.run_synthesis",
            side_effect=_fake_synthesis_result,
        ) as mocked_synthesis:
            with patch(
                "agent_core.orchestrator.run_presentation",
                wraps=__import__("agent_core.presentation", fromlist=["run_presentation"]).run_presentation,
            ) as mocked_presentation:
                orchestrator = AgentOrchestrator(
                    runtime_adapter=adapter,
                    persona_boundary=boundary,
                )

                response = orchestrator.handle_message("分析这队联防")

        self.assertEqual(adapter.messages, ["分析这队联防"])
        self.assertEqual(mocked_synthesis.call_count, 1)
        self.assertEqual(mocked_presentation.call_count, 1)
        self.assertEqual(boundary.received_answers, ["grounded answer。我会先按当前队伍信息给出能落地的判断。"])
        self.assertEqual(response.answer, boundary.received_answers[0])
        self.assertIn(response.answer, response.persona.rendered_answer or "")

    def test_multiple_safe_personas_change_expression_not_grounding(self) -> None:
        adapter = _FakeRuntimeAdapter(_sample_response())
        orchestrator = AgentOrchestrator(runtime_adapter=adapter)

        default_response = orchestrator.handle_message("分析这队联防")
        alternate_response = orchestrator.handle_message(
            "分析这队联防",
            persona=PersonaEnvelope(persona_id=ALTERNATE_PERSONA_ID),
        )

        self.assertEqual(default_response.answer, alternate_response.answer)
        self.assertEqual(
            default_response.presentation.model_dump(mode="json"),
            alternate_response.presentation.model_dump(mode="json"),
        )
        self.assertEqual(
            [item.model_dump(mode="json") for item in default_response.evidence],
            [item.model_dump(mode="json") for item in alternate_response.evidence],
        )
        self.assertEqual(
            [note.model_dump(mode="json") for note in default_response.confidence_notes],
            [note.model_dump(mode="json") for note in alternate_response.confidence_notes],
        )
        self.assertEqual(default_response.status, alternate_response.status)
        self.assertIsNotNone(default_response.persona)
        self.assertIsNotNone(alternate_response.persona)
        assert default_response.persona is not None
        assert alternate_response.persona is not None
        self.assertEqual(default_response.persona.persona_id, DEFAULT_PERSONA_ID)
        self.assertEqual(alternate_response.persona.persona_id, ALTERNATE_PERSONA_ID)
        self.assertEqual(alternate_response.persona.display_name, ALTERNATE_PERSONA_DISPLAY_NAME)
        self.assertNotEqual(
            default_response.persona.rendered_answer,
            alternate_response.persona.rendered_answer,
        )
        self.assertIn(default_response.answer, default_response.persona.rendered_answer or "")
        self.assertIn(alternate_response.answer, alternate_response.persona.rendered_answer or "")

    def test_safety_refusal_does_not_call_runtime_adapter(self) -> None:
        adapter = _FakeRuntimeAdapter(_sample_response())
        orchestrator = AgentOrchestrator(
            runtime_adapter=adapter,
            safety_guard=_RefusingSafetyGuard(),
        )

        response = orchestrator.handle_message("blocked message")

        self.assertEqual(adapter.messages, [])
        self.assertEqual(response.status, AgentResponseStatus.REFUSED)
        self.assertEqual(response.backend, "agent_core_safety")
        self.assertEqual(response.analysis_type, AnalysisType.UNSUPPORTED)
        self.assertIn("安全边界拒绝", response.answer)
        self.assertFalse(response.evidence)
        self.assertFalse(response.confidence_notes)
        self.assertIsNotNone(response.synthesis)
        self.assertIsNotNone(response.presentation)

    def test_persona_metadata_locks_facts_without_altering_response(self) -> None:
        adapter = _FakeRuntimeAdapter(_sample_response())
        orchestrator = AgentOrchestrator(runtime_adapter=adapter)

        response = orchestrator.handle_message(
            "分析这队联防",
            persona=PersonaEnvelope(
                persona_id=DEFAULT_PERSONA_ID,
                display_name=DEFAULT_PERSONA_DISPLAY_NAME,
                display_style="compact",
                rendered_answer="style-only copy",
                facts_locked=False,
                fact_policy="unsafe_override_attempt",
            ),
        )

        self.assertEqual(response.answer, "grounded answer。我会先按当前队伍信息给出能落地的判断。")
        self.assertEqual(response.evidence[0].content, "engine evidence")
        self.assertEqual(response.confidence_notes[0].note, "confirmed by engine")
        self.assertEqual(response.status, AgentResponseStatus.OK)
        self.assertIsNotNone(response.persona)
        assert response.persona is not None
        self.assertTrue(response.persona.facts_locked)
        self.assertEqual(response.persona.fact_policy, FACT_POLICY)
        self.assertEqual(response.persona.persona_id, DEFAULT_PERSONA_ID)
        self.assertIn(response.answer, response.persona.rendered_answer or "")
        self.assertNotEqual(response.persona.rendered_answer, "style-only copy")
        self.assertFalse(response.persona.sanitized)

    def test_unsafe_official_ip_persona_request_is_sanitized(self) -> None:
        adapter = _FakeRuntimeAdapter(_sample_response())
        orchestrator = AgentOrchestrator(runtime_adapter=adapter)

        response = orchestrator.handle_message(
            "分析这队联防",
            persona=PersonaEnvelope(
                persona_id="official_enzo",
                display_name="恩佐",
                display_style="Tencent official authorization",
                rendered_answer="官方授权角色台词",
            ),
        )

        self.assertEqual(response.answer, "grounded answer。我会先按当前队伍信息给出能落地的判断。")
        self.assertEqual(response.status, AgentResponseStatus.OK)
        self.assertIsNotNone(response.persona)
        assert response.persona is not None
        self.assertEqual(response.persona.persona_id, DEFAULT_PERSONA_ID)
        self.assertEqual(response.persona.display_name, DEFAULT_PERSONA_DISPLAY_NAME)
        self.assertTrue(response.persona.sanitized)
        persona_payload = response.persona.model_dump_json()
        for marker in FORBIDDEN_PUBLIC_PERSONA_MARKERS:
            if marker.isascii():
                self.assertNotIn(marker, persona_payload.casefold())
            else:
                self.assertNotIn(marker, persona_payload)

    def test_persona_does_not_alter_refusal_decision_fields(self) -> None:
        adapter = _FakeRuntimeAdapter(_sample_response())
        orchestrator = AgentOrchestrator(
            runtime_adapter=adapter,
            safety_guard=_RefusingSafetyGuard(),
        )

        response = orchestrator.handle_message("blocked message")

        self.assertEqual(response.status, AgentResponseStatus.REFUSED)
        self.assertEqual(response.backend, "agent_core_safety")
        self.assertEqual(response.analysis_type, AnalysisType.UNSUPPORTED)
        self.assertEqual(response.answer, "安全边界拒绝该请求。")
        self.assertFalse(response.evidence)
        self.assertFalse(response.confidence_notes)
        self.assertEqual([option.label for option in response.followup_options], ["/help"])
        self.assertIsNotNone(response.synthesis)
        self.assertIsNotNone(response.presentation)
        self.assertIsNotNone(response.persona)
        assert response.persona is not None
        self.assertIn(response.answer, response.persona.rendered_answer or "")

    def test_advisor_runtime_adapter_wraps_existing_advisor_agent(self) -> None:
        adapter = AdvisorRuntimeAdapter(AdvisorAgent(repository=None))

        response = adapter.handle_message("/help")

        self.assertEqual(response.backend, "deterministic")
        self.assertEqual(response.status, AgentResponseStatus.OK)
        self.assertEqual(response.analysis_type, AnalysisType.SESSION_COMMAND)
        self.assertIn("可用命令", response.answer)


class _FakeRuntimeAdapter:
    def __init__(self, response: AgentResponse) -> None:
        self.response = response
        self.messages: list[str] = []

    def handle_message(self, message: str) -> AgentResponse:
        self.messages.append(message)
        return self.response


class _RefusingSafetyGuard(SafetyGuard):
    def evaluate(self, message: str) -> SafetyDecision:
        return SafetyDecision.refuse(
            reason="test_refusal",
            answer="安全边界拒绝该请求。",
            followup_options=("/help",),
        )


class _SpyPersonaBoundary:
    def __init__(self) -> None:
        self.received_answers: list[str] = []

    def attach_metadata(self, response: AgentResponse, persona: PersonaEnvelope | None = None) -> AgentResponse:
        self.received_answers.append(response.answer)
        from agent_core.persona import PersonaBoundary

        return PersonaBoundary().attach_metadata(response, persona)


def _fake_synthesis_result(_input) -> SynthesisResult:
    return SynthesisResult(
        synthesis_version="p1a_synthesis.v1",
        synthesized_judgement="硬结论：grounded answer。我会先按当前队伍信息给出能落地的判断。",
        why_summary="我先看了当前问题、已提供的队伍信息和可用资料，只保留能直接支撑判断的部分。",
        surfaced_warnings=[
            SynthesisWarning(
                code="provisional_only",
                severity=SynthesisWarningSeverity.MEDIUM,
                message="当前信息只够做初步判断。",
            )
        ],
        followup_directions=["继续问：补洞方向是什么"],
        grounding_refs=["ev_001"],
        doctrine_refs=["generic_battle_doctrine_pack"],
    )


def _sample_response() -> AgentResponse:
    return AgentResponse(
        status=AgentResponseStatus.OK,
        backend="fake_runtime",
        analysis_type=AnalysisType.TEAM_ANALYSIS,
        answer="grounded answer",
        tool_results=[],
        evidence=[
            EvidenceItem(
                id="ev_001",
                source_type="engine",
                source_label="battle_engine.team_structure",
                confidence=ConfidenceTier.CONFIRMED,
                content="engine evidence",
                retrieval_reason="test_fixture",
            )
        ],
        confidence_notes=[
            ConfidenceNote(
                claim_scope="team_structure",
                confidence=ConfidenceTier.CONFIRMED,
                note="confirmed by engine",
            )
        ],
        followup_options=[],
        persona=None,
    )


if __name__ == "__main__":
    unittest.main()
