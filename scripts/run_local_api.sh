#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

ENV_FILE="${ROCO_ENV_FILE:-${HOME}/.config/roco-advisor/env}"
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

DEFAULT_MANAGED_PERSONA_PATH="${ROOT_DIR}/artifacts/persona_runtime/you_know_who_minimal/materialized_profiles.yaml"
if [[ -z "${ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH:-}" ]] && [[ -f "${DEFAULT_MANAGED_PERSONA_PATH}" ]]; then
  export ROCO_MANAGED_PERSONA_MATERIALIZATION_PATH="${DEFAULT_MANAGED_PERSONA_PATH}"
fi
export ROCO_MANAGED_PERSONA_SCOPE="${ROCO_MANAGED_PERSONA_SCOPE:-internal_only_runtime}"

if [[ ! -x ".venv/bin/uvicorn" ]]; then
  echo "Missing .venv/bin/uvicorn. Run .venv/bin/pip install -r requirements.txt first." >&2
  exit 1
fi

exec env PYTHONPATH="${ROOT_DIR}/src" .venv/bin/uvicorn api.main:app \
  --reload \
  --host "${ROCO_API_HOST:-127.0.0.1}" \
  --port "${ROCO_API_PORT:-8000}"
