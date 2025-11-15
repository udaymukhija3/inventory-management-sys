// Initialize MongoDB for analytics service

db = db.getSiblingDB('inventory_analytics');

db.createCollection('inventory_transactions');
db.createCollection('predictions');
db.createCollection('models');

db.inventory_transactions.createIndex({ "sku": 1, "warehouse_id": 1 });
db.inventory_transactions.createIndex({ "timestamp": 1 });
db.predictions.createIndex({ "sku": 1, "warehouse_id": 1 });
db.models.createIndex({ "model_key": 1 });

print("MongoDB initialized successfully");

