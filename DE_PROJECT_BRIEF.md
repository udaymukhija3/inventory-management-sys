# Project Brief: Event-Driven Inventory Analytics

## What it is

A runnable data engineering project that turns operational inventory mutations into analytical outputs across Postgres, Redis, and Parquet.

## Primary flow

- `inventory-service` writes transactional inventory changes to Postgres
- the same service emits Kafka events with stable `eventId` and transaction references
- `data-pipeline-service` validates, deduplicates, enriches, and materializes metrics
- `analytics-service` serves the ETL outputs from Postgres and Redis

## Why it signals data engineering work

- event-driven ingestion
- current-state plus history modeling
- idempotent processing via event log
- explicit forced reprocess mode for backfills
- persisted DQ reports and run manifests
- multi-sink outputs: Postgres, Redis, Parquet, DLQ, Kafka alerts
- Prometheus/Grafana observability in the demo stack

## Demo command

```bash
cp .env.example .env
make demo
```

## Proof files

- `artifacts/demo/inventory_before.json`
- `artifacts/demo/inventory_after.json`
- `artifacts/demo/current_metrics.txt`
- `artifacts/demo/pipeline_runs.txt`
- `artifacts/demo/data_quality_runs.txt`
- `artifacts/demo/latest_run_manifest.json`
- `artifacts/demo/parquet_files.txt`

## Useful follow-up command

```bash
FORCE_REPROCESS=true make backfill BACKFILL_START=2026-03-01T00:00:00 BACKFILL_END=2026-03-13T00:00:00
```
