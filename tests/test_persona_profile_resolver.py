from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from agent_core.contracts import (
    AgentResponse,
    AgentResponseStatus,
    AnalysisType,
    DetailSection,
    DetailSectionContentKind,
    DetailSectionVisibility,
    PersonaEnvelope,
    PersonaProfileResolutionSource,
    PersonaProfileResolutionStatus,
    PersonaRuntimeActivationScope,
    PresentationMetadata,
    PresentationResult,
    SynthesisWarningSeverity,
    VisibleWarning,
)
from agent_core.persona import (
    DEFAULT_PERSONA_DISPLAY_NAME,
    DEFAULT_PERSONA_ID,
    FACT_POLICY,
    PERSONA_LLM_CONTEXT_CONTRACT,
    PersonaBoundary,
    build_persona_llm_context,
)
from agent_core.persona_activation_projection import build_persona_activation_registry_projection
from agent_core.persona_artifact_ingestion import ingest_persona_source_bundle
from agent_core.persona_profile_config import (
    PersonaProfileConfigError,
    build_persona_profile_resolver_from_materialization_path,
    load_persona_projection_profile_materialization,
)
from agent_core.persona_profile_materialization import materialize_persona_projection_profiles
from agent_core.persona_profile_materialization import write_persona_projection_profile_materialization
from agent_core.persona_profile_resolver import (
    PersonaProfileResolver,
    make_managed_persona_selector,
)
from agent_core.persona_registry import ALTERNATE_PERSONA_ID
from agent_core.persona_registry_admission import build_persona_registry_candidate
from agent_core.persona_registry_store import write_persona_registry_record
from agent_core.persona_runtime_activation import build_persona_runtime_activation_report
from agent_core.persona_source_adapter import generate_internal_nuwa_distillation_bundle


