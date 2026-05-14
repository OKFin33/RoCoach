#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Missing .venv/bin/python. Create a venv and install requirements first:" >&2
  echo "  python3 -m venv .venv" >&2
  echo "  .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

if ! ".venv/bin/python" -c "import uvicorn" >/dev/null 2>&1; then
  echo "Missing Python backend dependencies. Run:" >&2
  echo "  .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

cd desktop
if [[ ! -d "node_modules" ]]; then
  npm install
fi

npm run dev
