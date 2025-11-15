-- Seed data for demonstration
-- This script populates the database with sample data for testing and demonstration

-- Insert sample categories
INSERT INTO categories (name, description, status, created_at, updated_at)
VALUES 
    ('Electronics', 'Electronic devices and accessories', 'ACTIVE', NOW(), NOW()),
    ('Computers', 'Computers and laptops', 'ACTIVE', NOW(), NOW()),
    ('Phones', 'Smartphones and mobile devices', 'ACTIVE', NOW(), NOW()),
    ('Accessories', 'Device accessories', 'ACTIVE', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Insert sample warehouses
INSERT INTO warehouses (warehouse_id, name, address, city, state, zip_code, country, status, created_at, updated_at)
VALUES 
    ('WAREHOUSE-001', 'Main Warehouse', '123 Main St', 'New York', 'NY', '10001', 'USA', 'ACTIVE', NOW(), NOW()),
    ('WAREHOUSE-002', 'West Coast Warehouse', '456 Oak Ave', 'Los Angeles', 'CA', '90001', 'USA', 'ACTIVE', NOW(), NOW()),
    ('WAREHOUSE-003', 'East Coast Warehouse', '789 Pine Rd', 'Boston', 'MA', '02101', 'USA', 'ACTIVE', NOW(), NOW())
ON CONFLICT (warehouse_id) DO NOTHING;

-- Insert sample products
INSERT INTO products (sku, name, description, category_id, unit_price, status, created_at, updated_at)
SELECT 
    'LAPTOP-001',
    'Gaming Laptop',
    'High-performance gaming laptop with RTX 4070',
    c.id,
    1299.99,
    'ACTIVE',
    NOW(),
    NOW()
FROM categories c WHERE c.name = 'Computers'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (sku, name, description, category_id, unit_price, status, created_at, updated_at)
SELECT 
    'LAPTOP-002',
    'Business Laptop',
    'Professional business laptop',
    c.id,
    899.99,
    'ACTIVE',
    NOW(),
    NOW()
FROM categories c WHERE c.name = 'Computers'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (sku, name, description, category_id, unit_price, status, created_at, updated_at)
SELECT 
    'PHONE-001',
    'Smartphone Pro',
    'Latest smartphone with advanced features',
    c.id,
    799.99,
    'ACTIVE',
    NOW(),
    NOW()
FROM categories c WHERE c.name = 'Phones'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (sku, name, description, category_id, unit_price, status, created_at, updated_at)
SELECT 
    'PHONE-002',
    'Budget Smartphone',
    'Affordable smartphone with great features',
    c.id,
    299.99,
    'ACTIVE',
    NOW(),
    NOW()
FROM categories c WHERE c.name = 'Phones'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (sku, name, description, category_id, unit_price, status, created_at, updated_at)
SELECT 
    'TABLET-001',
    'Tablet Pro',
    'High-end tablet device',
    c.id,
    599.99,
    'ACTIVE',
    NOW(),
    NOW()
FROM categories c WHERE c.name = 'Electronics'
ON CONFLICT (sku) DO NOTHING;

INSERT INTO products (sku, name, description, category_id, unit_price, status, created_at, updated_at)
SELECT 
    'WATCH-001',
    'Smart Watch',
    'Feature-rich smartwatch',
    c.id,
    249.99,
    'ACTIVE',
    NOW(),
    NOW()
FROM categories c WHERE c.name = 'Accessories'
ON CONFLICT (sku) DO NOTHING;

-- Insert sample inventory items
INSERT INTO inventory_items (sku, warehouse_id, quantity_on_hand, quantity_reserved, reorder_point, reorder_quantity, unit_cost, inventory_status, created_at, updated_at)
VALUES 
    ('LAPTOP-001', 'WAREHOUSE-001', 50, 5, 20, 30, 1000.00, 'NORMAL', NOW(), NOW()),
    ('LAPTOP-001', 'WAREHOUSE-002', 30, 3, 15, 25, 1000.00, 'NORMAL', NOW(), NOW()),
    ('LAPTOP-002', 'WAREHOUSE-001', 40, 2, 15, 20, 700.00, 'NORMAL', NOW(), NOW()),
    ('PHONE-001', 'WAREHOUSE-001', 100, 10, 30, 50, 600.00, 'NORMAL', NOW(), NOW()),
    ('PHONE-001', 'WAREHOUSE-002', 80, 5, 25, 40, 600.00, 'NORMAL', NOW(), NOW()),
    ('PHONE-002', 'WAREHOUSE-001', 150, 8, 40, 60, 200.00, 'NORMAL', NOW(), NOW()),
    ('TABLET-001', 'WAREHOUSE-001', 60, 4, 20, 30, 400.00, 'NORMAL', NOW(), NOW()),
    ('WATCH-001', 'WAREHOUSE-001', 200, 15, 50, 100, 150.00, 'NORMAL', NOW(), NOW()),
    ('WATCH-001', 'WAREHOUSE-002', 120, 8, 30, 60, 150.00, 'NORMAL', NOW(), NOW())
ON CONFLICT (sku, warehouse_id) DO NOTHING;

-- Insert sample transactions (last 30 days)
INSERT INTO inventory_transactions (sku, warehouse_id, quantity_change, transaction_type, timestamp, reference_id, notes)
SELECT 
    i.sku,
    i.warehouse_id,
    -ABS((RANDOM() * 10 + 1)::INTEGER) as quantity_change,
    'SALE' as transaction_type,
    (NOW() - (RANDOM() * INTERVAL '30 days')) as timestamp,
    'ORDER-' || LPAD((RANDOM() * 10000)::INTEGER::TEXT, 6, '0') as reference_id,
    'Sample sale transaction' as notes
FROM inventory_items i
CROSS JOIN generate_series(1, 5)  -- 5 transactions per item
WHERE i.inventory_status = 'NORMAL'
ON CONFLICT DO NOTHING;

-- Insert some receipt transactions
INSERT INTO inventory_transactions (sku, warehouse_id, quantity_change, transaction_type, timestamp, reference_id, notes)
SELECT 
    i.sku,
    i.warehouse_id,
    ABS((RANDOM() * 50 + 20)::INTEGER) as quantity_change,
    'RESTOCK' as transaction_type,
    (NOW() - (RANDOM() * INTERVAL '30 days')) as timestamp,
    'RECEIPT-' || LPAD((RANDOM() * 10000)::INTEGER::TEXT, 6, '0') as reference_id,
    'Sample restock transaction' as notes
FROM inventory_items i
CROSS JOIN generate_series(1, 2)  -- 2 restock transactions per item
WHERE i.inventory_status = 'NORMAL'
ON CONFLICT DO NOTHING;

-- Update inventory quantities based on transactions
UPDATE inventory_items i
SET quantity_on_hand = i.quantity_on_hand + COALESCE(
    (SELECT SUM(t.quantity_change)
     FROM inventory_transactions t
     WHERE t.sku = i.sku 
       AND t.warehouse_id = i.warehouse_id
       AND t.transaction_type = 'RESTOCK'),
    0
) - COALESCE(
    (SELECT SUM(ABS(t.quantity_change))
     FROM inventory_transactions t
     WHERE t.sku = i.sku 
       AND t.warehouse_id = i.warehouse_id
       AND t.transaction_type = 'SALE'),
    0
)
WHERE EXISTS (
    SELECT 1 FROM inventory_transactions t
    WHERE t.sku = i.sku AND t.warehouse_id = i.warehouse_id
);

