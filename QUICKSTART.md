# Quick Start Guide - Minimal Setup for M1 Mac

This guide helps you quickly get the Inventory Management System running on an M1 MacBook Pro with minimal complexity.

## Why Minimal Setup?

The full docker-compose.yml includes 15+ services (Elasticsearch, Flink, Airflow, Prometheus, Grafana) which:
- Require significant resources (RAM, CPU)
- May not run smoothly on M1 Mac
- Add unnecessary complexity for demonstrating basic engineering skills
- Take longer to download and start

The minimal setup (`docker-compose.dev.yml`) includes only **essential services** needed to demonstrate:
- ✅ Microservices architecture (3 services + API Gateway)
- ✅ RESTful APIs with CRUD operations
- ✅ Caching layer (Redis)
- ✅ Multiple databases (PostgreSQL, MongoDB)
- ✅ Event-driven architecture (Kafka)
- ✅ Python/Java integration

## Prerequisites

- **Docker Desktop** (with M1/ARM64 support)
- **8GB+ RAM** available
- **10GB+ free disk space**

## Step-by-Step Setup

### 1. Start Minimal Services

```bash
# Navigate to project directory
cd inventory_management_sys

# Start all minimal services (this may take 2-3 minutes on first run)
docker-compose -f docker-compose.dev.yml up -d
```

This starts:
- **PostgreSQL** (port 5432) - Primary database
- **Redis** (port 6379) - Caching layer
- **MongoDB** (port 27017) - Analytics database
- **Zookeeper** (port 2181) - Kafka coordination
- **Kafka** (port 9092) - Event streaming
- **Inventory Service** (port 8080) - Java/Spring Boot
- **Analytics Service** (port 8000) - Python/FastAPI
- **Reorder Service** (port 8081) - Java/Spring Boot
- **API Gateway** (port 9000) - Entry point

### 2. Verify Services Are Running

Wait 1-2 minutes for all services to start, then check status:

```bash
# Check container status
docker-compose -f docker-compose.dev.yml ps

# Check logs if any service is failing
docker-compose -f docker-compose.dev.yml logs inventory-service
docker-compose -f docker-compose.dev.yml logs analytics-service
```

### 3. Health Checks

Test that services are responding:

```bash
# API Gateway
curl http://localhost:9000/actuator/health

# Inventory Service
curl http://localhost:8080/actuator/health

# Analytics Service
curl http://localhost:8000/health
```

All should return `{"status":"UP"}` or similar.

### 4. Seed Sample Data

Populate the database with sample data:

```bash
# Run seed data script
./scripts/seed-data.sh
```

This creates:
- Sample categories
- Sample products
- Sample warehouses
- Sample inventory entries

### 5. Test the System

#### Quick API Test

```bash
# Get all products via API Gateway
curl http://localhost:9000/api/v1/products

# Get a specific product
curl http://localhost:9000/api/v1/products/LAPTOP-001/WAREHOUSE-001

# Record a sale
curl -X POST "http://localhost:9000/api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=2"
```

#### Access API Documentation

- **Swagger UI (Inventory Service)**: http://localhost:8080/swagger-ui.html
- **FastAPI Docs (Analytics Service)**: http://localhost:8000/api/docs

## Common Issues & Solutions

### Issue: Services won't start

**Solution**: Check if ports are already in use:
```bash
# Check for port conflicts
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8080  # Inventory Service
lsof -i :9000  # API Gateway
```

### Issue: "Cannot connect to Docker daemon"

**Solution**: Make sure Docker Desktop is running:
```bash
# Open Docker Desktop app, or
open -a Docker
```

### Issue: Out of memory

**Solution**: Reduce Redis memory limit in docker-compose.dev.yml:
```yaml
redis:
  command: redis-server --maxmemory 256mb ...
```

### Issue: Slow startup on M1 Mac

**Solution**: This is normal. Services need 2-3 minutes to:
1. Download images (first time only)
2. Build application images
3. Initialize databases
4. Start all services

## What's NOT Included (And Why)

The minimal setup excludes these services from the full docker-compose.yml:

- ❌ **Elasticsearch** - Large (~1GB), not essential for basic demo
- ❌ **Flink** - Stream processing, adds complexity
- ❌ **Airflow** - ETL orchestration, can be demonstrated separately
- ❌ **Prometheus/Grafana** - Monitoring, nice-to-have but not essential
- ❌ **Schema Registry** - Kafka schema management, advanced feature
- ❌ **Data Pipeline Service** - Can be run separately if needed

These can be added later if needed for specific demonstrations.

## Stopping Services

```bash
# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.dev.yml down -v
```

## Next Steps

- Explore the API endpoints: `./scripts/test-apis.sh`
- Run the demo script: `./scripts/demo.sh`
- Read the full documentation: `docs/API.md`
- Check architecture: `docs/ARCHITECTURE.md`

## Support

If you encounter issues:
1. Check service logs: `docker-compose -f docker-compose.dev.yml logs <service-name>`
2. Verify Docker resources: Docker Desktop → Settings → Resources
3. Check [Troubleshooting Guide](./docs/TROUBLESHOOTING.md)

