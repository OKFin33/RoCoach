from __future__ import annotations

from pathlib import Path

from fastapi import Request

from advisor.battle_dex import DEFAULT_RUNTIME_DB
from api.services.advisor_service import AdvisorService


def get_advisor_service(request: Request) -> AdvisorService:
    return request.app.state.advisor_service


def rate_limit_placeholder() -> None:
    """No-op placeholder for local/public-prep builds; not production abuse control."""
    return None


def default_db_path() -> Path:
    return DEFAULT_RUNTIME_DB
