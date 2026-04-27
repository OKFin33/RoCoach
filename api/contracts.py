from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agent_core.contracts import AgentResponse
from api.release import API_VERSION


class HealthResponse(BaseModel):
    status: str
    service_name: str
    release_stage: str
    api_version: str
    response_schema_version: str


class MetadataResponse(BaseModel):
    service_name: str
    release_stage: str
    api_version: str
    response_schema_version: str
    default_backend: str
    battle_dex_available: bool
    session_continuity: str
    provider_key_mode: str
    rate_limit_mode: str
    unofficial_notice: str
    features: list[str]


class PersonaSelectorKind(StrEnum):
    BUILT_IN = "built_in"
    MANAGED = "managed"


class PersonaSelector(BaseModel):
    kind: PersonaSelectorKind
    persona_id: str = Field(min_length=1)
    version: str | None = None
    revision: int | None = Field(default=None, ge=1)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None
    persona_id: str | None = None
    persona_selector: PersonaSelector | None = None


class ChatResponse(BaseModel):
    session_id: str
    response: AgentResponse


class TeamSlotInput(BaseModel):
    primary_type: str = Field(min_length=1)
    secondary_type: str | None = None


class TeamAnalyzeRequest(BaseModel):
    team: list[TeamSlotInput] = Field(min_length=1, max_length=6)
    persona_id: str | None = None
    persona_selector: PersonaSelector | None = None


class SpeciesSearchItem(BaseModel):
    species_id: str
    display_name: str
    initial_species_name: str | None = None
    primary_type: str
    secondary_type: str | None = None


class SpeciesSearchResponse(BaseModel):
    query: str
    results: list[SpeciesSearchItem]


class SpeciesProfileResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    profile: dict[str, Any]


class ApiError(BaseModel):
    code: str
    message: str
