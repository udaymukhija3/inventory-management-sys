# Step-by-Step Guide to Run the Project

## ✅ Good News: No Code Changes Needed!

All existing services are **already designed** to work independently. The removed services (Elasticsearch, Flink, Airflow) were **optional** and not required by the core services.

### What Works Out of the Box:
- ✅ **Inventory Service** - Uses PostgreSQL, Redis, Kafka
- ✅ **Analytics Service** - Uses MongoDB, Redis, Kafka  
- ✅ **Reorder Service** - Uses PostgreSQL, Kafka
- ✅ **API Gateway** - Routes to all services

## Prerequisites

1. **Docker Desktop** running (M1 Mac supported)
2. **At least 8GB RAM** available
3. **10GB free disk space**

## Step 1: Verify Docker is Running

```bash
# Check Docker is running
docker info > /dev/null 2>&1 && echo "✅ Docker is running" || echo "❌ Please start Docker Desktop"

# If Docker is not running, start it:
open -a Docker
```

Wait 10-15 seconds for Docker to fully start.

## Step 2: Navigate to Project Directory

```bash
cd /Users/udaymukhija/inventory_management_sys
```

## Step 3: Start Minimal Services

```bash
# Start all minimal services (first time will download images - may take 3-5 minutes)
docker-compose -f docker-compose.dev.yml up -d
```

**What this does:**
- Downloads Docker images (first time only)
- Builds application images (Java/Python services)
- Starts all containers
- Initializes databases

**Expected output:**
```
Creating inventory-postgres ... done
Creating inventory-redis ... done
Creating inventory-mongodb ... done
Creating inventory-zookeeper ... done
Creating inventory-kafka ... done
Building inventory-service ...
Building analytics-service ...
...
```

## Step 4: Wait for Services to Start (1-2 minutes)

Services need time to:
1. Initialize databases
2. Connect to each other
3. Start Spring Boot applications

**Check status:**
```bash
# View container status
docker-compose -f docker-compose.dev.yml ps

# You should see all services as "Up" or "Up (healthy)"
```

**If a service is restarting:**
```bash
# Check logs for errors
docker-compose -f docker-compose.dev.yml logs <service-name>

# Example: Check inventory service
docker-compose -f docker-compose.dev.yml logs inventory-service
```

## Step 5: Verify Services Are Healthy

```bash
# Test health endpoints one by one
curl http://localhost:9000/actuator/health  # API Gateway
curl http://localhost:8080/actuator/health  # Inventory Service  
curl http://localhost:8000/health           # Analytics Service
curl http://localhost:8081/actuator/health  # Reorder Service

# Or use the health check script
./scripts/health-check.sh
```

**Expected response:**
```json
{"status":"UP"}
```

## Step 6: Seed Sample Data

```bash
# Populate database with sample products, categories, warehouses
./scripts/seed-data.sh
```

**This creates:**
- Sample categories (Electronics, Clothing, etc.)
- Sample products (Laptops, Phones, etc.)
- Sample warehouses (WAREHOUSE-001, etc.)
- Sample inventory entries

**Expected output:**
```
Seeding database with sample data...
Creating categories...
Creating products...
Creating warehouses...
✅ Data seeding completed successfully!
```

## Step 7: Test the API

### Quick Test - Get All Products

```bash
# Via API Gateway (recommended)
curl http://localhost:9000/api/v1/products

# Or directly from Inventory Service
curl http://localhost:8080/api/v1/products
```

### Create a Product

```bash
curl -X POST http://localhost:9000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TEST-001",
    "name": "Test Product",
    "description": "A test product",
    "categoryId": 1,
    "unitPrice": 99.99,
    "status": "ACTIVE"
  }'
```

### Get Inventory

```bash
curl http://localhost:9000/api/v1/inventory/TEST-001/WAREHOUSE-001
```

### Record a Sale

```bash
curl -X POST "http://localhost:9000/api/v1/inventory/sale?sku=TEST-001&warehouseId=WAREHOUSE-001&quantity=2"
```

## Step 8: Access API Documentation

Open in your browser:

- **Swagger UI (Inventory Service)**: http://localhost:8080/swagger-ui.html
- **FastAPI Docs (Analytics Service)**: http://localhost:8000/api/docs
- **API Gateway Health**: http://localhost:9000/actuator/health

## Troubleshooting

### Issue: Services won't start

**Check ports are free:**
```bash
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis  
lsof -i :8080  # Inventory Service
lsof -i :9000  # API Gateway
```

**Check Docker resources:**
- Docker Desktop → Settings → Resources
- Ensure at least 8GB RAM allocated
- At least 10GB disk space

### Issue: Connection refused errors

**Wait longer** - services need 1-2 minutes to fully start:
```bash
# Watch logs in real-time
docker-compose -f docker-compose.dev.yml logs -f inventory-service
```

### Issue: Out of memory

**Reduce Redis memory:**
Edit `docker-compose.dev.yml`:
```yaml
redis:
  command: redis-server --maxmemory 256mb ...
```

### Issue: Build failures

**Clean and rebuild:**
```bash
# Stop everything
docker-compose -f docker-compose.dev.yml down

# Remove old images
docker-compose -f docker-compose.dev.yml build --no-cache

# Start again
docker-compose -f docker-compose.dev.yml up -d
```

## View Logs

```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f inventory-service
docker-compose -f docker-compose.dev.yml logs -f analytics-service
docker-compose -f docker-compose.dev.yml logs -f api-gateway
```

## Stop Services

```bash
# Stop all services (keeps data)
docker-compose -f docker-compose.dev.yml stop

# Stop and remove containers (keeps data)
docker-compose -f docker-compose.dev.yml down

# Stop and remove everything including data (clean slate)
docker-compose -f docker-compose.dev.yml down -v
```

## What Services Are Running?

```bash
docker-compose -f docker-compose.dev.yml ps
```

You should see:
- ✅ inventory-postgres (PostgreSQL database)
- ✅ inventory-redis (Redis cache)
- ✅ inventory-mongodb (MongoDB for analytics)
- ✅ inventory-zookeeper (Kafka coordination)
- ✅ inventory-kafka (Event streaming)
- ✅ inventory-service (Java/Spring Boot)
- ✅ analytics-service (Python/FastAPI)
- ✅ reorder-service (Java/Spring Boot)
- ✅ api-gateway (Spring Cloud Gateway)

## Next Steps

1. **Explore APIs**: Run `./scripts/test-apis.sh`
2. **Run Demo**: Run `./scripts/demo.sh`
3. **Read Docs**: Check `docs/API.md` for all endpoints
4. **Understand Architecture**: Read `docs/ARCHITECTURE.md`

## Quick Command Reference

```bash
# Start
docker-compose -f docker-compose.dev.yml up -d

# Status
docker-compose -f docker-compose.dev.yml ps

# Logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop
docker-compose -f docker-compose.dev.yml down

# Restart
docker-compose -f docker-compose.dev.yml restart

# Health check
curl http://localhost:9000/actuator/health
```

