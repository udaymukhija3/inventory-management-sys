import os
from pathlib import Path
import uuid

import psycopg2
import pytest

from data_pipeline import (
    InventoryETLPipeline,
    InventoryEvent,
    PipelineRunContext,
    ProcessedMetrics,
    event_payload_hash,
    utc_now,
)


class DummyProducer:
    def __init__(self):
        self.messages = []

    def send(self, topic, payload):
        self.messages.append((topic, payload))

    def close(self):
        return None


class DummyRedis:
    def __init__(self):
        self.hashes = {}

    def hset(self, key, mapping):
        self.hashes[key] = mapping

    def expire(self, key, ttl):
        return None


@pytest.fixture()
def pg_conn():
    conn = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    yield conn
    conn.close()


@pytest.fixture()
def pipeline(pg_conn, tmp_path):
    pipeline = InventoryETLPipeline.__new__(InventoryETLPipeline)
    pipeline.mode = "test"
    pipeline.run_once = True
    pipeline.force_reprocess = False
    pipeline.batch_size = 10
    pipeline.reconciliation_tolerance = 0.01
    pipeline.freshness_threshold_seconds = 900
    pipeline.metrics_port = 8001
    pipeline.data_dir = tmp_path
    pipeline.pg_conn = pg_conn
    pipeline.producer = DummyProducer()
    pipeline.redis_client = DummyRedis()
    pipeline.consumer = None
    pipeline.event_buffer = []
    pipeline._ensure_analytics_schema()

    with pipeline.pg_conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_transactions (
                id BIGSERIAL PRIMARY KEY,
                sku VARCHAR(255) NOT NULL,
                warehouse_id VARCHAR(255) NOT NULL,
                quantity_change INTEGER NOT NULL,
                transaction_type VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reference_id VARCHAR(255),
                notes TEXT
            );
            TRUNCATE TABLE analytics.data_quality_runs,
                           analytics.current_metrics,
                           analytics.metric_history,
                           analytics.invalid_inventory_events,
                           analytics.processed_event_log,
                           analytics.pipeline_runs
            RESTART IDENTITY;
            TRUNCATE TABLE inventory_transactions RESTART IDENTITY;
            """
        )
    pipeline.pg_conn.commit()
    return pipeline


def make_event(event_id="evt-1"):
    raw_payload = {
        "eventId": event_id,
        "sku": "LAPTOP-001",
        "warehouseId": "WAREHOUSE-001",
        "quantityChange": -1,
        "eventType": "INVENTORY_UPDATED",
        "timestamp": "2026-03-12T11:58:28",
        "referenceId": "txn-1",
    }
    return InventoryEvent(
        event_id=event_id,
        sku="LAPTOP-001",
        warehouse_id="WAREHOUSE-001",
        quantity_change=-1,
        timestamp=utc_now(),
        event_type="INVENTORY_UPDATED",
        reference_id="txn-1",
        raw_payload=raw_payload,
        payload_hash=event_payload_hash(raw_payload),
    )


def test_validate_events_accepts_java_timestamp_arrays(pipeline):
    valid_events, invalid_events = pipeline._validate_events(
        [
            {
                "eventId": "evt-java-time",
                "sku": "LAPTOP-001",
                "warehouse": "WAREHOUSE-001",
                "quantityChange": -1,
                "eventType": "INVENTORY_UPDATED",
                "timestamp": [2026, 3, 12, 11, 58, 28, 649237000],
                "referenceId": "txn-java",
            }
        ]
    )

    assert len(valid_events) == 1
    assert invalid_events == []
    assert valid_events[0].timestamp.isoformat() == "2026-03-12T11:58:28.649237"


def test_register_events_is_idempotent_by_default(pipeline):
    event = make_event()

    accepted_events, duplicate_count = pipeline._register_events("run-1", [event])
    assert [registered.event_id for registered in accepted_events] == ["evt-1"]
    assert duplicate_count == 0

    accepted_events, duplicate_count = pipeline._register_events("run-2", [event])
    assert accepted_events == []
    assert duplicate_count == 1


def test_register_events_supports_force_reprocess(pipeline):
    event = make_event()

    accepted_events, duplicate_count = pipeline._register_events("run-1", [event])
    assert len(accepted_events) == 1
    assert duplicate_count == 0

    pipeline.force_reprocess = True
    accepted_events, duplicate_count = pipeline._register_events("run-force", [event])
    assert [registered.event_id for registered in accepted_events] == ["evt-1"]
    assert duplicate_count == 0

    with pipeline.pg_conn.cursor() as cur:
        cur.execute(
            "SELECT last_run_id FROM analytics.processed_event_log WHERE event_id = %s",
            ("evt-1",),
        )
        row = cur.fetchone()
    assert row[0] == "run-force"


def test_load_results_and_dq_report_pass_for_matching_metrics(pipeline):
    with pipeline.pg_conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO inventory_transactions (sku, warehouse_id, quantity_change, transaction_type, timestamp, reference_id)
            VALUES
                ('LAPTOP-001', 'WAREHOUSE-001', -3, 'SALE', NOW() - INTERVAL '2 days', 'ORDER-1'),
                ('LAPTOP-001', 'WAREHOUSE-001', -1, 'SALE', NOW() - INTERVAL '1 day', 'ORDER-2')
            """
        )
    pipeline.pg_conn.commit()

    run_ctx = PipelineRunContext(
        run_id=str(uuid.uuid4()),
        batch_key="batch-1",
        mode="backfill",
        source="backfill",
        force_reprocess=False,
        started_at=utc_now(),
        replay_window_start=None,
        replay_window_end=None,
    )
    metrics = [
        ProcessedMetrics(
            sku="LAPTOP-001",
            warehouse_id="WAREHOUSE-001",
            velocity_7d=4 / 7,
            velocity_30d=4 / 30,
            volatility=1.0,
            trend=0.0,
            seasonality_index=1.0,
            stockout_risk=0.2,
            reorder_recommendation=2,
            source_event_count=2,
            last_event_timestamp=utc_now(),
        )
    ]

    parquet_path = pipeline._load_results(run_ctx, metrics)
    report = pipeline._run_data_quality_checks(run_ctx.run_id, metrics, 0)
    manifest_path = pipeline._write_run_manifest(
        run_ctx=run_ctx,
        metrics=metrics,
        valid_event_count=2,
        duplicate_count=0,
        invalid_event_count=0,
        parquet_path=parquet_path,
        dq_report=report,
        status="SUCCESS",
    )

    assert Path(parquet_path).exists()
    assert Path(manifest_path).exists()
    assert report["summary"]["status"] == "PASS"
    assert "metrics:LAPTOP-001:WAREHOUSE-001" in pipeline.redis_client.hashes
