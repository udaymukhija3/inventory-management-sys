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
