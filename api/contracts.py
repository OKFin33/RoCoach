from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class ModelDiagnosticRequest(BaseModel):
    prompt: str = "用一句中文回答：Roco 模型服务连接是否成功？"


class ModelDiagnosticResponse(BaseModel):
    status: Literal["ok", "failed"]
    diagnostic_code: str
    message: str
    provider_family_hint: str


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
    context_attachments: list[dict[str, Any]] = Field(default_factory=list)


class SessionEventPayload(BaseModel):
    type: Literal["started", "continued", "reconciled", "cleared", "rolled_over"]
    reason: str
    message: str
    user_action: str | None = None
    diagnostic: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    session_id: str
    response: AgentResponse
    session_event: SessionEventPayload | None = None


class SessionClearRequest(BaseModel):
    reason: str = "user_clear"


class SessionClearResponse(BaseModel):
    session_id: str
    session_event: SessionEventPayload


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
    form_name: str | None = None
    regional_form_name: str | None = None
    primary_type: str
    secondary_type: str | None = None


class SpeciesSearchResponse(BaseModel):
    query: str
    results: list[SpeciesSearchItem]


class SpeciesProfileResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    profile: dict[str, Any]


class SpeciesMovesResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    species_id: str
    moves: list[dict[str, Any]]


class TeamStatKey(StrEnum):
    HP = "hp"
    ATK = "atk"
    DEFENSE = "defense"
    SPA = "spa"
    SPD = "spd"
    SPE = "spe"


class TeamAbilitySnapshot(BaseModel):
    ability_name: str = Field(min_length=1)
    effect_text: str | None = None


class TeamMoveSelection(BaseModel):
    move_id: str = Field(min_length=1)
    move_name: str = Field(min_length=1)
    access_channel: str | None = None
    move_type: str | None = None
    category_raw: str | None = None


class TeamNature(BaseModel):
    label: str | None = None
    plus_stat: TeamStatKey | None = None
    minus_stat: TeamStatKey | None = None


class TeamIndividualValueBonus(BaseModel):
    stat: TeamStatKey
    value: int = Field(ge=7, le=10)


class TeamContextSlot(BaseModel):
    slot_index: int = Field(ge=1, le=6)
    species_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    primary_type: str = Field(min_length=1)
    secondary_type: str | None = None
    fixed_ability: TeamAbilitySnapshot | None = None
    selected_moves: list[TeamMoveSelection] = Field(default_factory=list, max_length=4)
    nature: TeamNature
    individual_value_bonuses: list[TeamIndividualValueBonus] = Field(default_factory=list, max_length=3)
    notes: str | None = None

    @model_validator(mode="after")
    def _validate_unique_bonus_stats(self) -> "TeamContextSlot":
        stats = [bonus.stat for bonus in self.individual_value_bonuses]
        if len(stats) != len(set(stats)):
            raise ValueError("individual_value_bonuses stats must be unique within a slot")
        return self


class TeamContextAttachment(BaseModel):
    kind: Literal["team_context"]
    schema_version: Literal["team_context.v1"]
    source: Literal["team_builder"]
    team_id: str = Field(min_length=1)
    active: Literal[True]
    slots: list[TeamContextSlot] = Field(default_factory=list, max_length=6)

    @model_validator(mode="after")
    def _validate_unique_slots(self) -> "TeamContextAttachment":
        indexes = [slot.slot_index for slot in self.slots]
        if len(indexes) != len(set(indexes)):
            raise ValueError("slot_index values must be unique within a team")
        return self


class ApiError(BaseModel):
    code: str
    message: str
