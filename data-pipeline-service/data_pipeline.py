"""
ETL pipeline for inventory analytics.

Supported modes:
- stream: consume Kafka inventory events continuously
- backfill: rebuild metrics from inventory_transactions for a date range
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import psycopg2
import pyarrow as pa
import pyarrow.parquet as pq
import redis
from kafka import KafkaConsumer, KafkaProducer
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from psycopg2.extras import Json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ALLOWED_EVENT_TYPES = {
    "INVENTORY_UPDATED",
    "LOW_STOCK",
    "OUT_OF_STOCK",
    "RESTOCKED",
    "RESERVED",
    "RELEASED",
    "ADJUSTED",
}

BATCHES_PROCESSED = Counter(
    "pipeline_batches_processed_total",
    "Number of ETL batches successfully processed",
)
EVENTS_CONSUMED = Counter(
    "pipeline_events_consumed_total",
    "Number of raw inventory events read by the pipeline",
)
EVENTS_DUPLICATE = Counter(
    "pipeline_events_duplicate_total",
    "Number of duplicate inventory events skipped by idempotency checks",
)
EVENTS_INVALID = Counter(
    "pipeline_events_invalid_total",
    "Number of invalid inventory events routed to the invalid-event sink",
)
EVENTS_BACKFILLED = Counter(
    "pipeline_events_backfilled_total",
    "Number of events loaded in backfill mode",
)
RUN_FAILURES = Counter(
    "pipeline_run_failures_total",
    "Number of ETL runs that ended in failure",
)
PROCESSING_DURATION = Histogram(
    "pipeline_batch_processing_seconds",
    "Wall-clock duration of successful ETL batches",
)
LAST_SUCCESSFUL_RUN = Gauge(
    "pipeline_last_success_timestamp",
    "Unix timestamp of the latest successful ETL batch",
)
LAST_BATCH_SIZE = Gauge(
    "pipeline_last_batch_size",
    "Number of valid, non-duplicate events processed in the latest batch",
)
LAST_DQ_STATUS = Gauge(
    "pipeline_last_dq_pass",
    "1 when the latest DQ run passed and 0 when it failed",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None

    if isinstance(value, (list, tuple)):
        if len(value) < 6:
            raise ValueError("timestamp array must include at least year-month-day-hour-minute-second")
        year, month, day, hour, minute, second, *rest = value
        microsecond = 0
        if rest:
            microsecond = int(rest[0]) // 1000
        return datetime(
            int(year),
            int(month),
            int(day),
            int(hour),
            int(minute),
            int(second),
            microsecond,
        )

    if isinstance(value, datetime):
        parsed = value
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def event_payload_hash(raw_payload: Dict[str, Any]) -> str:
    payload = json.dumps(raw_payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class InventoryEvent:
    event_id: str
    sku: str
    warehouse_id: str
    quantity_change: int
    timestamp: datetime
    event_type: str
    reference_id: str
    raw_payload: Dict[str, Any]
    payload_hash: str


@dataclass
class InvalidEventRecord:
    event_id: str
    errors: List[str]
    raw_payload: Dict[str, Any]


@dataclass
class ProcessedMetrics:
    sku: str
    warehouse_id: str
    velocity_7d: float
    velocity_30d: float
    volatility: float
    trend: float
    seasonality_index: float
    stockout_risk: float
    reorder_recommendation: int
    source_event_count: int
    last_event_timestamp: datetime


@dataclass
class PipelineRunContext:
    run_id: str
    batch_key: str
    mode: str
    source: str
    force_reprocess: bool
    started_at: datetime
    replay_window_start: Optional[datetime]
    replay_window_end: Optional[datetime]


class InventoryETLPipeline:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.mode = args.mode
        self.run_once = args.run_once
        self.force_reprocess = args.force_reprocess
        self.batch_size = args.batch_size
        self.reconciliation_tolerance = float(
            os.getenv("RECONCILIATION_TOLERANCE", "0.01")
        )
        self.freshness_threshold_seconds = int(
            os.getenv("PIPELINE_FRESHNESS_THRESHOLD_SECONDS", "900")
        )
        self.metrics_port = int(os.getenv("PIPELINE_METRICS_PORT", "8001"))
        self.data_dir = Path(os.getenv("DATA_DIR", "./data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)

        kafka_bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092").split(",")
        self.consumer = None
        if self.mode == "stream":
            self.consumer = KafkaConsumer(
                "inventory-events",
                bootstrap_servers=kafka_bootstrap,
                auto_offset_reset=os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                group_id=os.getenv("KAFKA_CONSUMER_GROUP", "etl-pipeline-group"),
            )

        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        self.pg_conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            database=os.getenv("POSTGRES_DB", "inventory"),
            user=os.getenv("POSTGRES_USER", "inventory_user"),
            password=os.getenv("POSTGRES_PASSWORD", "inventory_pass"),
            port=os.getenv("POSTGRES_PORT", "5432"),
        )

        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD", "")
        redis_kwargs: Dict[str, Any] = {
            "host": redis_host,
            "port": redis_port,
            "decode_responses": True,
        }
        if redis_password:
            redis_kwargs["password"] = redis_password
        self.redis_client = redis.Redis(**redis_kwargs)

        start_http_server(self.metrics_port)
        logger.info("Pipeline metrics endpoint started on port %s", self.metrics_port)

        self.event_buffer: List[Dict[str, Any]] = []
        self._ensure_analytics_schema()

    async def run(self):
        logger.info("Starting ETL pipeline in %s mode", self.mode)

        try:
            if self.mode == "backfill":
                await self._run_backfill()
            else:
                await self._run_stream()
        except KeyboardInterrupt:
            logger.info("Shutting down ETL pipeline...")
        finally:
            if self.event_buffer:
                await self._process_batch(self.event_buffer, source=self.mode)
            self._cleanup()

    async def _run_stream(self):
        assert self.consumer is not None

        while True:
            message_batch = self.consumer.poll(timeout_ms=1000, max_records=self.batch_size)

            if not message_batch:
                if self.event_buffer:
                    await self._process_batch(self.event_buffer, source="kafka")
                    self.event_buffer = []
                    if self.run_once:
                        return
                elif self.run_once:
                    logger.info("Run-once mode finished without new Kafka events")
                    return
                continue

            for _, messages in message_batch.items():
                for message in messages:
                    EVENTS_CONSUMED.inc()
                    self.event_buffer.append(message.value)
                    if len(self.event_buffer) >= self.batch_size:
                        await self._process_batch(self.event_buffer, source="kafka")
                        self.event_buffer = []
                        if self.run_once:
                            return

    async def _run_backfill(self):
        if not self.args.backfill_start or not self.args.backfill_end:
            raise ValueError("Backfill mode requires --backfill-start and --backfill-end")

        replay_window = (
            parse_datetime(self.args.backfill_start),
            parse_datetime(self.args.backfill_end),
        )
        if replay_window[0] is None or replay_window[1] is None:
            raise ValueError("Backfill window must use ISO-8601 timestamps")
        if replay_window[0] >= replay_window[1]:
            raise ValueError("Backfill start must be earlier than backfill end")

        raw_events = self._fetch_backfill_events(replay_window[0], replay_window[1])
        EVENTS_BACKFILLED.inc(len(raw_events))
        logger.info(
            "Loaded %s events for backfill window %s -> %s",
            len(raw_events),
            replay_window[0].isoformat(),
            replay_window[1].isoformat(),
        )

        if not raw_events:
            logger.info("Backfill produced no events")
            return

        for index in range(0, len(raw_events), self.batch_size):
            await self._process_batch(
                raw_events[index : index + self.batch_size],
                source="backfill",
                replay_window=replay_window,
            )

    def _fetch_backfill_events(
        self,
        start_at: datetime,
        end_at: datetime,
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT
                id,
                sku,
                warehouse_id,
                quantity_change,
                transaction_type,
                timestamp,
                COALESCE(reference_id, CONCAT('txn-', id::text)) AS reference_id
            FROM inventory_transactions
            WHERE timestamp >= %s
              AND timestamp < %s
            ORDER BY timestamp, id
        """

        with self.pg_conn.cursor() as cur:
            cur.execute(query, (start_at, end_at))
            rows = cur.fetchall()

        events: List[Dict[str, Any]] = []
        for row in rows:
            transaction_id, sku, warehouse_id, quantity_change, transaction_type, timestamp, reference_id = row
            events.append(
                {
                    "eventId": f"backfill-{transaction_id}",
                    "sku": sku,
                    "warehouseId": warehouse_id,
                    "quantityChange": quantity_change,
                    "eventType": self._map_transaction_type(transaction_type, quantity_change),
                    "timestamp": timestamp.isoformat(),
                    "referenceId": reference_id,
                }
            )
        return events

    async def _process_batch(
        self,
        raw_events: Sequence[Dict[str, Any]],
        source: str,
        replay_window: Optional[Tuple[datetime, datetime]] = None,
    ):
        batch_received_at = utc_now()
        valid_events, invalid_events = self._validate_events(raw_events)
        batch_key = self._build_batch_key(valid_events, raw_events)
        run_ctx = self._start_pipeline_run(
            batch_key=batch_key,
            source=source,
            source_event_count=len(raw_events),
            mode=self.mode,
            replay_window=replay_window,
        )

        if invalid_events:
            self._record_invalid_events(run_ctx.run_id, batch_key, invalid_events)

        duplicate_count = 0
        accepted_events: List[InventoryEvent] = []
        if valid_events:
            accepted_events, duplicate_count = self._register_events(run_ctx.run_id, valid_events)
            if duplicate_count:
                EVENTS_DUPLICATE.inc(duplicate_count)

        if invalid_events:
            EVENTS_INVALID.inc(len(invalid_events))

        if not accepted_events:
            manifest_path = self._write_run_manifest(
                run_ctx=run_ctx,
                metrics=[],
                valid_event_count=len(valid_events),
                duplicate_count=duplicate_count,
                invalid_event_count=len(invalid_events),
                parquet_path=None,
                dq_report=self._skipped_report(len(invalid_events), duplicate_count),
                status="SKIPPED",
            )
            self._complete_pipeline_run(
                run_id=run_ctx.run_id,
                status="SKIPPED",
                valid_event_count=len(valid_events),
                duplicate_count=duplicate_count,
                invalid_event_count=len(invalid_events),
                processed_metric_count=0,
                parquet_path=None,
                manifest_path=manifest_path,
                dq_report=self._skipped_report(len(invalid_events), duplicate_count),
            )
            return

        LAST_BATCH_SIZE.set(len(accepted_events))

        try:
            with PROCESSING_DURATION.time():
                df = self._events_to_dataframe(accepted_events)
                features_df = await self._engineer_features(df)
                metrics = self._calculate_metrics(features_df)
                parquet_path = self._load_results(run_ctx, metrics)
                self._publish_processed_events(metrics)
                dq_report = self._run_data_quality_checks(run_ctx.run_id, metrics, len(invalid_events))

            manifest_path = self._write_run_manifest(
                run_ctx=run_ctx,
                metrics=metrics,
                valid_event_count=len(valid_events),
                duplicate_count=duplicate_count,
                invalid_event_count=len(invalid_events),
                parquet_path=parquet_path,
                dq_report=dq_report,
                status="SUCCESS",
            )

            self._complete_pipeline_run(
                run_id=run_ctx.run_id,
                status="SUCCESS",
                valid_event_count=len(valid_events),
                duplicate_count=duplicate_count,
                invalid_event_count=len(invalid_events),
                processed_metric_count=len(metrics),
                parquet_path=parquet_path,
                manifest_path=manifest_path,
                dq_report=dq_report,
            )

            BATCHES_PROCESSED.inc()
            LAST_SUCCESSFUL_RUN.set(batch_received_at.timestamp())
            LAST_DQ_STATUS.set(1 if dq_report["summary"]["status"] == "PASS" else 0)
        except Exception as exc:
            RUN_FAILURES.inc()
            logger.error("Error processing batch %s: %s", run_ctx.run_id, exc, exc_info=True)
            self.pg_conn.rollback()
            self._complete_pipeline_run(
                run_id=run_ctx.run_id,
                status="FAILED",
                valid_event_count=len(valid_events),
                duplicate_count=duplicate_count,
                invalid_event_count=len(invalid_events),
                processed_metric_count=0,
                parquet_path=None,
                manifest_path=None,
                dq_report={
                    "summary": {
                        "status": "FAIL",
                        "reason": "batch_failed",
                    }
                },
                error_message=str(exc),
            )
            raise

    def _validate_events(
        self,
        raw_events: Sequence[Dict[str, Any]],
    ) -> Tuple[List[InventoryEvent], List[InvalidEventRecord]]:
        valid_events: List[InventoryEvent] = []
        invalid_events: List[InvalidEventRecord] = []

        for raw_event in raw_events:
            normalized = dict(raw_event)
            payload_hash = event_payload_hash(normalized)
            warehouse_id = (
                normalized.get("warehouse")
                or normalized.get("warehouseId")
                or normalized.get("warehouse_id")
                or ""
            )
            raw_event_id = (
                normalized.get("eventId")
                or normalized.get("event_id")
                or normalized.get("referenceId")
                or normalized.get("reference_id")
                or ""
            )
            event_id = str(raw_event_id).strip() or self._fallback_event_id(normalized, payload_hash)

            errors: List[str] = []
            sku = str(normalized.get("sku", "")).strip()
            if not sku:
                errors.append("sku is required")

            warehouse_id = str(warehouse_id).strip()
            if not warehouse_id:
                errors.append("warehouse_id is required")

            event_type = str(
                normalized.get("eventType") or normalized.get("event_type") or ""
            ).strip()
            if event_type not in ALLOWED_EVENT_TYPES:
                errors.append(f"event_type must be one of {sorted(ALLOWED_EVENT_TYPES)}")

            quantity_change_raw = normalized.get("quantityChange", normalized.get("quantity_change"))
            try:
                quantity_change = int(quantity_change_raw)
            except (TypeError, ValueError):
                quantity_change = 0
                errors.append("quantity_change must be an integer")

            if quantity_change == 0:
                errors.append("quantity_change must be non-zero")

            timestamp_raw = normalized.get("timestamp") or utc_now().isoformat()
            try:
                timestamp = parse_datetime(timestamp_raw)
            except ValueError:
                timestamp = None
            if timestamp is None:
                errors.append("timestamp must be ISO-8601 parseable")
                timestamp = utc_now()

            reference_id = str(
                normalized.get("referenceId")
                or normalized.get("reference_id")
                or event_id
            ).strip()

            if errors:
                invalid_events.append(
                    InvalidEventRecord(
                        event_id=event_id,
                        errors=errors,
                        raw_payload=normalized,
                    )
                )
                continue

            valid_events.append(
                InventoryEvent(
                    event_id=event_id,
                    sku=sku,
                    warehouse_id=warehouse_id,
                    quantity_change=quantity_change,
                    timestamp=timestamp,
                    event_type=event_type,
                    reference_id=reference_id,
                    raw_payload=normalized,
                    payload_hash=payload_hash,
                )
            )

        return valid_events, invalid_events

    def _fallback_event_id(self, raw_event: Dict[str, Any], payload_hash: str) -> str:
        seed = "|".join(
            [
                str(raw_event.get("sku", "")),
                str(raw_event.get("warehouse") or raw_event.get("warehouseId") or raw_event.get("warehouse_id") or ""),
                str(raw_event.get("quantityChange", raw_event.get("quantity_change", ""))),
                str(raw_event.get("eventType", raw_event.get("event_type", ""))),
                str(raw_event.get("timestamp", "")),
                str(raw_event.get("referenceId", raw_event.get("reference_id", ""))),
                payload_hash,
            ]
        )
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    def _build_batch_key(
        self,
        valid_events: Sequence[InventoryEvent],
        raw_events: Sequence[Dict[str, Any]],
    ) -> str:
        if valid_events:
            ids = sorted(event.event_id for event in valid_events)
            seed = "|".join(ids)
        else:
            seed = "|".join(sorted(event_payload_hash(dict(raw_event)) for raw_event in raw_events))
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    def _start_pipeline_run(
        self,
        batch_key: str,
        source: str,
        source_event_count: int,
        mode: str,
        replay_window: Optional[Tuple[datetime, datetime]],
    ) -> PipelineRunContext:
        run_id = str(uuid.uuid4())
        replay_start = replay_window[0] if replay_window else None
        replay_end = replay_window[1] if replay_window else None
        started_at = utc_now()

        insert_sql = """
            INSERT INTO analytics.pipeline_runs (
                run_id,
                batch_key,
                mode,
                source,
                status,
                started_at,
                replay_window_start,
                replay_window_end,
                source_event_count,
                force_reprocess,
                valid_event_count,
                duplicate_event_count,
                invalid_event_count,
                processed_metric_count
            )
            VALUES (%s, %s, %s, %s, 'RUNNING', %s, %s, %s, %s, %s, 0, 0, 0, 0)
        """

        with self.pg_conn.cursor() as cur:
            cur.execute(
                insert_sql,
                (
                    run_id,
                    batch_key,
                    mode,
                    source,
                    started_at,
                    replay_start,
                    replay_end,
                    source_event_count,
                    self.force_reprocess,
                ),
            )
        self.pg_conn.commit()

        return PipelineRunContext(
            run_id=run_id,
            batch_key=batch_key,
            mode=mode,
            source=source,
            force_reprocess=self.force_reprocess,
            started_at=started_at,
            replay_window_start=replay_start,
            replay_window_end=replay_end,
        )

    def _record_invalid_events(
        self,
        run_id: str,
        batch_key: str,
        invalid_events: Sequence[InvalidEventRecord],
    ):
        insert_sql = """
            INSERT INTO analytics.invalid_inventory_events (
                run_id,
                batch_key,
                event_id,
                validation_errors,
                raw_payload
            )
            VALUES (%s, %s, %s, %s, %s)
        """

        with self.pg_conn.cursor() as cur:
            for record in invalid_events:
                cur.execute(
                    insert_sql,
                    (
                        run_id,
                        batch_key,
                        record.event_id,
                        "; ".join(record.errors),
                        Json(record.raw_payload),
                    ),
                )
        self.pg_conn.commit()

        for record in invalid_events:
            self._publish_invalid_event(record)

    def _publish_invalid_event(self, record: InvalidEventRecord):
        try:
            self.producer.send(
                "inventory-events-dlq",
                {
                    "event_id": record.event_id,
                    "validation_errors": record.errors,
                    "raw_payload": record.raw_payload,
                    "recorded_at": utc_now().isoformat(),
                },
            )
        except Exception as exc:
            logger.warning("Failed to publish invalid event %s to DLQ: %s", record.event_id, exc)

    def _register_events(
        self,
        run_id: str,
        events: Sequence[InventoryEvent],
    ) -> Tuple[List[InventoryEvent], int]:
        if self.force_reprocess:
            insert_sql = """
                INSERT INTO analytics.processed_event_log (
                    event_id,
                    sku,
                    warehouse_id,
                    event_type,
                    quantity_change,
                    source_timestamp,
                    reference_id,
                    payload_hash,
                    last_run_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO UPDATE
                SET
                    sku = EXCLUDED.sku,
                    warehouse_id = EXCLUDED.warehouse_id,
                    event_type = EXCLUDED.event_type,
                    quantity_change = EXCLUDED.quantity_change,
                    source_timestamp = EXCLUDED.source_timestamp,
                    reference_id = EXCLUDED.reference_id,
                    payload_hash = EXCLUDED.payload_hash,
                    last_run_id = EXCLUDED.last_run_id
                RETURNING event_id
            """
        else:
            insert_sql = """
                INSERT INTO analytics.processed_event_log (
                    event_id,
                    sku,
                    warehouse_id,
                    event_type,
                    quantity_change,
                    source_timestamp,
                    reference_id,
                    payload_hash,
                    last_run_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
                RETURNING event_id
            """

        accepted_events: List[InventoryEvent] = []
        duplicate_count = 0

        with self.pg_conn.cursor() as cur:
            for event in events:
                cur.execute(
                    insert_sql,
                    (
                        event.event_id,
                        event.sku,
                        event.warehouse_id,
                        event.event_type,
                        event.quantity_change,
                        event.timestamp,
                        event.reference_id,
                        event.payload_hash,
                        run_id,
                    ),
                )
                inserted = cur.fetchone()
                if inserted:
                    accepted_events.append(event)
                elif not self.force_reprocess:
                    duplicate_count += 1
        self.pg_conn.commit()

        return accepted_events, duplicate_count

    def _events_to_dataframe(self, events: Sequence[InventoryEvent]) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "event_id": event.event_id,
                    "sku": event.sku,
                    "warehouse_id": event.warehouse_id,
                    "quantity_change": event.quantity_change,
                    "timestamp": event.timestamp,
                    "event_type": event.event_type,
                    "reference_id": event.reference_id,
                    "hour": event.timestamp.hour,
                    "day_of_week": event.timestamp.weekday(),
                    "is_weekend": event.timestamp.weekday() >= 5,
                }
                for event in events
            ]
        )

    async def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = df.copy()
        features["velocity_7d"] = 0.0
        features["velocity_30d"] = 0.0
        features["volatility"] = 0.0
        features["trend"] = 0.0
        features["seasonality_index"] = 1.0

        grouped = df.groupby(["sku", "warehouse_id"])
        for (sku, warehouse_id), group_df in grouped:
            try:
                hist_data = await self._get_historical_data(sku, warehouse_id)

                if not hist_data.empty:
                    velocity_7d = self._calculate_velocity(hist_data, days=7)
                    velocity_30d = self._calculate_velocity(hist_data, days=30)
                    volatility = self._calculate_volatility(hist_data)
                    trend = self._calculate_trend(hist_data)
                    seasonality = self._calculate_seasonality(hist_data)

                    mask = (features["sku"] == sku) & (features["warehouse_id"] == warehouse_id)
                    features.loc[mask, "velocity_7d"] = velocity_7d
                    features.loc[mask, "velocity_30d"] = velocity_30d
                    features.loc[mask, "volatility"] = volatility
                    features.loc[mask, "trend"] = trend
                    features.loc[mask, "seasonality_index"] = seasonality
            except Exception as exc:
                logger.error(
                    "Error engineering features for %s:%s: %s",
                    sku,
                    warehouse_id,
                    exc,
                )

        return features.fillna(0)

    async def _get_historical_data(self, sku: str, warehouse_id: str) -> pd.DataFrame:
        query = """
            SELECT
                date_trunc('day', timestamp) AS date,
                SUM(CASE WHEN transaction_type = 'SALE' THEN ABS(quantity_change) ELSE 0 END) AS daily_sales,
                COUNT(*) AS transaction_count
            FROM inventory_transactions
            WHERE sku = %s
              AND warehouse_id = %s
              AND timestamp >= NOW() - INTERVAL '90 days'
            GROUP BY date
            ORDER BY date
        """

        with self.pg_conn.cursor() as cur:
            cur.execute(query, (sku, warehouse_id))
            rows = cur.fetchall()
            columns = [description[0] for description in cur.description]

        if not rows:
            return pd.DataFrame()

        hist_data = pd.DataFrame(rows, columns=columns)
        hist_data["date"] = pd.to_datetime(hist_data["date"])
        hist_data["daily_sales"] = hist_data["daily_sales"].fillna(0.0)
        return hist_data

    def _calculate_velocity(self, hist_data: pd.DataFrame, days: int) -> float:
        if hist_data.empty:
            return 0.0

        latest_date = hist_data["date"].max()
        window_start = latest_date - pd.Timedelta(days=days - 1)
        recent_data = hist_data[hist_data["date"] >= window_start]
        total_sales = float(recent_data["daily_sales"].sum())
        return total_sales / float(days)

    def _calculate_volatility(self, hist_data: pd.DataFrame) -> float:
        if len(hist_data) > 1:
            return float(hist_data["daily_sales"].std(ddof=0))
        return 0.0

    def _calculate_trend(self, hist_data: pd.DataFrame) -> float:
        if len(hist_data) > 7:
            x = np.arange(len(hist_data))
            y = hist_data["daily_sales"].values
            slope, _ = np.polyfit(x, y, 1)
            return float(slope)
        return 0.0

    def _calculate_seasonality(self, hist_data: pd.DataFrame) -> float:
        if len(hist_data) > 30:
            recent_avg = hist_data.tail(7)["daily_sales"].mean()
            monthly_avg = hist_data.tail(30)["daily_sales"].mean()
            if monthly_avg > 0:
                return float(recent_avg / monthly_avg)
        return 1.0

    def _calculate_stockout_risk_basic(
        self,
        velocity_30d: float,
        volatility: float,
        trend: float,
        seasonality: float,
    ) -> float:
        risk = 0.0

        if velocity_30d > 50:
            risk += 0.3
        if volatility > velocity_30d * 0.5:
            risk += 0.2
        if trend < 0:
            risk += 0.2
        if seasonality > 1.5:
            risk += 0.3

        return min(risk, 1.0)

    def _calculate_metrics(self, features_df: pd.DataFrame) -> List[ProcessedMetrics]:
        if features_df.empty:
            return []

        metrics: List[ProcessedMetrics] = []
        grouped = features_df.groupby(["sku", "warehouse_id"], as_index=False)

        for _, group_df in grouped:
            row = group_df.iloc[-1]
            velocity_30d = float(row.get("velocity_30d", 0.0))
            volatility = float(row.get("volatility", 0.0))
            trend = float(row.get("trend", 0.0))
            seasonality = float(row.get("seasonality_index", 1.0))
            stockout_risk = self._calculate_stockout_risk_basic(
                velocity_30d=velocity_30d,
                volatility=volatility,
                trend=trend,
                seasonality=seasonality,
            )

            metrics.append(
                ProcessedMetrics(
                    sku=row["sku"],
                    warehouse_id=row["warehouse_id"],
                    velocity_7d=float(row.get("velocity_7d", 0.0)),
                    velocity_30d=velocity_30d,
                    volatility=volatility,
                    trend=trend,
                    seasonality_index=seasonality,
                    stockout_risk=stockout_risk,
                    reorder_recommendation=self._calculate_reorder_quantity(
                        velocity_30d,
                        volatility,
                        stockout_risk,
                    ),
                    source_event_count=len(group_df),
                    last_event_timestamp=pd.Timestamp(group_df["timestamp"].max()).to_pydatetime(),
                )
            )

        return metrics

    def _calculate_reorder_quantity(self, velocity: float, volatility: float, risk: float) -> int:
        lead_time = 7
        safety_factor = 1.5 + risk
        safety_stock = volatility * np.sqrt(lead_time) * safety_factor
        reorder_qty = (velocity * lead_time) + safety_stock
        return max(int(reorder_qty), 0)

    def _load_results(self, run_ctx: PipelineRunContext, metrics: Sequence[ProcessedMetrics]) -> Optional[str]:
        if not metrics:
            return None

        history_sql = """
            INSERT INTO analytics.metric_history (
                batch_key,
                run_id,
                sku,
                warehouse_id,
                velocity_7d,
                velocity_30d,
                volatility,
                trend,
                seasonality_index,
                stockout_risk,
                reorder_recommendation,
                source_event_count,
                last_event_timestamp,
                processed_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (batch_key, sku, warehouse_id) DO UPDATE
            SET
                run_id = EXCLUDED.run_id,
                velocity_7d = EXCLUDED.velocity_7d,
                velocity_30d = EXCLUDED.velocity_30d,
                volatility = EXCLUDED.volatility,
                trend = EXCLUDED.trend,
                seasonality_index = EXCLUDED.seasonality_index,
                stockout_risk = EXCLUDED.stockout_risk,
                reorder_recommendation = EXCLUDED.reorder_recommendation,
                source_event_count = EXCLUDED.source_event_count,
                last_event_timestamp = EXCLUDED.last_event_timestamp,
                processed_at = EXCLUDED.processed_at
        """

        current_sql = """
            INSERT INTO analytics.current_metrics (
                sku,
                warehouse_id,
                velocity_7d,
                velocity_30d,
                volatility,
                trend,
                seasonality_index,
                stockout_risk,
                reorder_recommendation,
                source_event_count,
                last_event_timestamp,
                last_run_id,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (sku, warehouse_id) DO UPDATE
            SET
                velocity_7d = EXCLUDED.velocity_7d,
                velocity_30d = EXCLUDED.velocity_30d,
                volatility = EXCLUDED.volatility,
                trend = EXCLUDED.trend,
                seasonality_index = EXCLUDED.seasonality_index,
                stockout_risk = EXCLUDED.stockout_risk,
                reorder_recommendation = EXCLUDED.reorder_recommendation,
                source_event_count = EXCLUDED.source_event_count,
                last_event_timestamp = EXCLUDED.last_event_timestamp,
                last_run_id = EXCLUDED.last_run_id,
                updated_at = EXCLUDED.updated_at
        """

        with self.pg_conn.cursor() as cur:
            for metric in metrics:
                cur.execute(
                    history_sql,
                    (
                        run_ctx.batch_key,
                        run_ctx.run_id,
                        metric.sku,
                        metric.warehouse_id,
                        metric.velocity_7d,
                        metric.velocity_30d,
                        metric.volatility,
                        metric.trend,
                        metric.seasonality_index,
                        metric.stockout_risk,
                        metric.reorder_recommendation,
                        metric.source_event_count,
                        metric.last_event_timestamp,
                    ),
                )
                cur.execute(
                    current_sql,
                    (
                        metric.sku,
                        metric.warehouse_id,
                        metric.velocity_7d,
                        metric.velocity_30d,
                        metric.volatility,
                        metric.trend,
                        metric.seasonality_index,
                        metric.stockout_risk,
                        metric.reorder_recommendation,
                        metric.source_event_count,
                        metric.last_event_timestamp,
                        run_ctx.run_id,
                    ),
                )
        self.pg_conn.commit()

        for metric in metrics:
            try:
                self.redis_client.hset(
                    f"metrics:{metric.sku}:{metric.warehouse_id}",
                    mapping={
                        "velocity_7d": str(metric.velocity_7d),
                        "velocity_30d": str(metric.velocity_30d),
                        "stockout_risk": str(metric.stockout_risk),
                        "last_updated": utc_now().isoformat(),
                        "last_run_id": run_ctx.run_id,
                    },
                )
                self.redis_client.expire(f"metrics:{metric.sku}:{metric.warehouse_id}", 3600)
            except Exception as exc:
                logger.warning(
                    "Error updating Redis cache for %s:%s: %s",
                    metric.sku,
                    metric.warehouse_id,
                    exc,
                )

        return self._write_parquet(run_ctx, metrics)

    def _write_parquet(
        self,
        run_ctx: PipelineRunContext,
        metrics: Sequence[ProcessedMetrics],
    ) -> str:
        run_date = run_ctx.started_at.strftime("%Y-%m-%d")
        run_dir = self.data_dir / f"run_date={run_date}" / f"run_id={run_ctx.run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)

        records = []
        for metric in metrics:
            record = asdict(metric)
            record["run_id"] = run_ctx.run_id
            record["batch_key"] = run_ctx.batch_key
            record["processed_at"] = utc_now().isoformat()
            record["last_event_timestamp"] = metric.last_event_timestamp.isoformat()
            records.append(record)

        table = pa.Table.from_pandas(pd.DataFrame(records))
        output_path = run_dir / "processed_metrics.parquet"
        pq.write_table(table, output_path)
        logger.info("Wrote metrics parquet to %s", output_path)
        return str(output_path)

    def _run_data_quality_checks(
        self,
        run_id: str,
        metrics: Sequence[ProcessedMetrics],
        invalid_event_count: int,
    ) -> Dict[str, Any]:
        with self.pg_conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM analytics.current_metrics
                WHERE sku IS NULL OR sku = '' OR warehouse_id IS NULL OR warehouse_id = ''
                """
            )
            null_key_count = int(cur.fetchone()[0])

            cur.execute(
                """
                SELECT COUNT(*)
                FROM analytics.current_metrics
                WHERE velocity_7d < 0
                   OR velocity_30d < 0
                   OR stockout_risk < 0
                   OR stockout_risk > 1
                """
            )
            range_violations = int(cur.fetchone()[0])

            cur.execute(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT sku, warehouse_id, COUNT(*) AS key_count
                    FROM analytics.current_metrics
                    GROUP BY sku, warehouse_id
                    HAVING COUNT(*) > 1
                ) duplicate_keys
                """
            )
            duplicate_keys = int(cur.fetchone()[0])

            cur.execute(
                """
                SELECT COALESCE(EXTRACT(EPOCH FROM (NOW() - MAX(updated_at))), 0)
                FROM analytics.current_metrics
                """
            )
            freshness_seconds = float(cur.fetchone()[0] or 0.0)

        reconciliation_failures: List[Dict[str, Any]] = []
        with self.pg_conn.cursor() as cur:
            for metric in metrics:
                cur.execute(
                    """
                    SELECT COALESCE(SUM(ABS(quantity_change)) / 30.0, 0)
                    FROM inventory_transactions
                    WHERE sku = %s
                      AND warehouse_id = %s
                      AND transaction_type = 'SALE'
                      AND timestamp >= NOW() - INTERVAL '30 days'
                    """,
                    (metric.sku, metric.warehouse_id),
                )
                expected_velocity_30d = float(cur.fetchone()[0] or 0.0)
                difference = abs(expected_velocity_30d - metric.velocity_30d)
                if difference > self.reconciliation_tolerance:
                    reconciliation_failures.append(
                        {
                            "sku": metric.sku,
                            "warehouse_id": metric.warehouse_id,
                            "expected_velocity_30d": round(expected_velocity_30d, 4),
                            "actual_velocity_30d": round(metric.velocity_30d, 4),
                            "difference": round(difference, 4),
                        }
                    )

        checks = {
            "freshness": {
                "status": "PASS"
                if freshness_seconds <= self.freshness_threshold_seconds
                else "FAIL",
                "freshness_seconds": round(freshness_seconds, 2),
                "threshold_seconds": self.freshness_threshold_seconds,
            },
            "null_keys": {
                "status": "PASS" if null_key_count == 0 else "FAIL",
                "violations": null_key_count,
            },
            "unique_current_metrics": {
                "status": "PASS" if duplicate_keys == 0 else "FAIL",
                "duplicate_key_groups": duplicate_keys,
            },
            "metric_ranges": {
                "status": "PASS" if range_violations == 0 else "FAIL",
                "violations": range_violations,
            },
            "reconciliation": {
                "status": "PASS" if not reconciliation_failures else "FAIL",
                "violations": len(reconciliation_failures),
                "examples": reconciliation_failures[:5],
            },
            "invalid_events": {
                "status": "PASS" if invalid_event_count == 0 else "FAIL",
                "violations": invalid_event_count,
            },
        }

        status = "PASS" if all(check["status"] == "PASS" for check in checks.values()) else "FAIL"
        report = {
            "run_id": run_id,
            "checked_at": utc_now().isoformat(),
            "checks": checks,
            "summary": {
                "status": status,
                "total_checks": len(checks),
                "failed_checks": sum(1 for check in checks.values() if check["status"] == "FAIL"),
            },
        }

        with self.pg_conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO analytics.data_quality_runs (run_id, status, report, checked_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (run_id) DO UPDATE
                SET status = EXCLUDED.status,
                    report = EXCLUDED.report,
                    checked_at = EXCLUDED.checked_at
                """,
                (run_id, status, Json(report)),
            )
        self.pg_conn.commit()

        return report

    def _skipped_report(self, invalid_event_count: int, duplicate_count: int) -> Dict[str, Any]:
        return {
            "summary": {
                "status": "SKIPPED",
                "invalid_events": invalid_event_count,
                "duplicate_events": duplicate_count,
            }
        }

    def _write_run_manifest(
        self,
        run_ctx: PipelineRunContext,
        metrics: Sequence[ProcessedMetrics],
        valid_event_count: int,
        duplicate_count: int,
        invalid_event_count: int,
        parquet_path: Optional[str],
        dq_report: Dict[str, Any],
        status: str,
    ) -> str:
        run_date = run_ctx.started_at.strftime("%Y-%m-%d")
        run_dir = self.data_dir / f"run_date={run_date}" / f"run_id={run_ctx.run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "run_id": run_ctx.run_id,
            "batch_key": run_ctx.batch_key,
            "mode": run_ctx.mode,
            "source": run_ctx.source,
            "force_reprocess": run_ctx.force_reprocess,
            "status": status,
            "started_at": run_ctx.started_at.isoformat(),
            "replay_window": {
                "start": run_ctx.replay_window_start.isoformat()
                if run_ctx.replay_window_start
                else None,
                "end": run_ctx.replay_window_end.isoformat()
                if run_ctx.replay_window_end
                else None,
            },
            "counts": {
                "valid_events": valid_event_count,
                "duplicate_events": duplicate_count,
                "invalid_events": invalid_event_count,
                "processed_metrics": len(metrics),
            },
            "artifacts": {
                "parquet_path": parquet_path,
            },
            "data_quality": dq_report.get("summary", dq_report),
            "generated_at": utc_now().isoformat(),
        }

        manifest_path = run_dir / "manifest.json"
        with manifest_path.open("w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)

        return str(manifest_path)

    def _complete_pipeline_run(
        self,
        run_id: str,
        status: str,
        valid_event_count: int,
        duplicate_count: int,
        invalid_event_count: int,
        processed_metric_count: int,
        parquet_path: Optional[str],
        manifest_path: Optional[str],
        dq_report: Dict[str, Any],
        error_message: Optional[str] = None,
    ):
        update_sql = """
            UPDATE analytics.pipeline_runs
            SET
                status = %s,
                completed_at = NOW(),
                valid_event_count = %s,
                duplicate_event_count = %s,
                invalid_event_count = %s,
                processed_metric_count = %s,
                parquet_path = %s,
                manifest_path = %s,
                dq_status = %s,
                dq_report = %s,
                error_message = %s
            WHERE run_id = %s
        """

        with self.pg_conn.cursor() as cur:
            cur.execute(
                update_sql,
                (
                    status,
                    valid_event_count,
                    duplicate_count,
                    invalid_event_count,
                    processed_metric_count,
                    parquet_path,
                    manifest_path,
                    dq_report.get("summary", {}).get("status"),
                    Json(dq_report),
                    error_message,
                    run_id,
                ),
            )
        self.pg_conn.commit()

    def _publish_processed_events(self, metrics: Sequence[ProcessedMetrics]):
        for metric in metrics:
            if metric.stockout_risk <= 0.7:
                continue

            try:
                self.producer.send(
                    "inventory-alerts",
                    {
                        "type": "HIGH_STOCKOUT_RISK",
                        "sku": metric.sku,
                        "warehouse_id": metric.warehouse_id,
                        "risk_score": metric.stockout_risk,
                        "recommended_reorder": metric.reorder_recommendation,
                        "velocity_30d": metric.velocity_30d,
                        "volatility": metric.volatility,
                        "timestamp": utc_now().isoformat(),
                    },
                )
            except Exception as exc:
                logger.warning(
                    "Error publishing processed event for %s:%s: %s",
                    metric.sku,
                    metric.warehouse_id,
                    exc,
                )

    def _ensure_analytics_schema(self):
        schema_sql = """
            CREATE SCHEMA IF NOT EXISTS analytics;

            CREATE TABLE IF NOT EXISTS analytics.processed_event_log (
                event_id VARCHAR(128) PRIMARY KEY,
                sku VARCHAR(255) NOT NULL,
                warehouse_id VARCHAR(255) NOT NULL,
                event_type VARCHAR(64) NOT NULL,
                quantity_change INTEGER NOT NULL,
                source_timestamp TIMESTAMP NOT NULL,
                reference_id VARCHAR(255),
                payload_hash VARCHAR(64) NOT NULL,
                first_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_run_id VARCHAR(36)
            );

            CREATE TABLE IF NOT EXISTS analytics.invalid_inventory_events (
                id BIGSERIAL PRIMARY KEY,
                run_id VARCHAR(36) NOT NULL,
                batch_key VARCHAR(64) NOT NULL,
                event_id VARCHAR(128),
                validation_errors TEXT NOT NULL,
                raw_payload JSONB NOT NULL,
                recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS analytics.pipeline_runs (
                run_id VARCHAR(36) PRIMARY KEY,
                batch_key VARCHAR(64) NOT NULL,
                mode VARCHAR(32) NOT NULL,
                source VARCHAR(32) NOT NULL,
                status VARCHAR(16) NOT NULL,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                replay_window_start TIMESTAMP,
                replay_window_end TIMESTAMP,
                source_event_count INTEGER NOT NULL DEFAULT 0,
                force_reprocess BOOLEAN NOT NULL DEFAULT FALSE,
                valid_event_count INTEGER NOT NULL DEFAULT 0,
                duplicate_event_count INTEGER NOT NULL DEFAULT 0,
                invalid_event_count INTEGER NOT NULL DEFAULT 0,
                processed_metric_count INTEGER NOT NULL DEFAULT 0,
                parquet_path TEXT,
                manifest_path TEXT,
                dq_status VARCHAR(16),
                dq_report JSONB,
                error_message TEXT
            );

            ALTER TABLE analytics.pipeline_runs
                ADD COLUMN IF NOT EXISTS force_reprocess BOOLEAN NOT NULL DEFAULT FALSE;

            CREATE TABLE IF NOT EXISTS analytics.metric_history (
                id BIGSERIAL PRIMARY KEY,
                batch_key VARCHAR(64) NOT NULL,
                run_id VARCHAR(36) NOT NULL,
                sku VARCHAR(255) NOT NULL,
                warehouse_id VARCHAR(255) NOT NULL,
                velocity_7d DOUBLE PRECISION NOT NULL DEFAULT 0,
                velocity_30d DOUBLE PRECISION NOT NULL DEFAULT 0,
                volatility DOUBLE PRECISION NOT NULL DEFAULT 0,
                trend DOUBLE PRECISION NOT NULL DEFAULT 0,
                seasonality_index DOUBLE PRECISION NOT NULL DEFAULT 1,
                stockout_risk DOUBLE PRECISION NOT NULL DEFAULT 0,
                reorder_recommendation INTEGER NOT NULL DEFAULT 0,
                source_event_count INTEGER NOT NULL DEFAULT 0,
                last_event_timestamp TIMESTAMP,
                processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_metric_history_batch UNIQUE (batch_key, sku, warehouse_id)
            );

            CREATE TABLE IF NOT EXISTS analytics.current_metrics (
                sku VARCHAR(255) NOT NULL,
                warehouse_id VARCHAR(255) NOT NULL,
                velocity_7d DOUBLE PRECISION NOT NULL DEFAULT 0,
                velocity_30d DOUBLE PRECISION NOT NULL DEFAULT 0,
                volatility DOUBLE PRECISION NOT NULL DEFAULT 0,
                trend DOUBLE PRECISION NOT NULL DEFAULT 0,
                seasonality_index DOUBLE PRECISION NOT NULL DEFAULT 1,
                stockout_risk DOUBLE PRECISION NOT NULL DEFAULT 0,
                reorder_recommendation INTEGER NOT NULL DEFAULT 0,
                source_event_count INTEGER NOT NULL DEFAULT 0,
                last_event_timestamp TIMESTAMP,
                last_run_id VARCHAR(36) NOT NULL,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (sku, warehouse_id)
            );

            CREATE TABLE IF NOT EXISTS analytics.data_quality_runs (
                run_id VARCHAR(36) PRIMARY KEY,
                status VARCHAR(16) NOT NULL,
                report JSONB NOT NULL,
                checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status
                ON analytics.pipeline_runs (status, started_at DESC);
            CREATE INDEX IF NOT EXISTS idx_metric_history_processed_at
                ON analytics.metric_history (processed_at DESC);
            CREATE INDEX IF NOT EXISTS idx_invalid_inventory_events_recorded_at
                ON analytics.invalid_inventory_events (recorded_at DESC);
            CREATE INDEX IF NOT EXISTS idx_current_metrics_updated_at
                ON analytics.current_metrics (updated_at DESC);
        """

        with self.pg_conn.cursor() as cur:
            cur.execute(schema_sql)
        self.pg_conn.commit()

    def _map_transaction_type(self, transaction_type: str, quantity_change: int) -> str:
        mapping = {
            "SALE": "INVENTORY_UPDATED",
            "RESTOCK": "RESTOCKED",
            "RESERVATION": "RESERVED",
            "RELEASE": "RELEASED",
            "ADJUSTMENT": "ADJUSTED",
        }
        normalized = mapping.get(str(transaction_type).upper())
        if normalized:
            return normalized
        return "RESTOCKED" if quantity_change > 0 else "INVENTORY_UPDATED"

    def _cleanup(self):
        try:
            if self.consumer is not None:
                self.consumer.close()
            self.producer.close()
            self.pg_conn.close()
            logger.info("ETL pipeline cleanup complete")
        except Exception as exc:
            logger.error("Error during cleanup: %s", exc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory analytics ETL pipeline")
    parser.add_argument(
        "--mode",
        choices=["stream", "backfill"],
        default=os.getenv("PIPELINE_MODE", "stream"),
        help="Pipeline execution mode",
    )
    parser.add_argument(
        "--backfill-start",
        default=os.getenv("BACKFILL_START"),
        help="Inclusive backfill start timestamp in ISO-8601 format",
    )
    parser.add_argument(
        "--backfill-end",
        default=os.getenv("BACKFILL_END"),
        help="Exclusive backfill end timestamp in ISO-8601 format",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.getenv("BATCH_SIZE", "100")),
        help="Maximum events to process in one ETL batch",
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        default=os.getenv("PIPELINE_RUN_ONCE", "false").lower() == "true",
        help="Exit after the first flushed batch",
    )
    parser.add_argument(
        "--force-reprocess",
        action="store_true",
        default=os.getenv("PIPELINE_FORCE_REPROCESS", "false").lower() == "true",
        help="Recompute metrics even if an event already exists in the processed-event log",
    )
    return parser.parse_args()


if __name__ == "__main__":
    pipeline = InventoryETLPipeline(parse_args())
    asyncio.run(pipeline.run())
