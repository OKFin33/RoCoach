#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_core.contracts import (
    PersonaSourceArtifactBundle,
    PersonaSourceArtifactKind,
    PersonaSourceArtifactRef,
    PersonaSourceProvenance,
    PersonaRuntimeActivationScope,
)
from agent_core.persona_activation_projection import build_persona_activation_registry_projection
from agent_core.persona_artifact_ingestion import ingest_persona_source_bundle
from agent_core.persona_profile_materialization import materialize_persona_projection_profiles
from agent_core.persona_profile_resolver import make_managed_persona_selector
from agent_core.persona_registry_admission import build_persona_registry_candidate
from agent_core.persona_registry_store import write_persona_registry_record
from agent_core.persona_runtime_activation import build_persona_runtime_activation_report
from agent_core.persona_source_adapter import DOCTRINE_CONTRACT_TARGET, validate_persona_source_bundle


DEFAULT_MEMO_NAME = "distillation_or_design_memo.md"
DEFAULT_DOCTRINE_NAME = "normalized_persona_doctrine_draft.yaml"
DEFAULT_MAPPING_NAME = "mapping_or_usage_note.md"
DEFAULT_PROVENANCE_NAME = "provenance_metadata.yaml"


def main() -> int:
    args = _parse_args()
    result = materialize_persona_artifacts(
        source_root=args.source_root,
        output_root=args.output_root,
        memo_path=args.memo,
        doctrine_path=args.doctrine,
        mapping_path=args.mapping,
        provenance_path=args.provenance,
        scope=args.scope,
        approve_public_safe=args.approve_public_safe,
    )
    print(f"materialization_path={result['materialization_path']}")
    print(f"selector={result['selector'] or ''}")
    print(f"profile_count={result['profile_count']}")
    print(f"blocked_count={result['blocked_count']}")
    return 0


def materialize_persona_artifacts(
    *,
    source_root: Path,
    output_root: Path,
    memo_path: Path | None = None,
    doctrine_path: Path | None = None,
    mapping_path: Path | None = None,
    provenance_path: Path | None = None,
    scope: PersonaRuntimeActivationScope = PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
    approve_public_safe: bool = False,
) -> dict[str, Any]:
    resolved_source_root = source_root.expanduser().resolve()
    resolved_output_root = output_root.expanduser().resolve()
    bundle = _build_source_bundle(
        source_root=resolved_source_root,
        memo_path=_resolve_artifact_path(resolved_source_root, memo_path, DEFAULT_MEMO_NAME),
        doctrine_path=_resolve_artifact_path(resolved_source_root, doctrine_path, DEFAULT_DOCTRINE_NAME),
        mapping_path=_resolve_artifact_path(resolved_source_root, mapping_path, DEFAULT_MAPPING_NAME),
        provenance_path=_resolve_artifact_path(resolved_source_root, provenance_path, DEFAULT_PROVENANCE_NAME),
    )
    validate_persona_source_bundle(bundle)

    resolved_output_root.mkdir(parents=True, exist_ok=True)
    ledger_path = resolved_output_root / "registry_ledger.yaml"
    ingestion = ingest_persona_source_bundle(
        bundle,
        approve_public_safe=approve_public_safe,
        output_path=resolved_output_root / "ingestion_result.yaml",
    )
    candidate = build_persona_registry_candidate(
        ingestion,
        output_path=resolved_output_root / "registry_candidate.yaml",
    )
    record = write_persona_registry_record(ledger_path, candidate, ingestion)
    activation_report = build_persona_runtime_activation_report(
        ledger_path,
        requested_scope=scope,
        output_path=resolved_output_root / "activation_report.yaml",
    )
    projection = build_persona_activation_registry_projection(
        activation_report,
        output_path=resolved_output_root / "activation_projection.yaml",
    )
    materialization_path = resolved_output_root / "materialized_profiles.yaml"
    materialization = materialize_persona_projection_profiles(
        projection,
        output_path=materialization_path,
    )

    selector = None
    for profile in materialization.profiles:
        if (
            profile.persona_id == record.persona_id
            and profile.version == record.version
            and profile.revision == record.revision
        ):
            selector = make_managed_persona_selector(profile.persona_id, profile.version, profile.revision)
            break

    _write_runtime_env_snippet(resolved_output_root / "runtime_env_snippet.env", materialization_path, scope)
    if selector is not None:
        (resolved_output_root / "selector.txt").write_text(selector + "\n", encoding="utf-8")

    summary = {
        "source_root": str(resolved_source_root),
        "output_root": str(resolved_output_root),
        "materialization_path": str(materialization_path),
        "selector": selector,
        "persona_id": record.persona_id,
        "version": record.version,
        "revision": record.revision,
        "scope": str(scope),
        "profile_count": len(materialization.profiles),
        "blocked_count": len(materialization.blocked_decision_summaries),
        "approved_public_safe": approve_public_safe,
    }
    (resolved_output_root / "summary.yaml").write_text(
        yaml.safe_dump(summary, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return summary


def _build_source_bundle(
    *,
    source_root: Path,
    memo_path: Path,
    doctrine_path: Path,
    mapping_path: Path,
    provenance_path: Path,
) -> PersonaSourceArtifactBundle:
    provenance_payload = _load_yaml_mapping(provenance_path, "provenance_metadata")
    provenance = PersonaSourceProvenance.model_validate(provenance_payload)
    return PersonaSourceArtifactBundle(
        adapter_id=provenance.adapter_id,
        adapter_kind=provenance.adapter_kind,
        run_mode=provenance.run_mode,
        output_root=source_root,
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


def _resolve_artifact_path(source_root: Path, explicit_path: Path | None, default_name: str) -> Path:
    path = explicit_path if explicit_path is not None else source_root / default_name
    return path.expanduser().resolve()


def _load_yaml_mapping(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label} is missing: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a YAML mapping: {path}")
    return payload


def _write_runtime_env_snippet(
    path: Path,
    materialization_path: Path,
    scope: PersonaRuntimeActivationScope,
) -> None:
    path.write_text(
        "\n".join(
            [
                f"ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH={materialization_path}",
                f"ROCO_MANAGED_PERSONA_SCOPE={scope}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize reviewed persona distillation artifacts into a runtime-consumable profile artifact.",
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--memo", type=Path)
    parser.add_argument("--doctrine", type=Path)
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument(
        "--scope",
        type=PersonaRuntimeActivationScope,
        choices=list(PersonaRuntimeActivationScope),
        default=PersonaRuntimeActivationScope.INTERNAL_ONLY_RUNTIME,
    )
    parser.add_argument(
        "--approve-public-safe",
        action="store_true",
        help="Admit the reviewed artifact as public-safe when doctrine and IP checks also pass.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
