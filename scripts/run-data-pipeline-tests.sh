#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="${DATA_PIPELINE_TEST_VENV:-$REPO_ROOT/.venv-data-pipeline-tests}"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip >/dev/null
pip install -r "$REPO_ROOT/data-pipeline-service/requirements.txt" pytest >/dev/null

export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_DB="${POSTGRES_DB:-inventory}"
export POSTGRES_USER="${POSTGRES_USER:-inventory_user}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-inventory_pass}"

pytest "$REPO_ROOT/data-pipeline-service/tests" -q
