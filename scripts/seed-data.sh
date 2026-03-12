#!/bin/bash

# Deterministic SQL seed for the supported demo path.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-ims-postgres}"
POSTGRES_DB="${POSTGRES_DB:-inventory}"
POSTGRES_USER="${POSTGRES_USER:-inventory_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-inventory_pass}"
SEED_FILE="$REPO_ROOT/infrastructure/docker/postgres/demo-seed.sql"

echo "Seeding deterministic demo data..."

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker is required"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker Desktop must be running before you seed demo data."
    exit 1
fi

if [ ! -f "$SEED_FILE" ]; then
    echo "Error: $SEED_FILE not found"
    exit 1
fi

echo "Waiting for application tables to exist..."
until docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_CONTAINER" \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atqc "select to_regclass('public.products')" | grep -q products; do
    sleep 2
done

docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" -i "$POSTGRES_CONTAINER" \
    psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$SEED_FILE"

echo "Deterministic demo data loaded."
