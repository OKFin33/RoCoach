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

if [[ ! -x ".venv/bin/uvicorn" ]]; then
  echo "Missing .venv/bin/uvicorn. Run .venv/bin/pip install -r requirements.txt first." >&2
  exit 1
fi

exec .venv/bin/uvicorn api.main:app \
  --reload \
  --host "${ROCO_API_HOST:-127.0.0.1}" \
  --port "${ROCO_API_PORT:-8000}"
