#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if docker compose version >/dev/null 2>&1; then
    COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose)
else
    echo "Error: docker compose is required"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker Desktop must be running before you call make demo."
    exit 1
fi

INVENTORY_SERVICE="http://localhost:8080"
ANALYTICS_SERVICE="http://localhost:8000"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-ims-postgres}"
REDIS_CONTAINER="${REDIS_CONTAINER:-ims-redis}"
POSTGRES_DB="${POSTGRES_DB:-inventory}"
POSTGRES_USER="${POSTGRES_USER:-inventory_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-inventory_pass}"
REDIS_PASSWORD="${REDIS_PASSWORD:-redis_pass}"
INVENTORY_USER="${INVENTORY_SECURITY_USERNAME:-demo_user}"
INVENTORY_PASSWORD="${INVENTORY_SECURITY_PASSWORD:-demo_pass}"
DATA_DIR="$REPO_ROOT/data-pipeline-service/data"
ARTIFACT_DIR="$REPO_ROOT/artifacts/demo"

mkdir -p "$ARTIFACT_DIR" "$DATA_DIR"
rm -rf "$DATA_DIR"/run_date=* 2>/dev/null || true
rm -f "$DATA_DIR"/*.parquet "$DATA_DIR"/*.json 2>/dev/null || true
rm -f "$ARTIFACT_DIR"/*.txt "$ARTIFACT_DIR"/*.json "$ARTIFACT_DIR"/*.md 2>/dev/null || true

echo "Starting supported demo stack..."
"${COMPOSE[@]}" -f "$REPO_ROOT/docker-compose.dev.yml" up --build -d postgres redis zookeeper kafka inventory-service analytics-service data-pipeline prometheus grafana

echo "Waiting for services to become healthy..."
until curl -s -f "$INVENTORY_SERVICE/actuator/health" >/dev/null; do sleep 2; done
until curl -s -f "$ANALYTICS_SERVICE/health/" >/dev/null; do sleep 2; done
until curl -s -f "http://localhost:9090/-/ready" >/dev/null; do sleep 2; done
until curl -s -f "http://localhost:3001/api/health" >/dev/null; do sleep 2; done

"$SCRIPT_DIR/seed-data.sh"

echo "Capturing inventory before the live event..."
curl -s -u "$INVENTORY_USER:$INVENTORY_PASSWORD" \
    "$INVENTORY_SERVICE/api/v1/inventory/LAPTOP-001/WAREHOUSE-001" \
    > "$ARTIFACT_DIR/inventory_before.json"

echo "Triggering a live sale event..."
curl -s -u "$INVENTORY_USER:$INVENTORY_PASSWORD" -X POST \
    "$INVENTORY_SERVICE/api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=1" \
    > "$ARTIFACT_DIR/sale_response.json"

echo "Waiting for the ETL consumer to process the event..."
sleep 10

curl -s -u "$INVENTORY_USER:$INVENTORY_PASSWORD" \
    "$INVENTORY_SERVICE/api/v1/inventory/LAPTOP-001/WAREHOUSE-001" \
    > "$ARTIFACT_DIR/inventory_after.json"

curl -s \
    "$ANALYTICS_SERVICE/api/v1/analytics/velocity/LAPTOP-001/WAREHOUSE-001?period_days=30" \
    > "$ARTIFACT_DIR/analytics_velocity.json"

docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_CONTAINER" \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
    "select sku, warehouse_id, velocity_7d, velocity_30d, stockout_risk, updated_at from analytics.current_metrics order by updated_at desc limit 5;" \
    > "$ARTIFACT_DIR/current_metrics.txt"

docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_CONTAINER" \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
    "select run_id, status, source_event_count, valid_event_count, duplicate_event_count, invalid_event_count, processed_metric_count, dq_status, completed_at from analytics.pipeline_runs order by completed_at desc nulls last, started_at desc limit 5;" \
    > "$ARTIFACT_DIR/pipeline_runs.txt"

docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_CONTAINER" \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
    "select run_id, status, checked_at from analytics.data_quality_runs order by checked_at desc limit 5;" \
    > "$ARTIFACT_DIR/data_quality_runs.txt"

docker exec "$REDIS_CONTAINER" redis-cli -a "$REDIS_PASSWORD" \
    HGETALL metrics:LAPTOP-001:WAREHOUSE-001 \
    > "$ARTIFACT_DIR/redis_metrics.txt"

if ls "$DATA_DIR"/*.parquet >/dev/null 2>&1; then
    ls -lh "$DATA_DIR"/*.parquet > "$ARTIFACT_DIR/parquet_files.txt"
elif find "$DATA_DIR" -name '*.parquet' | grep -q .; then
    find "$DATA_DIR" -name '*.parquet' -print | sort > "$ARTIFACT_DIR/parquet_files.txt"
else
    echo "No parquet files were produced" > "$ARTIFACT_DIR/parquet_files.txt"
fi

LATEST_MANIFEST="$(find "$DATA_DIR" -name manifest.json -print | sort | tail -n 1 || true)"
if [[ -n "$LATEST_MANIFEST" ]]; then
    cp "$LATEST_MANIFEST" "$ARTIFACT_DIR/latest_run_manifest.json"
fi

cat > "$ARTIFACT_DIR/summary.md" <<EOF
# Demo Summary

- Inventory before live sale: inventory_before.json
- Inventory after live sale: inventory_after.json
- Analytics response: analytics_velocity.json
- Latest Postgres current metrics: current_metrics.txt
- Latest pipeline runs: pipeline_runs.txt
- Latest data quality runs: data_quality_runs.txt
- Latest Redis hash: redis_metrics.txt
- Generated Parquet files: parquet_files.txt
- Latest run manifest: latest_run_manifest.json
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
EOF

echo "Demo complete. Artifacts written to $ARTIFACT_DIR"
