-- Deterministic demo seed for the supported end-to-end flow.
-- This resets the operational and derived tables used by the demo so reruns are predictable.

BEGIN;

TRUNCATE TABLE analytics.data_quality_runs RESTART IDENTITY;
TRUNCATE TABLE analytics.current_metrics RESTART IDENTITY;
TRUNCATE TABLE analytics.metric_history RESTART IDENTITY;
TRUNCATE TABLE analytics.invalid_inventory_events RESTART IDENTITY;
TRUNCATE TABLE analytics.processed_event_log RESTART IDENTITY;
TRUNCATE TABLE analytics.pipeline_runs RESTART IDENTITY;
TRUNCATE TABLE analytics.processed_metrics RESTART IDENTITY;
TRUNCATE TABLE inventory_transactions RESTART IDENTITY CASCADE;
TRUNCATE TABLE inventory_items RESTART IDENTITY CASCADE;
TRUNCATE TABLE products RESTART IDENTITY CASCADE;
TRUNCATE TABLE warehouses RESTART IDENTITY CASCADE;
TRUNCATE TABLE categories RESTART IDENTITY CASCADE;

INSERT INTO categories (id, name, description, is_active, created_at, updated_at)
VALUES
    (nextval('categories_seq'), 'Electronics', 'Electronic devices and accessories', TRUE, NOW(), NOW()),
    (nextval('categories_seq'), 'Computers', 'Computers and laptops', TRUE, NOW(), NOW()),
    (nextval('categories_seq'), 'Phones', 'Smartphones and mobile devices', TRUE, NOW(), NOW()),
    (nextval('categories_seq'), 'Accessories', 'Device accessories', TRUE, NOW(), NOW());

INSERT INTO warehouses (id, warehouse_id, name, address, city, state, postal_code, country, is_active, created_at, updated_at)
VALUES
    (nextval('warehouses_seq'), 'WAREHOUSE-001', 'Main Warehouse', '123 Main St', 'New York', 'NY', '10001', 'USA', TRUE, NOW(), NOW()),
    (nextval('warehouses_seq'), 'WAREHOUSE-002', 'West Coast Warehouse', '456 Oak Ave', 'Los Angeles', 'CA', '90001', 'USA', TRUE, NOW(), NOW()),
    (nextval('warehouses_seq'), 'WAREHOUSE-003', 'East Coast Warehouse', '789 Pine Rd', 'Boston', 'MA', '02101', 'USA', TRUE, NOW(), NOW());

INSERT INTO products (id, sku, name, description, category_id, price, is_active, created_at, updated_at)
SELECT nextval('products_seq'), 'LAPTOP-001', 'Gaming Laptop', 'High-performance gaming laptop with RTX 4070', c.id, 1299.99, TRUE, NOW(), NOW()
FROM categories c WHERE c.name = 'Computers';

INSERT INTO products (id, sku, name, description, category_id, price, is_active, created_at, updated_at)
SELECT nextval('products_seq'), 'LAPTOP-002', 'Business Laptop', 'Professional business laptop', c.id, 899.99, TRUE, NOW(), NOW()
FROM categories c WHERE c.name = 'Computers';

INSERT INTO products (id, sku, name, description, category_id, price, is_active, created_at, updated_at)
SELECT nextval('products_seq'), 'PHONE-001', 'Smartphone Pro', 'Latest smartphone with advanced features', c.id, 799.99, TRUE, NOW(), NOW()
FROM categories c WHERE c.name = 'Phones';

INSERT INTO products (id, sku, name, description, category_id, price, is_active, created_at, updated_at)
SELECT nextval('products_seq'), 'PHONE-002', 'Budget Smartphone', 'Affordable smartphone with great features', c.id, 299.99, TRUE, NOW(), NOW()
FROM categories c WHERE c.name = 'Phones';

INSERT INTO products (id, sku, name, description, category_id, price, is_active, created_at, updated_at)
SELECT nextval('products_seq'), 'TABLET-001', 'Tablet Pro', 'High-end tablet device', c.id, 599.99, TRUE, NOW(), NOW()
FROM categories c WHERE c.name = 'Electronics';

INSERT INTO products (id, sku, name, description, category_id, price, is_active, created_at, updated_at)
SELECT nextval('products_seq'), 'WATCH-001', 'Smart Watch', 'Feature-rich smartwatch', c.id, 249.99, TRUE, NOW(), NOW()
FROM categories c WHERE c.name = 'Accessories';