class PersonaProfileResolverTests(unittest.TestCase):
    def test_public_safe_materialized_selector_resolves_exact_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization = _build_public_safe_materialization(Path(tmpdir))
            profile = materialization.profiles[0]
            selector = make_managed_persona_selector(profile.persona_id, profile.version, profile.revision)
            resolver = PersonaProfileResolver(materialization)

            result = resolver.resolve(selector)

            self.assertEqual(result.status, PersonaProfileResolutionStatus.RESOLVED)
            self.assertEqual(result.source, PersonaProfileResolutionSource.MATERIALIZED_PROFILE)
            self.assertFalse(result.sanitized)
            self.assertIsNone(result.sanitized_reason)
            self.assertEqual(result.requested_persona_id, profile.persona_id)
            self.assertEqual(result.requested_version, profile.version)
            self.assertEqual(result.requested_revision, profile.revision)
            self.assertEqual(result.profile.persona_id, profile.persona_id)
            self.assertEqual(result.profile.display_name, "Public Safe Runtime Persona")
            self.assertTrue(result.profile.ip_safety_profile.public_safe)
            self.assertEqual(result.profile.fact_policy, FACT_POLICY)

    def test_materialized_selector_requires_exact_version_revision_no_fuzzy_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization = _build_public_safe_materialization(Path(tmpdir))
            profile = materialization.profiles[0]
            resolver = PersonaProfileResolver(materialization)

            bare_result = resolver.resolve(profile.persona_id)
            wrong_version = resolver.resolve(make_managed_persona_selector(profile.persona_id, "draft.v2", profile.revision))
            malformed = resolver.resolve(f"{profile.persona_id}@{profile.version}")

            self.assertEqual(bare_result.resolved_persona_id, DEFAULT_PERSONA_ID)
            self.assertTrue(bare_result.sanitized)
            self.assertEqual(
                bare_result.sanitized_reason,
                "materialized_profile_requires_exact_persona_id_version_revision",
            )
            self.assertEqual(wrong_version.resolved_persona_id, DEFAULT_PERSONA_ID)
            self.assertEqual(wrong_version.sanitized_reason, "materialized_profile_not_found")
            self.assertEqual(malformed.sanitized_reason, "invalid_managed_selector")

    def test_scope_incompatible_or_unsafe_materialized_profiles_fall_back_safely(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            internal_materialization = _build_internal_materialization(Path(tmpdir))
            profile = internal_materialization.profiles[0]
            selector = make_managed_persona_selector(profile.persona_id, profile.version, profile.revision)
            public_resolver = PersonaProfileResolver(
                internal_materialization,
                allowed_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
            )
            internal_resolver = PersonaProfileResolver(
                internal_materialization,
                allowed_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
            )

            public_result = public_resolver.resolve(selector)
            internal_result = internal_resolver.resolve(selector)

            self.assertEqual(public_result.resolved_persona_id, DEFAULT_PERSONA_ID)
            self.assertTrue(public_result.sanitized)
            self.assertEqual(public_result.sanitized_reason, "materialized_profile_scope_incompatible")
            self.assertEqual(internal_result.source, PersonaProfileResolutionSource.MATERIALIZED_PROFILE)
            self.assertEqual(internal_result.resolved_persona_id, profile.persona_id)
            self.assertFalse(internal_result.profile.ip_safety_profile.public_safe)

    def test_unsupported_and_unsafe_selectors_use_public_safe_default_with_audit_reason(self) -> None:
        resolver = PersonaProfileResolver()

        unknown = resolver.resolve("missing_persona")
        unsafe = resolver.resolve("official_enzo")

        self.assertEqual(unknown.resolved_persona_id, DEFAULT_PERSONA_ID)
        self.assertEqual(unknown.source, PersonaProfileResolutionSource.PUBLIC_SAFE_FALLBACK)
        self.assertTrue(unknown.sanitized)
        self.assertEqual(unknown.sanitized_reason, "built_in_selector_sanitized")
        self.assertEqual(unsafe.resolved_persona_id, DEFAULT_PERSONA_ID)
        self.assertTrue(unsafe.sanitized)
        self.assertTrue(unsafe.profile.ip_safety_profile.public_safe)

    def test_existing_builtin_selector_still_resolves_without_sanitization(self) -> None:
        resolver = PersonaProfileResolver()

        result = resolver.resolve(ALTERNATE_PERSONA_ID)

        self.assertEqual(result.source, PersonaProfileResolutionSource.BUILT_IN)
        self.assertFalse(result.sanitized)
        self.assertEqual(result.profile.persona_id, ALTERNATE_PERSONA_ID)

    def test_persona_boundary_renders_materialized_envelope_without_changing_canonical_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization = _build_public_safe_materialization(Path(tmpdir))
            profile = materialization.profiles[0]
            selector = make_managed_persona_selector(profile.persona_id, profile.version, profile.revision)
            boundary = PersonaBoundary(persona_resolver=PersonaProfileResolver(materialization))
            response = _sample_response()

            rendered = boundary.attach_metadata(response, PersonaEnvelope(persona_id=selector))

            self.assertEqual(rendered.answer, response.answer)
            self.assertIsNotNone(rendered.presentation)
            assert rendered.presentation is not None
            assert response.presentation is not None
            self.assertEqual(rendered.presentation.reply, response.presentation.reply)
            self.assertEqual(
                rendered.presentation.model_dump(mode="json"),
                response.presentation.model_dump(mode="json"),
            )
            self.assertIsNotNone(rendered.persona)
            assert rendered.persona is not None
            self.assertEqual(rendered.persona.persona_id, profile.persona_id)
            self.assertEqual(rendered.persona.display_name, "Public Safe Runtime Persona")
            self.assertFalse(rendered.persona.sanitized)
            self.assertIn(response.answer, rendered.persona.rendered_answer or "")
            self.assertNotEqual(rendered.persona.display_name, DEFAULT_PERSONA_DISPLAY_NAME)

    def test_rendering_flavor_rules_are_rendering_only_and_do_not_change_answer(self) -> None:
        response = _sample_response_with_grass_context()
        boundary = PersonaBoundary(persona_resolver=PersonaProfileResolver())

        rendered = boundary.attach_metadata(response, PersonaEnvelope(persona_id=DEFAULT_PERSONA_ID))

        self.assertEqual(rendered.answer, response.answer)
        self.assertIsNotNone(rendered.persona)
        assert rendered.persona is not None
        self.assertIn("grass_type_hostility", rendered.persona.rendering_flavor_rule_ids)
        self.assertIn("草系我不会替它说好话", rendered.persona.rendered_answer or "")

    def test_materialized_profiles_preserve_rendering_flavor_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization = _build_public_safe_materialization(Path(tmpdir))
            profile = materialization.profiles[0]
            selector = make_managed_persona_selector(profile.persona_id, profile.version, profile.revision)
            boundary = PersonaBoundary(persona_resolver=PersonaProfileResolver(materialization))
            response = _sample_response_with_grass_context()

            rendered = boundary.attach_metadata(response, PersonaEnvelope(persona_id=selector))

            self.assertEqual(rendered.answer, response.answer)
            self.assertIsNotNone(rendered.persona)
            assert rendered.persona is not None
            self.assertIn("grass_type_hostility", rendered.persona.rendering_flavor_rule_ids)
            self.assertIn("草系我不会替它说好话", rendered.persona.rendered_answer or "")

    def test_materialized_persona_builds_compressed_llm_context_without_raw_forbidden_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization = _build_public_safe_materialization(Path(tmpdir))
            profile = materialization.profiles[0]
            selector = make_managed_persona_selector(profile.persona_id, profile.version, profile.revision)

            context = build_persona_llm_context(
                PersonaEnvelope(persona_id=selector),
                persona_resolver=PersonaProfileResolver(materialization),
            )

            self.assertIsNotNone(context)
            assert context is not None
            self.assertIn(PERSONA_LLM_CONTEXT_CONTRACT, context)
            self.assertIn("Selected persona codename: Public Safe Runtime Persona", context)
            self.assertIn("Mental models:", context)
            self.assertIn("Decision heuristics:", context)
            self.assertIn("Hard rule: persona controls wording", context)
            self.assertNotIn("Enzo", context)
            self.assertNotIn("恩佐", context)
            self.assertNotIn("洛克王国世界", context)

    def test_persona_boundary_sanitizes_bad_managed_selector_without_changing_answer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization = _build_public_safe_materialization(Path(tmpdir))
            boundary = PersonaBoundary(persona_resolver=PersonaProfileResolver(materialization))
            response = _sample_response()

            rendered = boundary.attach_metadata(response, PersonaEnvelope(persona_id="public_safe_runtime_persona@draft.v2#1"))

            self.assertEqual(rendered.answer, response.answer)
            self.assertIsNotNone(rendered.persona)
            assert rendered.persona is not None
            self.assertEqual(rendered.persona.persona_id, DEFAULT_PERSONA_ID)
            self.assertEqual(rendered.persona.display_name, DEFAULT_PERSONA_DISPLAY_NAME)
            self.assertTrue(rendered.persona.sanitized)

    def test_resolver_module_does_not_consume_raw_doctrine_projection_or_ledger_internals(self) -> None:
        source = (Path(__file__).resolve().parent.parent / "agent_core" / "persona_profile_resolver.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("yaml", source)
        self.assertNotIn("doctrine_ref", source)
        self.assertNotIn("PersonaActivationRegistryProjection", source)
        self.assertNotIn("PersonaRegistryLedger", source)
        self.assertNotIn("load_persona_registry_ledger", source)

    def test_materialized_profile_loader_round_trips_yaml_and_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            materialization = _build_public_safe_materialization(Path(tmpdir))
            output_path = Path(tmpdir) / "materialized_profiles.yaml"
            write_persona_projection_profile_materialization(materialization, output_path)
            profile = materialization.profiles[0]
            selector = make_managed_persona_selector(profile.persona_id, profile.version, profile.revision)

            loaded = load_persona_projection_profile_materialization(output_path)
            resolver = build_persona_profile_resolver_from_materialization_path(output_path)
            result = resolver.resolve(selector)

            self.assertEqual(loaded, materialization)
            self.assertEqual(result.source, PersonaProfileResolutionSource.MATERIALIZED_PROFILE)
            self.assertEqual(result.profile.persona_id, profile.persona_id)

    def test_materialized_profile_loader_rejects_bad_or_missing_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing.yaml"
            invalid_path = Path(tmpdir) / "invalid.yaml"
            invalid_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

            with self.assertRaisesRegex(PersonaProfileConfigError, "missing"):
                load_persona_projection_profile_materialization(missing_path)
            with self.assertRaisesRegex(PersonaProfileConfigError, "mapping"):
                load_persona_projection_profile_materialization(invalid_path)

    def test_loader_module_consumes_only_materialized_profile_artifact_contract(self) -> None:
        source = (Path(__file__).resolve().parent.parent / "agent_core" / "persona_profile_config.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("PersonaProjectionProfileMaterialization", source)
        self.assertNotIn("PersonaActivationRegistryProjection", source)
        self.assertNotIn("PersonaRuntimeActivationReport", source)
        self.assertNotIn("PersonaRegistryLedger", source)
        self.assertNotIn("doctrine_ref", source)


def _build_public_safe_materialization(root: Path):
    ledger_path = root / "ledger.yaml"
    _write_public_safe_record(ledger_path, root / "source")
    activation_report = build_persona_runtime_activation_report(
        ledger_path,
        requested_scope=PersonaRuntimeActivationScope.PUBLIC_SAFE_RELEASE,
    )
    projection = build_persona_activation_registry_projection(activation_report)
    return materialize_persona_projection_profiles(projection)


def _build_internal_materialization(root: Path):
    ledger_path = root / "ledger.yaml"
    _write_internal_only_record(ledger_path, root / "source")
    activation_report = build_persona_runtime_activation_report(
        ledger_path,
        requested_scope=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
    )
    projection = build_persona_activation_registry_projection(activation_report)
    return materialize_persona_projection_profiles(projection)


def _write_internal_only_record(ledger_path: Path, output_root: Path):
    bundle = generate_internal_nuwa_distillation_bundle(output_root=output_root)
    ingestion_result = ingest_persona_source_bundle(bundle)
    candidate = build_persona_registry_candidate(ingestion_result)
    return write_persona_registry_record(ledger_path, candidate, ingestion_result)


def _write_public_safe_record(ledger_path: Path, output_root: Path):
    bundle = generate_internal_nuwa_distillation_bundle(output_root=output_root)
    doctrine = yaml.safe_load(bundle.doctrine_draft.path.read_text(encoding="utf-8"))
    doctrine["persona_id"] = "public_safe_runtime_persona"
    doctrine["display_name"] = "Public Safe Runtime Persona"
    doctrine["ip_safety_profile"] = {"public_safe": True, "forbidden_markers": []}
    doctrine["rendering_flavor_rules"] = [
        {
            "id": "grass_type_hostility",
            "trigger_terms": ["草系", "草属性", "草"],
            "allowed_effects": ["add_mild_disdain_in_wording"],
            "forbidden_effects": ["change_score", "change_recommendation"],
            "style_hint": "涉及草系时可以带轻微敌意，但必须明确不影响客观判断。",
        }
    ]
    bundle.doctrine_draft.path.write_text(yaml.safe_dump(doctrine, allow_unicode=True), encoding="utf-8")
    ingestion_result = ingest_persona_source_bundle(bundle, approve_public_safe=True)
    candidate = build_persona_registry_candidate(ingestion_result)
    return write_persona_registry_record(ledger_path, candidate, ingestion_result)


def _sample_response() -> AgentResponse:
    presentation = PresentationResult(
        presentation_version="p1b_presentation.v1",
        reply="答复：canonical field stays fixed.",
        why="Evidence and synthesis stay canonical.",
        visible_warnings=[
            VisibleWarning(
                code="test_warning",
                severity=SynthesisWarningSeverity.LOW,
                message="Keep this warning visible.",
            )
        ],
        detail_sections=[
            DetailSection(
                section_id="analytical_base",
                label="分析基底",
                default_visibility=DetailSectionVisibility.EXPANDED,
                content_kind=DetailSectionContentKind.ANALYTICAL_BASE,
                content="canonical field stays fixed.",
            )
        ],
        followup_prompts=["Keep followup."],
        presentation_metadata=PresentationMetadata(
            persona_id=None,
            facts_locked=True,
            fact_policy=FACT_POLICY,
            source_contract="specs/presentation_response_contract.yaml",
        ),
    )
    return AgentResponse(
        status=AgentResponseStatus.OK,
        backend="fake_runtime",
        analysis_type=AnalysisType.TEAM_ANALYSIS,
        answer=presentation.reply,
        tool_results=[],
        evidence=[],
        confidence_notes=[],
        followup_options=[],
        synthesis=None,
        presentation=presentation,
        persona=None,
    )


def _sample_response_with_grass_context() -> AgentResponse:
    response = _sample_response()
    presentation = response.presentation
    assert presentation is not None
    updated_presentation = presentation.model_copy(
        update={
            "reply": "草系精灵可以进队，但只能按它的抗性和技能价值判断。",
            "why": "草属性上下文触发的是语气规则，不是评分规则。",
        },
        deep=True,
    )
    return response.model_copy(
        update={
            "answer": updated_presentation.reply,
            "presentation": updated_presentation,
        },
        deep=True,
    )


if __name__ == "__main__":
    unittest.main()
