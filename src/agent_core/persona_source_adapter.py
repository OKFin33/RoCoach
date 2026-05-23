from __future__ import annotations

from pathlib import Path

from agent_core.contracts import (
    PersonaSourceAdapterKind,
    PersonaSourceAdapterRequest,
    PersonaSourceArtifactBundle,
    PersonaSourceArtifactKind,
    PersonaSourceArtifactRef,
    PersonaSourceProvenance,
    PersonaSourceRunMode,
)


DEFAULT_SOURCE_ADAPTER_OUTPUT_ROOT = Path("artifacts") / "persona_source_adapter_runs"
DOCTRINE_CONTRACT_TARGET = "specs/persona_doctrine_contract.yaml"
PERSONA_SOURCE_STAGE_LABEL = "P1d Persona Source Adapter"
NUWA_DISTILLATION_ADAPTER_ID = "nuwa_distillation_adapter"
ENZO_FIXTURE_SOURCES = {
    "memo": Path("docs/personas/enzo_internal_distillation_memo.md"),
    "doctrine": Path("docs/personas/enzo_internal_persona_doctrine.yaml"),
    "mapping": Path("docs/personas/enzo_internal_mapping_note.md"),
}
MAPPING_NOTE_REQUIRED_SECTIONS = (
    "## Synthesis-Facing Fields",
    "## Rendering-Facing Fields",
    "## Metadata-Only Fields And Notes",
    "## Integration Review Verdict",
)
CRAWLER_TRACK_MARKERS = ("crawler", "battle wiki", "dry-run")


class PersonaSourceAdapterError(ValueError):
    pass


class NuwaDistillationAdapter:
    adapter_id = NUWA_DISTILLATION_ADAPTER_ID
    adapter_kind = PersonaSourceAdapterKind.DISTILL_FROM_EXISTING_SUBJECT

    def generate_bundle(
        self,
        request: PersonaSourceAdapterRequest,
        *,
        output_root: Path | None = None,
    ) -> PersonaSourceArtifactBundle:
        _validate_stage_label(request.stage_label)
        if request.target_subject.strip().casefold() != "enzo":
            raise PersonaSourceAdapterError(
                "nuwa_distillation_adapter only supports the bounded internal 'enzo' subject in P1d."
            )
        source_materials = _load_enzo_source_materials()
        source_summary = _build_source_summary(request)
        provenance = PersonaSourceProvenance(
            adapter_id=self.adapter_id,
            adapter_kind=self.adapter_kind,
            run_mode=request.run_mode,
            source_summary=source_summary,
            target_subject=request.target_subject.strip(),
            public_source_scope=list(request.public_source_scope),
            stage_label=request.stage_label,
            source_material_refs=[str(path) for path in ENZO_FIXTURE_SOURCES.values()],
        )
        resolved_root = (output_root or DEFAULT_SOURCE_ADAPTER_OUTPUT_ROOT) / self.adapter_id / _bundle_slug(
            request.target_subject,
            request.run_mode,
        )
        resolved_root.mkdir(parents=True, exist_ok=True)
        memo_path = resolved_root / "distillation_or_design_memo.md"
        doctrine_path = resolved_root / "normalized_persona_doctrine_draft.yaml"
        mapping_path = resolved_root / "mapping_or_usage_note.md"
        provenance_path = resolved_root / "provenance_metadata.yaml"

        memo_path.write_text(source_materials["memo"], encoding="utf-8")
        doctrine_path.write_text(source_materials["doctrine"], encoding="utf-8")
        mapping_path.write_text(source_materials["mapping"], encoding="utf-8")
        provenance_path.write_text(_render_provenance_yaml(provenance), encoding="utf-8")

        bundle = PersonaSourceArtifactBundle(
            adapter_id=self.adapter_id,
            adapter_kind=self.adapter_kind,
            run_mode=request.run_mode,
            output_root=resolved_root,
            memo=PersonaSourceArtifactRef(
                artifact_kind=PersonaSourceArtifactKind.DISTILLATION_OR_DESIGN_MEMO,
                path=memo_path,
            ),
            doctrine_draft=PersonaSourceArtifactRef(
                artifact_kind=PersonaSourceArtifactKind.NORMALIZED_PERSONA_DOCTRINE_DRAFT,
                path=doctrine_path,
                contract_target=DOCTRINE_CONTRACT_TARGET,
            ),
            mapping_note=PersonaSourceArtifactRef(
                artifact_kind=PersonaSourceArtifactKind.MAPPING_OR_USAGE_NOTE,
                path=mapping_path,
            ),
            provenance_metadata=PersonaSourceArtifactRef(
                artifact_kind=PersonaSourceArtifactKind.PROVENANCE_METADATA,
                path=provenance_path,
            ),
            provenance=provenance,
        )
        validate_persona_source_bundle(bundle)
        return bundle


