# Data Pipeline Service

Real-time ETL pipeline for inventory data processing that consumes events from Kafka, performs data transformation, calculates basic analytics, and outputs results to multiple data stores.

## Features

- **Kafka Consumption**: Consumes inventory events from Kafka in stream mode
- **Backfills**: Rebuilds analytics from `inventory_transactions` for a date range
- **Data Transformation**: Transforms events into structured data
- **Feature Engineering**: Calculates velocity, volatility, trend, and seasonality (basic analytics, not ML)
- **Analytics Calculation**: Calculates stockout risk and reorder recommendations using basic statistical methods
- **Idempotency**: Deduplicates events via `analytics.processed_event_log`
- **Data Quality**: Persists freshness/range/uniqueness/reconciliation checks per run
- **Data Output**: Writes to PostgreSQL, Redis, and partitioned Parquet files
- **Event Publishing**: Publishes alerts to Kafka topics

## Configuration

Environment variables:
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses (default: localhost:9092)
- `POSTGRES_HOST`: PostgreSQL host (default: localhost)
- `POSTGRES_DB`: Database name (default: inventory)
- `POSTGRES_USER`: Database user (default: inventory_user)
- `POSTGRES_PASSWORD`: Database password
- `REDIS_HOST`: Redis host (default: localhost)
- `REDIS_PORT`: Redis port (default: 6379)
- `REDIS_PASSWORD`: Redis password (optional)
- `BATCH_SIZE`: Batch processing size (default: 100)
- `DATA_DIR`: Path for Parquet output (default: ./data)
- `PIPELINE_METRICS_PORT`: Prometheus metrics port (default: 8001)
- `PIPELINE_FORCE_REPROCESS`: Recompute metrics even when an event already exists in the dedupe log

## Usage

```bash
python data_pipeline.py
```

Run a bounded backfill:

```bash
python data_pipeline.py --mode backfill --backfill-start 2026-03-01T00:00:00 --backfill-end 2026-03-13T00:00:00
```

Force a backfill reprocess for an already-seen range:

```bash
python data_pipeline.py --mode backfill --backfill-start 2026-03-01T00:00:00 --backfill-end 2026-03-13T00:00:00 --force-reprocess
```

Or with Docker:

```bash
docker build -t data-pipeline-service .
docker run -e POSTGRES_PASSWORD=your_password data-pipeline-service
```

## Data Processing Flow

1. **Consume Events** - Consume inventory events from Kafka
2. **Transform Events** - Transform events into structured data
3. **Calculate Metrics** - Calculate velocity, volatility, trend, seasonality
4. **Calculate Business Metrics** - Calculate stockout risk and reorder recommendations
5. **Store Data** - Store in PostgreSQL, Redis, and Parquet files
6. **Publish Alerts** - Publish high stockout risk alerts to Kafka

## Analytics Calculations

### Velocity
- **Velocity 7d**: Average daily sales over last 7 days
- **Velocity 30d**: Average daily sales over last 30 days

### Volatility
- **Volatility**: Standard deviation of daily sales

### Trend
- **Trend**: Linear regression slope of daily sales

### Seasonality
- **Seasonality Index**: Ratio of recent sales to monthly average

### Stockout Risk
- **Stockout Risk**: Basic statistical calculation based on velocity, volatility, trend, and seasonality (not ML)

### Reorder Recommendation
- **Reorder Quantity**: Calculated based on velocity, volatility, and stockout risk

## Output

### PostgreSQL
- **analytics.current_metrics**: Current-state serving table keyed by `sku + warehouse_id`
- **analytics.metric_history**: Idempotent history table keyed by `batch_key + sku + warehouse_id`
- **analytics.pipeline_runs**: Run manifests and processing counts
- **analytics.data_quality_runs**: Per-run data quality reports
- **analytics.processed_event_log**: Event-level dedupe log
- **analytics.invalid_inventory_events**: Invalid-event sink with raw payloads and errors

### Redis
- **metrics:{sku}:{warehouse_id}**: Cached metrics
- Stores: velocity, stockout risk, last updated timestamp
- TTL: 1 hour

### Parquet Files
- **run_date=YYYY-MM-DD/run_id=<uuid>/processed_metrics.parquet**: Partitioned run output
- **run_date=YYYY-MM-DD/run_id=<uuid>/manifest.json**: Run manifest with counts and DQ status

### Kafka Topics
- **inventory-alerts**: High stockout risk alerts
- Publishes: Stockout risk alerts with recommended reorder quantities
- **inventory-events-dlq**: Invalid-event sink for schema violations

## Tests

```bash
bash ./scripts/run-data-pipeline-tests.sh
```

These behavioral tests cover:

- Java `LocalDateTime` array timestamps from the inventory service
- default idempotency in `analytics.processed_event_log`
- explicit `--force-reprocess` behavior
- Parquet + manifest generation
- a passing DQ run against matching source transactions

## Notes

- This service uses **basic statistical calculations**, not machine learning
- Analytics are calculated using simple heuristics based on historical data
- Stockout risk is calculated using basic statistical methods, not ML models
- The service is designed for demonstration and learning purposes