INSERT INTO inventory_items (
    id, sku, warehouse_id, quantity_on_hand, quantity_reserved, reorder_point,
    reorder_quantity, unit_cost, inventory_status, created_at, updated_at
)
VALUES
    (nextval('inventory_items_seq'), 'LAPTOP-001', 'WAREHOUSE-001', 42, 4, 20, 30, 1000.00, 'NORMAL', NOW(), NOW()),
    (nextval('inventory_items_seq'), 'LAPTOP-001', 'WAREHOUSE-002', 28, 2, 15, 25, 1000.00, 'NORMAL', NOW(), NOW()),
    (nextval('inventory_items_seq'), 'LAPTOP-002', 'WAREHOUSE-001', 35, 3, 15, 20, 700.00, 'NORMAL', NOW(), NOW()),
    (nextval('inventory_items_seq'), 'PHONE-001', 'WAREHOUSE-001', 96, 8, 30, 50, 600.00, 'NORMAL', NOW(), NOW()),
    (nextval('inventory_items_seq'), 'PHONE-001', 'WAREHOUSE-002', 77, 5, 25, 40, 600.00, 'NORMAL', NOW(), NOW()),
    (nextval('inventory_items_seq'), 'PHONE-002', 'WAREHOUSE-001', 143, 6, 40, 60, 200.00, 'NORMAL', NOW(), NOW()),
    (nextval('inventory_items_seq'), 'TABLET-001', 'WAREHOUSE-001', 57, 3, 20, 30, 400.00, 'NORMAL', NOW(), NOW()),
    (nextval('inventory_items_seq'), 'WATCH-001', 'WAREHOUSE-001', 190, 10, 50, 100, 150.00, 'NORMAL', NOW(), NOW()),
    (nextval('inventory_items_seq'), 'WATCH-001', 'WAREHOUSE-002', 114, 6, 30, 60, 150.00, 'NORMAL', NOW(), NOW());

INSERT INTO inventory_transactions (sku, warehouse_id, quantity_change, transaction_type, timestamp, reference_id, notes)
VALUES
    ('LAPTOP-001', 'WAREHOUSE-001', -2, 'SALE', NOW() - INTERVAL '2 days', 'ORDER-100001', 'Deterministic demo sale'),
    ('LAPTOP-001', 'WAREHOUSE-001', -1, 'SALE', NOW() - INTERVAL '5 days', 'ORDER-100002', 'Deterministic demo sale'),
    ('LAPTOP-001', 'WAREHOUSE-001', 5, 'RESTOCK', NOW() - INTERVAL '8 days', 'RECEIPT-100001', 'Deterministic demo restock'),
    ('LAPTOP-001', 'WAREHOUSE-002', -1, 'SALE', NOW() - INTERVAL '4 days', 'ORDER-100003', 'Deterministic demo sale'),
    ('LAPTOP-002', 'WAREHOUSE-001', -3, 'SALE', NOW() - INTERVAL '6 days', 'ORDER-100004', 'Deterministic demo sale'),
    ('PHONE-001', 'WAREHOUSE-001', -4, 'SALE', NOW() - INTERVAL '1 day', 'ORDER-100005', 'Deterministic demo sale'),
    ('PHONE-001', 'WAREHOUSE-001', -3, 'SALE', NOW() - INTERVAL '3 days', 'ORDER-100006', 'Deterministic demo sale'),
    ('PHONE-001', 'WAREHOUSE-002', -2, 'SALE', NOW() - INTERVAL '7 days', 'ORDER-100007', 'Deterministic demo sale'),
    ('PHONE-002', 'WAREHOUSE-001', -5, 'SALE', NOW() - INTERVAL '9 days', 'ORDER-100008', 'Deterministic demo sale'),
    ('PHONE-002', 'WAREHOUSE-001', 10, 'RESTOCK', NOW() - INTERVAL '12 days', 'RECEIPT-100002', 'Deterministic demo restock'),
    ('TABLET-001', 'WAREHOUSE-001', -2, 'SALE', NOW() - INTERVAL '11 days', 'ORDER-100009', 'Deterministic demo sale'),
    ('WATCH-001', 'WAREHOUSE-001', -6, 'SALE', NOW() - INTERVAL '2 days', 'ORDER-100010', 'Deterministic demo sale'),
    ('WATCH-001', 'WAREHOUSE-001', -4, 'SALE', NOW() - INTERVAL '10 days', 'ORDER-100011', 'Deterministic demo sale'),
    ('WATCH-001', 'WAREHOUSE-002', -3, 'SALE', NOW() - INTERVAL '13 days', 'ORDER-100012', 'Deterministic demo sale'),
    ('WATCH-001', 'WAREHOUSE-002', 8, 'RESTOCK', NOW() - INTERVAL '18 days', 'RECEIPT-100003', 'Deterministic demo restock');

COMMIT;
