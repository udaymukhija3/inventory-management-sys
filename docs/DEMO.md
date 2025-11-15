# Demo Guide

This guide provides step-by-step instructions for demonstrating the Inventory Management System.

## Prerequisites

1. **Docker and Docker Compose** installed
2. **curl** installed (for API testing)
3. **jq** installed (optional, for JSON formatting)
4. **PostgreSQL client** (optional, for database access)

## Setup

### 1. Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# Check service logs
docker-compose logs -f
```

### 2. Wait for Services to Start

Wait for all services to be healthy (may take 2-3 minutes):

```bash
# Check health endpoints
curl http://localhost:8080/actuator/health
curl http://localhost:8000/health
curl http://localhost:9000/actuator/health
```

### 3. Seed Sample Data

```bash
# Seed database with sample data
./scripts/seed-data.sh
```

## Demonstration

### Option 1: Run Demo Script

```bash
# Run automated demo script
./scripts/demo.sh
```

This script demonstrates:
- API endpoints (CRUD operations)
- Caching performance
- Event streaming
- ETL pipeline
- Data quality checks

### Option 2: Manual Demonstration

#### 1. API Endpoints

##### Get Products
```bash
curl http://localhost:9000/api/v1/products?pageNumber=0&pageSize=5
```

##### Get Inventory
```bash
curl http://localhost:9000/api/v1/inventory/LAPTOP-001/WAREHOUSE-001
```

##### Record a Sale
```bash
curl -X POST "http://localhost:9000/api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=2"
```

##### Get Inventory Again (to show change)
```bash
curl http://localhost:9000/api/v1/inventory/LAPTOP-001/WAREHOUSE-001
```

##### Get Analytics
```bash
curl "http://localhost:8000/api/v1/analytics/velocity/LAPTOP-001/WAREHOUSE-001?period_days=30"
```

##### Get Low Stock Items
```bash
curl "http://localhost:9000/api/v1/inventory/low-stock?threshold=20"
```

#### 2. Swagger UI

1. Open Swagger UI: http://localhost:8080/swagger-ui.html
2. Explore API endpoints
3. Test API endpoints directly from Swagger UI

#### 3. Airflow UI

1. Open Airflow UI: http://localhost:8084
2. Login: admin/admin
3. View DAGs:
   - `inventory_etl_pipeline` - Daily ETL pipeline
   - `transaction_aggregation` - Transaction aggregation
   - `low_stock_alerts` - Low stock alerts
   - `data_quality_checks` - Data quality checks
4. Trigger a DAG manually
5. View DAG execution logs

#### 4. Prometheus

1. Open Prometheus: http://localhost:9090
2. Explore metrics
3. Query metrics:
   - `http_server_requests_seconds_count` - Request count
   - `jvm_memory_used_bytes` - Memory usage
   - `process_cpu_usage` - CPU usage

#### 5. Grafana

1. Open Grafana: http://localhost:3000
2. Login: admin/admin
3. View dashboards:
   - Inventory Dashboard
   - Service Metrics Dashboard
   - API Performance Dashboard

#### 6. Kafka Events

1. Check Kafka topics:
```bash
docker exec -it inventory-kafka kafka-topics --list --bootstrap-server localhost:9092
```

2. Consume events:
```bash
docker exec -it inventory-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic inventory-events --from-beginning
```

3. Produce an event (by making an API call):
```bash
curl -X POST "http://localhost:9000/api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=1"
```

#### 7. Redis Cache

1. Connect to Redis:
```bash
docker exec -it inventory-redis redis-cli -a redis_pass
```

2. Check cache keys:
```bash
KEYS *
```

3. Get cached data:
```bash
GET product:LAPTOP-001
GET inventory:LAPTOP-001:WAREHOUSE-001
```

4. Check cache performance:
```bash
INFO stats
```

#### 8. Database

1. Connect to PostgreSQL:
```bash
docker exec -it inventory-postgres psql -U inventory_user -d inventory
```

2. Query data:
```sql
-- Get products
SELECT * FROM products LIMIT 10;

-- Get inventory
SELECT * FROM inventory_items LIMIT 10;

-- Get transactions
SELECT * FROM inventory_transactions ORDER BY timestamp DESC LIMIT 10;

-- Get analytics
SELECT * FROM analytics.processed_metrics LIMIT 10;
```

## Expected Outputs

### API Responses

#### Get Products
```json
{
  "content": [
    {
      "id": 1,
      "sku": "LAPTOP-001",
      "name": "Gaming Laptop",
      "description": "High-performance gaming laptop",
      "price": 1299.99,
      "category": {
        "id": 1,
        "name": "Computers"
      },
      "isActive": true
    }
  ],
  "totalElements": 6,
  "totalPages": 1,
  "size": 10,
  "number": 0
}
```

#### Get Inventory
```json
{
  "sku": "LAPTOP-001",
  "warehouseId": "WAREHOUSE-001",
  "quantityOnHand": 50,
  "quantityReserved": 5,
  "availableQuantity": 45,
  "reorderPoint": 20,
  "reorderQuantity": 30,
  "unitCost": 1000.00,
  "status": "NORMAL"
}
```

#### Get Analytics
```json
{
  "sku": "LAPTOP-001",
  "warehouse_id": "WAREHOUSE-001",
  "period_days": 30,
  "velocity_7d": 5.2,
  "velocity_30d": 4.8,
  "total_sales": 144,
  "average_daily_sales": 4.8
}
```

## Troubleshooting

### Services Not Starting

1. Check Docker logs:
```bash
docker-compose logs -f
```

2. Check service health:
```bash
curl http://localhost:8080/actuator/health
curl http://localhost:8000/health
```

3. Check service dependencies:
```bash
docker-compose ps
```

### Database Connection Issues

1. Check PostgreSQL is running:
```bash
docker exec -it inventory-postgres pg_isready -U inventory_user
```

2. Check database connection:
```bash
docker exec -it inventory-postgres psql -U inventory_user -d inventory -c "SELECT 1;"
```

### API Not Responding

1. Check API Gateway:
```bash
curl http://localhost:9000/actuator/health
```

2. Check service directly:
```bash
curl http://localhost:8080/actuator/health
curl http://localhost:8000/health
```

3. Check service logs:
```bash
docker-compose logs inventory-service
docker-compose logs analytics-service
```

### Kafka Issues

1. Check Kafka is running:
```bash
docker exec -it inventory-kafka kafka-topics --list --bootstrap-server localhost:9092
```

2. Check Kafka logs:
```bash
docker-compose logs kafka
```

### Redis Issues

1. Check Redis is running:
```bash
docker exec -it inventory-redis redis-cli -a redis_pass ping
```

2. Check Redis logs:
```bash
docker-compose logs redis
```

## Next Steps

1. **Explore APIs**: Use Swagger UI to explore all API endpoints
2. **Run ETL Pipelines**: Trigger Airflow DAGs and monitor execution
3. **Monitor Metrics**: Check Prometheus and Grafana for system metrics
4. **Test Caching**: Verify Redis caching is working
5. **Test Events**: Produce and consume Kafka events
6. **Test Data Quality**: Run data quality checks and review results

## Conclusion

This demo guide provides step-by-step instructions for demonstrating the Inventory Management System. Follow the steps to showcase:
- Backend APIs (70%)
- Data Engineering (30%)
- System Architecture
- Performance Optimization
- Monitoring and Observability

For more information, see:
- [API Documentation](./API.md)
- [Architecture Documentation](./ARCHITECTURE.md)
- [Backend Design](./BACKEND_DESIGN.md)
- [Data Engineering](./DATA_ENGINEERING.md)

