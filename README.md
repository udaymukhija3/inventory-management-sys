# Inventory Management System

An inventory operations service plus a streaming analytics pipeline:
every stock movement is written transactionally by a Spring Boot service,
published as a Kafka event, consumed by a Python ETL, and materialized
into Postgres analytics, Redis cache, and Parquet files. A FastAPI
service then serves the derived metrics, and a static dashboard ties
the whole loop together.

## Live Demo

- **Public frontend preview:** <https://udaymukhija3.github.io/inventory-management-sys/>
  is published by the GitHub Pages workflow on every `main` push.
- **Static frontend (preview mode):** deploy with the Vercel button below — without
  a reachable backend the dashboard renders in *preview mode* with
  illustrative data and a clear banner telling the viewer to run the stack
  locally for live numbers.
- **Full end-to-end demo (live data):** run locally with `make demo`.

## Deploy The Frontend To Vercel

The `frontend/` directory is a static HTML/JS dashboard. It deploys to
GitHub Pages automatically via `.github/workflows/pages.yml`, or to
Vercel with no build step.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/udaymukhija3/inventory-management-sys&root-directory=frontend&project-name=inventory-management-sys-frontend)

When deployed without a backend the page detects unreachable endpoints
and renders preview data (with a visible *Preview mode* banner). To wire
the deployed frontend to a real backend, set
`window.__APP_CONFIG__.API_BASE_URL` in `frontend/js/config.js` to a
publicly reachable URL that fronts the inventory service (`/api/v1/...`)
and the analytics service (`/api/v1/analytics/...`). The simplest way to
expose those locally is via an `ngrok`/`cloudflared` tunnel pointed at
the in-stack Nginx (port 3000), which already proxies both services.

## Run Locally (One Command)

```bash
git clone https://github.com/udaymukhija3/inventory-management-sys.git
cd inventory-management-sys
cp .env.example .env 2>/dev/null || true
make demo
```

This brings up the supported stack from `docker-compose.dev.yml`, seeds
deterministic demo data, triggers a live sale, waits for the ETL
consumer to process it, and writes proof artifacts to `artifacts/demo/`.
The dashboard is available at <http://localhost:3000>.

Prerequisites: Docker Desktop with Compose, `make`, `curl`.

## Architecture

```
inventory-service ──Kafka producer──▶ inventory-events
                                           │
                                           ▼
                                  data-pipeline-service
                                           │
                          ┌────────────────┼────────────────┐
                          ▼                ▼                ▼
                  analytics schema   metrics:{sku}        Parquet +
                   in Postgres       in Redis            run manifest
                          │
                          ▼
                  analytics-service (FastAPI) ──▶ frontend dashboard
```

| Component             | Stack                                   | Responsibility                                                          |
| --------------------- | --------------------------------------- | ----------------------------------------------------------------------- |
| `inventory-service`   | Spring Boot, Java 17, Postgres, Redis   | Source-of-truth inventory APIs, transactional writes, event publication |
| `data-pipeline-service` | Python 3.11, Kafka, Postgres, Redis   | Consumes inventory events, computes metrics, writes outputs             |
| `analytics-service`   | FastAPI, Python 3.11, Postgres, Redis   | Serves ETL-derived analytics over HTTP                                  |
| `frontend`            | Static HTML/JS via Nginx                | Demo monitor with a live "Trigger sale" action                          |
| `prometheus + grafana`| Prometheus, Grafana                     | Health, metrics, dashboards                                             |

## URLs You Will Care About

Once the demo stack is up:

- Frontend dashboard: <http://localhost:3000>
- Inventory service: <http://localhost:8080>
- Inventory Swagger UI: <http://localhost:8080/swagger-ui/index.html>
- Analytics service: <http://localhost:8000>
- Analytics docs: <http://localhost:8000/api/docs>
- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3001> (default `admin / admin`)

## Manual Verification

If you want to verify things by hand instead of trusting the generated
artifacts under `artifacts/demo/`:

