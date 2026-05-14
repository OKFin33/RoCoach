from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import ValidationError

from advisor.config import RocoNativeModelConfig


HEADER_PROVIDER_KEY = "X-Roco-Provider-Key"
HEADER_PROVIDER_BASE_URL = "X-Roco-Provider-Base-Url"
HEADER_MODEL = "X-Roco-Model"
HEADER_RUNTIME_MODE = "X-Roco-Runtime-Mode"
HEADER_REASONING_MODE = "X-Roco-Reasoning-Mode"
HEADER_REASONING_EFFORT = "X-Roco-Reasoning-Effort"

SENSITIVE_RUNTIME_HEADER_NAMES = frozenset(
    {
        HEADER_PROVIDER_KEY.casefold(),
        HEADER_REASONING_MODE.casefold(),
        HEADER_REASONING_EFFORT.casefold(),
        "authorization",
        "roco_openai_api_key",
    }
)


class RequestRuntimeMode(StrEnum):
    DETERMINISTIC = "deterministic"
    NATIVE = "native"
    AUTO = "auto"


@dataclass(frozen=True)
class RequestRuntimeConfig:
    mode: RequestRuntimeMode
    native_model_config: RocoNativeModelConfig | None = None
    setup_error: str | None = None

    @property
    def requests_native_runtime(self) -> bool:
        return self.mode in {RequestRuntimeMode.NATIVE, RequestRuntimeMode.AUTO}


def request_runtime_config_from_headers(
    *,
    provider_key: str | None,
    provider_base_url: str | None,
    model: str | None,
    runtime_mode: str | None,
    reasoning_mode: str | None = None,
    reasoning_effort: str | None = None,
) -> RequestRuntimeConfig:
    has_provider_header = any(_present(value) for value in (provider_key, provider_base_url, model))
    mode = _parse_runtime_mode(runtime_mode)
    if mode is None:
        return RequestRuntimeConfig(
            mode=RequestRuntimeMode.NATIVE,
            setup_error="unsupported_runtime_mode",
        )
    if mode == RequestRuntimeMode.DETERMINISTIC and has_provider_header:
        return RequestRuntimeConfig(
            mode=RequestRuntimeMode.NATIVE,
            setup_error="missing_runtime_mode",
        )
    if mode == RequestRuntimeMode.DETERMINISTIC:
        return RequestRuntimeConfig(mode=mode)

    if not _present(provider_key) or not _present(provider_base_url) or not _present(model):
        return RequestRuntimeConfig(mode=mode, setup_error="missing_native_runtime_config")

    try:
        native_config = RocoNativeModelConfig(
            model_name=model or "",
            base_url=provider_base_url or "",
            api_key=provider_key or "",
            reasoning_mode=_parse_reasoning_mode(reasoning_mode) or "disabled",
            reasoning_effort=_parse_reasoning_effort(reasoning_effort),
        )
    except ValidationError:
        return RequestRuntimeConfig(mode=mode, setup_error="invalid_native_runtime_config")

    return RequestRuntimeConfig(mode=mode, native_model_config=native_config)


def redact_runtime_text(
    text: str,
    *,
    provider_key: str | None = None,
    provider_base_url: str | None = None,
    model: str | None = None,
) -> str:
    redacted = text
    for value in (provider_key, provider_base_url, model):
        if _present(value):
            redacted = redacted.replace(value.strip(), "[REDACTED]")
    for header_name in (
        HEADER_PROVIDER_KEY,
        HEADER_PROVIDER_BASE_URL,
        HEADER_MODEL,
        HEADER_RUNTIME_MODE,
        HEADER_REASONING_MODE,
        HEADER_REASONING_EFFORT,
        "ROCO_OPENAI_API_KEY",
        "Authorization",
    ):
        redacted = redacted.replace(header_name, "[REDACTED_HEADER]")
    return redacted


def _parse_runtime_mode(value: str | None) -> RequestRuntimeMode | None:
    normalized = (value or "").strip().casefold()
    if normalized in {"", "default", "deterministic"}:
        return RequestRuntimeMode.DETERMINISTIC
    if normalized in {"native", "pydantic_ai_native", "pydantic_ai"}:
        return RequestRuntimeMode.NATIVE
    if normalized == "auto":
        return RequestRuntimeMode.AUTO
    return None


def _parse_reasoning_mode(value: str | None) -> str | None:
    normalized = (value or "").strip().casefold()
    if normalized in {"", "disabled", "off", "none"}:
        return "disabled"
    if normalized in {"enabled", "on"}:
        return "enabled"
    return None


def _parse_reasoning_effort(value: str | None) -> str | None:
    normalized = (value or "").strip().casefold()
    if normalized in {"", "none"}:
        return None
    if normalized in {"high", "max"}:
        return normalized
    return None


def _present(value: str | None) -> bool:
    return bool(value and value.strip())
