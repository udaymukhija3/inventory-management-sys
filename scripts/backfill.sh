#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <backfill-start-iso> <backfill-end-iso>"
    exit 1
fi

if docker compose version >/dev/null 2>&1; then
    COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose)
else
    echo "Error: docker compose is required"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker Desktop must be running before you call scripts/backfill.sh."
    exit 1
fi

BACKFILL_START="$1"
BACKFILL_END="$2"
FORCE_REPROCESS="${FORCE_REPROCESS:-false}"
PIPELINE_ARGS=(
    python data_pipeline.py
    --mode backfill
    --backfill-start "$BACKFILL_START"
    --backfill-end "$BACKFILL_END"
)

if [[ "$FORCE_REPROCESS" == "true" ]]; then
    PIPELINE_ARGS+=(--force-reprocess)
fi

"${COMPOSE[@]}" -f "$REPO_ROOT/docker-compose.dev.yml" up --build -d postgres redis zookeeper kafka inventory-service analytics-service
"${COMPOSE[@]}" -f "$REPO_ROOT/docker-compose.dev.yml" run --rm data-pipeline "${PIPELINE_ARGS[@]}"