def generate_internal_nuwa_distillation_bundle(
    *,
    target_subject: str = "enzo",
    public_source_scope: list[str] | None = None,
    output_root: Path | None = None,
    run_mode: PersonaSourceRunMode = PersonaSourceRunMode.INTERNAL_ONLY,
) -> PersonaSourceArtifactBundle:
    request = PersonaSourceAdapterRequest(
        target_subject=target_subject,
        public_source_scope=public_source_scope or ["reviewed_internal_distillation_artifacts"],
        run_mode=run_mode,
        stage_label=PERSONA_SOURCE_STAGE_LABEL,
    )
    return NuwaDistillationAdapter().generate_bundle(request, output_root=output_root)


def validate_persona_source_bundle(bundle: PersonaSourceArtifactBundle) -> None:
    if bundle.run_mode != PersonaSourceRunMode.INTERNAL_ONLY:
        raise PersonaSourceAdapterError("P1d bundle generation must remain internal_only by default.")
    if bundle.runtime_activation_requested or bundle.registry_write_requested:
        raise PersonaSourceAdapterError("P1d source adapter output must stay upstream of runtime and registry.")
    _require_non_empty_file(bundle.memo.path, "memo")
    _require_non_empty_file(bundle.doctrine_draft.path, "doctrine draft")
    _require_non_empty_file(bundle.mapping_note.path, "mapping note")
    _require_non_empty_file(bundle.provenance_metadata.path, "provenance metadata")
    if bundle.doctrine_draft.contract_target != DOCTRINE_CONTRACT_TARGET:
        raise PersonaSourceAdapterError("Doctrine draft contract target must be specs/persona_doctrine_contract.yaml.")
    mapping_text = bundle.mapping_note.path.read_text(encoding="utf-8")
    for required_section in MAPPING_NOTE_REQUIRED_SECTIONS:
        if required_section not in mapping_text:
            raise PersonaSourceAdapterError(
                f"Mapping note is missing required section: {required_section}."
            )
    if not bundle.provenance.source_summary:
        raise PersonaSourceAdapterError("Provenance metadata must include a non-empty source_summary.")
    if bundle.provenance.adapter_id != NUWA_DISTILLATION_ADAPTER_ID:
        raise PersonaSourceAdapterError("Unexpected adapter_id for bounded P1d adapter path.")
    _validate_stage_label(bundle.provenance.stage_label)


def _load_enzo_source_materials() -> dict[str, str]:
    materials: dict[str, str] = {}
    for key, path in ENZO_FIXTURE_SOURCES.items():
        _require_non_empty_file(path, f"{key} source")
        materials[key] = path.read_text(encoding="utf-8")
    return materials


def _build_source_summary(request: PersonaSourceAdapterRequest) -> list[str]:
    summary = [
        "checked-in Enzo internal distillation memo",
        "checked-in Enzo internal persona doctrine draft",
        "checked-in Enzo internal mapping note",
        f"public_source_scope={','.join(request.public_source_scope)}",
    ]
    return summary


def _render_provenance_yaml(provenance: PersonaSourceProvenance) -> str:
    lines = [
        f"adapter_id: {provenance.adapter_id}",
        f"adapter_kind: {provenance.adapter_kind}",
        f"run_mode: {provenance.run_mode}",
        f"target_subject: {provenance.target_subject}",
        f"stage_label: {provenance.stage_label}",
        "public_source_scope:",
        *[f"  - {item}" for item in provenance.public_source_scope],
        "source_summary:",
        *[f"  - {item}" for item in provenance.source_summary],
        "source_material_refs:",
        *[f"  - {item}" for item in provenance.source_material_refs],
    ]
    return "\n".join(lines) + "\n"


def _require_non_empty_file(path: Path, label: str) -> None:
    if not path.exists():
        raise PersonaSourceAdapterError(f"Missing required {label}: {path}")
    if not path.read_text(encoding="utf-8").strip():
        raise PersonaSourceAdapterError(f"Required {label} is empty: {path}")


def _validate_stage_label(stage_label: str) -> None:
    normalized = stage_label.strip().casefold()
    if "persona source adapter" not in normalized:
        raise PersonaSourceAdapterError(
            "Adapter-facing entry points must use the full persona-side stage name to avoid P1d track confusion."
        )
    if any(marker in normalized for marker in CRAWLER_TRACK_MARKERS):
        raise PersonaSourceAdapterError(
            "Crawler-side P1d terminology is forbidden in persona source adapter entry points."
        )


def _bundle_slug(target_subject: str, run_mode: PersonaSourceRunMode) -> str:
    normalized_subject = "_".join(target_subject.strip().casefold().split())
    return f"{normalized_subject}_{run_mode}"


__all__ = [
    "DEFAULT_SOURCE_ADAPTER_OUTPUT_ROOT",
    "DOCTRINE_CONTRACT_TARGET",
    "NUWA_DISTILLATION_ADAPTER_ID",
    "PERSONA_SOURCE_STAGE_LABEL",
    "PersonaSourceAdapterError",
    "NuwaDistillationAdapter",
    "generate_internal_nuwa_distillation_bundle",
    "validate_persona_source_bundle",
]
