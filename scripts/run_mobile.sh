#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/apps/mobile"

if [[ ! -d "node_modules" ]]; then
  npm install
fi

exec npm run start
