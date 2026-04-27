from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from advisor.battle_dex import DEFAULT_RUNTIME_DB
from agent_core.contracts import AgentResponse, PersonaEnvelope
from agent_core.persona import persona_request_from_selector
from agent_core.persona_profile_resolver import make_managed_persona_selector
from api.contracts import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    MetadataResponse,
    PersonaSelector,
    PersonaSelectorKind,
    SpeciesProfileResponse,
    SpeciesSearchResponse,
    TeamAnalyzeRequest,
)
from api.dependencies import get_advisor_service, rate_limit_placeholder
from api.logging_utils import get_api_logger, summarize_exception
from api.release import (
    API_VERSION,
    PROVIDER_KEY_MODE,
    RATE_LIMIT_MODE,
    RELEASE_STAGE,
    RESPONSE_SCHEMA_VERSION,
    SERVICE_NAME,
    SESSION_CONTINUITY_MODE,
    UNOFFICIAL_NOTICE,
)
from api.runtime_headers import (
    HEADER_MODEL,
    HEADER_PROVIDER_BASE_URL,
    HEADER_PROVIDER_KEY,
    HEADER_RUNTIME_MODE,
    request_runtime_config_from_headers,
)
from api.services.advisor_service import AdvisorService


ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV = "ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH"
_MANAGED_PERSONA_PATH_PLACEHOLDERS = {
    "",
    "unset",
    "disabled",
    "replace-with-materialized-profile-path",
    "/absolute/path/to/materialized_profiles.yaml",
}


def create_app(
    *,
    advisor_service: AdvisorService | None = None,
    db_path: Path | None = None,
    bootstrap: bool = True,
    default_backend: str = "deterministic",
    managed_persona_materialization_path: Path | None = None,
) -> FastAPI:
    resolved_materialization_path = (
        managed_persona_materialization_path
        if managed_persona_materialization_path is not None
        else managed_persona_materialization_path_from_env()
    )
    service = advisor_service or AdvisorService.from_db_path(
        db_path=db_path or DEFAULT_RUNTIME_DB,
        bootstrap=bootstrap,
        default_backend=default_backend,
        managed_persona_materialization_path=resolved_materialization_path,
    )
    app = FastAPI(title="Roco Advisor API", version=API_VERSION)
    app.state.advisor_service = service
    logger = get_api_logger()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost", "http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request, exc):  # type: ignore[no-untyped-def]
        if isinstance(exc, HTTPException):
            raise exc
        logger.error(
            "unhandled_exception method=%s path=%s exception_type=%s",
            request.method,
            request.url.path,
            summarize_exception(exc),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": {"code": "internal_error", "message": "Request failed safely."}},
        )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service_name=SERVICE_NAME,
            release_stage=RELEASE_STAGE,
            api_version=API_VERSION,
            response_schema_version=RESPONSE_SCHEMA_VERSION,
        )

    @app.get("/metadata", response_model=MetadataResponse)
    def metadata(
        service: AdvisorService = Depends(get_advisor_service),
    ) -> MetadataResponse:
        return MetadataResponse(
            service_name=SERVICE_NAME,
            release_stage=RELEASE_STAGE,
            api_version=API_VERSION,
            response_schema_version=RESPONSE_SCHEMA_VERSION,
            default_backend=service.default_backend,
            battle_dex_available=service.battle_dex_available,
            session_continuity=SESSION_CONTINUITY_MODE,
            provider_key_mode=PROVIDER_KEY_MODE,
            rate_limit_mode=RATE_LIMIT_MODE,
            unofficial_notice=UNOFFICIAL_NOTICE,
            features=[
                "chat",
                "team_analysis",
                "species_search",
                "species_profile",
                "persona_v1_built_in_registry",
                "managed_persona_public_selector_v1",
                "release_hardening_p0f",
            ],
        )

    @app.post(
        "/chat",
        response_model=ChatResponse,
        dependencies=[Depends(rate_limit_placeholder)],
    )
    def chat(
        request: ChatRequest,
        provider_key: str | None = Header(default=None, alias=HEADER_PROVIDER_KEY),
        provider_base_url: str | None = Header(default=None, alias=HEADER_PROVIDER_BASE_URL),
        model: str | None = Header(default=None, alias=HEADER_MODEL),
        runtime_mode: str | None = Header(default=None, alias=HEADER_RUNTIME_MODE),
        service: AdvisorService = Depends(get_advisor_service),
    ) -> ChatResponse:
        session_id, response = service.chat(
            message=request.message,
            session_id=request.session_id,
            persona=_persona_from_selector(request.persona_id, request.persona_selector),
            runtime_config=request_runtime_config_from_headers(
                provider_key=provider_key,
                provider_base_url=provider_base_url,
                model=model,
                runtime_mode=runtime_mode,
            ),
        )
        return ChatResponse(session_id=session_id, response=response)

    @app.post(
        "/team/analyze",
        response_model=AgentResponse,
        dependencies=[Depends(rate_limit_placeholder)],
    )
    def analyze_team(
        request: TeamAnalyzeRequest,
        service: AdvisorService = Depends(get_advisor_service),
    ) -> AgentResponse:
        slots = [
            (slot.primary_type.strip(), slot.secondary_type.strip() if slot.secondary_type else None)
            for slot in request.team
            if slot.primary_type.strip()
        ]
        if len(slots) != len(request.team):
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_team", "message": "Team slots require primary_type."},
            )
        return service.analyze_team(
            slots=slots,
            persona=_persona_from_selector(request.persona_id, request.persona_selector),
        )

    @app.get("/species/search", response_model=SpeciesSearchResponse)
    def species_search(
        q: str = Query(min_length=1),
        limit: int = Query(default=10, ge=1, le=20),
        service: AdvisorService = Depends(get_advisor_service),
    ) -> SpeciesSearchResponse:
        return SpeciesSearchResponse(
            query=q,
            results=service.search_species(query=q, limit=limit),
        )

    @app.get("/species/{species_id}", response_model=SpeciesProfileResponse)
    def species_profile(
        species_id: str,
        service: AdvisorService = Depends(get_advisor_service),
    ) -> SpeciesProfileResponse:
        return SpeciesProfileResponse(profile=service.get_species_profile(species_id=species_id))

    return app


def _persona_from_selector(
    persona_id: str | None,
    persona_selector: PersonaSelector | None = None,
) -> PersonaEnvelope | None:
    if persona_selector is None:
        return persona_request_from_selector(persona_id)
    if persona_selector.kind == PersonaSelectorKind.BUILT_IN:
        return persona_request_from_selector(persona_selector.persona_id)
    if persona_selector.version is None or persona_selector.revision is None:
        return persona_request_from_selector(f"{persona_selector.persona_id}@invalid")
    return persona_request_from_selector(
        make_managed_persona_selector(
            persona_selector.persona_id,
            persona_selector.version,
            persona_selector.revision,
        )
    )


def managed_persona_materialization_path_from_env(
    environ: dict[str, str] | None = None,
) -> Path | None:
    source = os.environ if environ is None else environ
    raw_value = source.get(ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH_ENV)
    if raw_value is None:
        return None
    value = raw_value.strip()
    if value.casefold() in _MANAGED_PERSONA_PATH_PLACEHOLDERS:
        return None
    return Path(value).expanduser()


app = create_app()