```bash
# Service health
./scripts/health-check.sh

# Read inventory for the seeded focus SKU
curl -s -u demo_user:demo_pass \
  http://localhost:8080/api/v1/inventory/LAPTOP-001/WAREHOUSE-001

# Trigger a sale
curl -s -u demo_user:demo_pass -X POST \
  "http://localhost:8080/api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=1"

# Read the analytics view
curl -s "http://localhost:8000/api/v1/analytics/velocity/LAPTOP-001/WAREHOUSE-001?period_days=30"

# Inspect analytics health (with pipeline freshness)
curl -s http://localhost:8000/health/detailed
```

The frontend at <http://localhost:3000> wraps these calls behind a single
*Trigger Live Sale* button. After clicking it, the inventory and
velocity panels both refresh against the real services.

## What `make demo` Captures

The end-to-end script (`scripts/demo.sh`) writes the following to
`artifacts/demo/`:

| File                          | Source                                                |
| ----------------------------- | ----------------------------------------------------- |
| `inventory_before.json`       | Inventory state before the live sale                  |
| `sale_response.json`          | Response from the inventory `sale` endpoint           |
| `inventory_after.json`        | Inventory state after the pipeline has caught up      |
| `analytics_velocity.json`     | Analytics service response for the focus SKU          |
| `current_metrics.txt`         | Latest rows from `analytics.current_metrics`          |
| `pipeline_runs.txt`           | Latest rows from `analytics.pipeline_runs`            |
| `data_quality_runs.txt`       | Latest rows from `analytics.data_quality_runs`        |
| `redis_metrics.txt`           | `metrics:LAPTOP-001:WAREHOUSE-001` hash from Redis    |
| `parquet_files.txt`           | Parquet files produced by the pipeline                |
| `latest_run_manifest.json`    | The most recent run manifest                          |
| `summary.md`                  | One-page index of everything above                    |

Open `artifacts/demo/summary.md` first if you only want one place to look.

## Useful Commands

```bash
make up        # start the supported local stack
make seed      # load deterministic demo data
make demo      # full end-to-end demo with proof artifacts
make build     # build the supported services
make test      # run inventory + analytics + pipeline test suites
make clean     # tear it all down
make backfill BACKFILL_START=2026-03-01T00:00:00 BACKFILL_END=2026-03-13T00:00:00
FORCE_REPROCESS=true make backfill BACKFILL_START=2026-03-01T00:00:00 BACKFILL_END=2026-03-13T00:00:00
./scripts/health-check.sh
./scripts/test-apis.sh
```

## Configuration

You do **not** need a `.env` file for the supported local demo. The
defaults are captured in [.env.example](.env.example), and
`docker-compose.dev.yml` provides local-safe fallbacks. Copy
`.env.example` to `.env` only if you want to override credentials.

The dev demo defaults are:

- inventory Basic Auth: `demo_user / demo_pass`
- Grafana: `admin / admin`
- Postgres: `inventory_user / inventory_pass`
- Redis password: `redis_pass`

## Repository Map

- `inventory-service/` — Spring Boot operational APIs and Kafka producer
- `data-pipeline-service/` — Python streaming + backfill ETL
- `analytics-service/` — FastAPI analytics serving layer
- `frontend/` — static demo dashboard (deployable to Vercel)
- `infrastructure/docker/postgres/` — schema bootstrap and deterministic seed SQL
- `scripts/` — demo, health, seed, smoke-test, and backfill helpers
- `monitoring/` — Prometheus config and Grafana provisioning
- `artifacts/demo/` — proof pack generated by `make demo`

## Scope Note

This repo also contains an `api-gateway`, `reorder-service`, `airflow`,
`stream-processor`, and a fuller `docker-compose.yml` with Mongo and
Elasticsearch. Those are *experimental* — they are not part of the
supported demo path, are not exercised by `make demo` or `make test`,
and may not start cleanly. If your goal is "does the system actually
work end to end?", stay with `docker-compose.dev.yml` and the commands
in this README.
