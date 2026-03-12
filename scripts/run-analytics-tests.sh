#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="${ANALYTICS_TEST_VENV:-$REPO_ROOT/.venv-analytics-tests}"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required to run analytics-service tests."
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install -r "$REPO_ROOT/analytics-service/requirements.txt" pytest
"$VENV_DIR/bin/python" -m pytest "$REPO_ROOT/analytics-service/tests" -q
