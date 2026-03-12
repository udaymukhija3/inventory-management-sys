-- Initialize PostgreSQL database for inventory service
-- Note: Database creation should be done separately, this script assumes the database exists

-- Create sequences for entities (Hibernate will create tables, but sequences need to exist)
CREATE SEQUENCE IF NOT EXISTS products_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE IF NOT EXISTS categories_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE IF NOT EXISTS warehouses_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE IF NOT EXISTS inventory_items_seq START WITH 1 INCREMENT BY 1;

-- Create inventory_items table (if not exists - Hibernate will create, but this ensures it exists)
CREATE TABLE IF NOT EXISTS inventory_items (
    id BIGINT PRIMARY KEY DEFAULT nextval('inventory_items_seq'),
    sku VARCHAR(50) NOT NULL,
    warehouse_id VARCHAR(20) NOT NULL,
    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    quantity_in_transit INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER NOT NULL DEFAULT 0,
    reorder_quantity INTEGER NOT NULL DEFAULT 0,
    unit_cost DECIMAL(10, 2),
    holding_cost_per_unit DECIMAL(10, 2),
    stockout_cost_per_unit DECIMAL(10, 2),
    inventory_status VARCHAR(20) DEFAULT 'NORMAL',
    last_stock_check TIMESTAMP,
    last_reorder_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version BIGINT DEFAULT 0,
    CONSTRAINT uk_sku_warehouse UNIQUE (sku, warehouse_id)
);

-- Create inventory_transactions table (if not exists)
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(255) NOT NULL,
    warehouse_id VARCHAR(255) NOT NULL,
    quantity_change INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reference_id VARCHAR(255),
    notes TEXT,
    inventory_item_id BIGINT REFERENCES inventory_items(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sku_warehouse ON inventory_items(sku, warehouse_id);
CREATE INDEX IF NOT EXISTS idx_warehouse ON inventory_items(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_reorder_point ON inventory_items(reorder_point);
CREATE INDEX IF NOT EXISTS idx_transactions_sku ON inventory_transactions(sku);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON inventory_transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_transactions_sku_warehouse ON inventory_transactions(sku, warehouse_id);

-- Analytics schema for processed metrics
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.processed_metrics (
    id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(255) NOT NULL,
    warehouse_id VARCHAR(255) NOT NULL,
    velocity_7d DOUBLE PRECISION,
    velocity_30d DOUBLE PRECISION,
    volatility DOUBLE PRECISION,
    trend DOUBLE PRECISION,
    seasonality_index DOUBLE PRECISION,
    stockout_risk DOUBLE PRECISION,
    reorder_recommendation INTEGER,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metrics_sku_wh ON analytics.processed_metrics(sku, warehouse_id);
CREATE INDEX IF NOT EXISTS idx_metrics_processed_at ON analytics.processed_metrics(processed_at);

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

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON analytics.pipeline_runs(status, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_metric_history_processed_at ON analytics.metric_history(processed_at DESC);
CREATE INDEX IF NOT EXISTS idx_invalid_inventory_events_recorded_at ON analytics.invalid_inventory_events(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_current_metrics_updated_at ON analytics.current_metrics(updated_at DESC);
