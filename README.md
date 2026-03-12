# Event-Driven Inventory Analytics

This repo is a runnable inventory analytics demo built around one supported path:

1. `inventory-service` writes inventory changes to PostgreSQL and publishes Kafka events
2. `data-pipeline-service` consumes those events, enriches them with historical transaction data, and writes analytics outputs to PostgreSQL, Redis, and Parquet
3. `analytics-service` reads the ETL outputs from PostgreSQL and Redis

The rest of the repo is secondary. The supported demo path is the services above.

## Supported Architecture

```text
inventory-service --> PostgreSQL inventory tables
inventory-service --> Kafka inventory-events
Kafka + PostgreSQL --> data-pipeline-service
data-pipeline-service --> PostgreSQL analytics.current_metrics + analytics.metric_history
data-pipeline-service --> PostgreSQL analytics.pipeline_runs + analytics.data_quality_runs
data-pipeline-service --> PostgreSQL analytics.processed_event_log + analytics.invalid_inventory_events
data-pipeline-service --> Redis metrics:{sku}:{warehouse_id}
data-pipeline-service --> Partitioned Parquet + run manifests under data-pipeline-service/data/
analytics-service --> PostgreSQL + Redis
```

## Supported Demo

### Prerequisites

- Docker Desktop with Compose support
- Docker Desktop running locally (`docker info` should succeed)
- `curl`
- `make`

### Demo Credentials

- Username: `demo_user`
- Password: `demo_pass`

Override them with `.env` if needed. See `.env.example`.

### Fastest Path

```bash
cp .env.example .env
make demo
```

That command:

- starts the supported local stack from `docker-compose.dev.yml`
- loads deterministic demo data from `infrastructure/docker/postgres/demo-seed.sql`
- triggers one live sale event
- waits for the ETL consumer to process it
- brings up Prometheus and Grafana for the same supported stack
- writes proof artifacts into `artifacts/demo/`

### Proof Artifacts

After `make demo`, inspect:

- `artifacts/demo/README.md`
- `artifacts/demo/inventory_before.json`
- `artifacts/demo/inventory_after.json`
- `artifacts/demo/analytics_velocity.json`
- `artifacts/demo/current_metrics.txt`
- `artifacts/demo/pipeline_runs.txt`
- `artifacts/demo/data_quality_runs.txt`
- `artifacts/demo/redis_metrics.txt`
- `artifacts/demo/parquet_files.txt`
- `artifacts/demo/latest_run_manifest.json`
- `artifacts/demo/summary.md`

Local monitoring during the demo:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- Grafana credentials: `admin / admin` by default
- The lightweight demo stack scrapes only `inventory-service`, `analytics-service`, and `data-pipeline`.

## Useful Commands

```bash
make up
make seed
make demo
make test
bash ./scripts/backfill.sh 2026-03-01T00:00:00 2026-03-13T00:00:00
FORCE_REPROCESS=true make backfill BACKFILL_START=2026-03-01T00:00:00 BACKFILL_END=2026-03-13T00:00:00
./scripts/health-check.sh
./scripts/test-apis.sh
```

## Core Components

- `inventory-service`: Spring Boot service for inventory writes, audit rows, and Kafka publication
- `data-pipeline-service`: Python ETL consumer that writes PostgreSQL, Redis, and Parquet outputs
  - idempotent event processing via `analytics.processed_event_log`
  - current-state serving table in `analytics.current_metrics`
  - history table in `analytics.metric_history`
  - per-run manifests and DQ reports in PostgreSQL and `data-pipeline-service/data/`
- `analytics-service`: FastAPI service that reads ETL-derived analytics
- `infrastructure/docker/postgres`: database initialization and deterministic demo seed
- `scripts`: supported setup, demo, health, and API test scripts

## Supported Tests

```bash
cd inventory-service && mvn test
./scripts/run-analytics-tests.sh
bash ./scripts/run-data-pipeline-tests.sh
```

The default `make test` target runs those supported tests.

## Optional / Secondary Components

These are present in the repo but are not part of the supported demo path:

- `airflow`
- `reorder-service`
- `api-gateway`
- `monitoring`
- `stream-processor`

Use them as extensions, not as the primary proof that this project works.
