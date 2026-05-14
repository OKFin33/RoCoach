from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, ValidationError, field_validator


REASONING_MODE_DISABLED = "disabled"
REASONING_MODE_ENABLED = "enabled"
REASONING_EFFORT_HIGH = "high"
REASONING_EFFORT_MAX = "max"


DEFAULT_ENV_PATH = Path.home() / ".config" / "roco-advisor" / "env"


class RocoNativeModelConfig(BaseModel):
    model_name: str
    base_url: str
    api_key: str
    reasoning_mode: str = REASONING_MODE_DISABLED
    reasoning_effort: str | None = None

    @field_validator("model_name", "base_url", "api_key")
    @classmethod
    def _require_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("value must not be empty")
        return normalized

    @field_validator("base_url")
    @classmethod
    def _require_safe_provider_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme == "https" and parsed.netloc:
            return value
        if parsed.scheme == "http" and _is_loopback_host(parsed.hostname):
            return value
        if parsed.scheme in {"http", "https"}:
            raise ValueError("base_url must use https unless it targets loopback http")
        raise ValueError("base_url must start with https:// or loopback http://")

    @field_validator("api_key")
    @classmethod
    def _reject_placeholder_api_key(cls, value: str) -> str:
        placeholders = {
            "your-live-key",
            "replace-with-live-local-secret",
            "<set-local-secret>",
            "changeme",
        }
        if value.lower() in placeholders:
            raise ValueError("api_key placeholder is not valid runtime config")
        return value

    @field_validator("reasoning_mode")
    @classmethod
    def _validate_reasoning_mode(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if normalized not in {REASONING_MODE_DISABLED, REASONING_MODE_ENABLED}:
            raise ValueError("reasoning_mode must be disabled or enabled")
        return normalized

    @field_validator("reasoning_effort")
    @classmethod
    def _validate_reasoning_effort(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().casefold()
        if normalized not in {REASONING_EFFORT_HIGH, REASONING_EFFORT_MAX}:
            raise ValueError("reasoning_effort must be high or max")
        return normalized


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_native_model_config(
    *,
    env_path: Path | None = None,
    model_name_override: str | None = None,
) -> RocoNativeModelConfig | None:
    values = load_env_file(env_path or DEFAULT_ENV_PATH)
    model_name = model_name_override or values.get("ROCO_ADVISOR_MODEL")
    base_url = values.get("ROCO_OPENAI_BASE_URL")
    api_key = values.get("ROCO_OPENAI_API_KEY")

    if not model_name or not base_url or not api_key:
        return None

    try:
        return RocoNativeModelConfig(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key,
        )
    except ValidationError:
        return None


def _is_loopback_host(hostname: str | None) -> bool:
    if hostname is None:
        return False
    return hostname.casefold() in {"localhost", "127.0.0.1", "::1"}
