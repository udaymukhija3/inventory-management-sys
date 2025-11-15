# Deployment Guide

This guide provides step-by-step instructions for deploying the Inventory Management System.

## Prerequisites

- Docker and Docker Compose
- Java 17+ (for local development)
- Python 3.11+ (for local development)
- Maven (for Java services)
- sbt (for Scala services - optional)

## Local Deployment

### 1. Clone the Repository

```bash
git clone <repository-url>
cd inventory_management_sys
```

### 2. Configure Environment Variables

Create a `.env` file (if not exists):

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# Check service logs
docker-compose logs -f
```

### 4. Wait for Services to Start

Wait for all services to be healthy (may take 2-3 minutes):

```bash
# Check health endpoints
curl http://localhost:8080/actuator/health
curl http://localhost:8000/health
curl http://localhost:9000/actuator/health
```

### 5. Seed Sample Data

```bash
# Seed database with sample data
./scripts/seed-data.sh
```

This script uses API endpoints to populate the database with sample data.

### 6. Verify Deployment

```bash
# Run health check script
./scripts/health-check.sh

# Run demo script
./scripts/demo.sh

# Test API endpoints
./scripts/test-apis.sh
```

## Production Deployment

### 1. Configure Production Environment

Create production environment file:

```bash
cp .env.example .env.prod
# Edit .env.prod with production configuration
```

### 2. Build Docker Images

```bash
# Build all services
make build

# Or build individually
docker build -t inventory-service:latest ./inventory-service
docker build -t analytics-service:latest ./analytics-service
docker build -t reorder-service:latest ./reorder-service
docker build -t api-gateway:latest ./api-gateway
```

### 3. Deploy with Docker Compose

```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Deploy with Kubernetes

```bash
# Apply Kubernetes configurations
kubectl apply -f infrastructure/kubernetes/namespace.yaml
kubectl apply -f infrastructure/kubernetes/configmaps/
kubectl apply -f infrastructure/kubernetes/deployments/

# Check deployment status
kubectl get pods -n inventory-system
kubectl get services -n inventory-system
```

### 5. Verify Production Deployment

```bash
# Check service health
curl https://your-domain.com/actuator/health

# Check service logs
kubectl logs -f deployment/inventory-service -n inventory-system
```

## Service URLs

### Local Development

- **API Gateway**: http://localhost:9000
- **Inventory Service**: http://localhost:8080
- **Analytics Service**: http://localhost:8000
- **Reorder Service**: http://localhost:8081
- **Swagger UI**: http://localhost:8080/swagger-ui.html
- **Airflow UI**: http://localhost:8084 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### Production

- **API Gateway**: https://your-domain.com
- **Swagger UI**: https://your-domain.com/swagger-ui.html
- **Airflow UI**: https://your-airflow-domain.com
- **Prometheus**: https://your-prometheus-domain.com
- **Grafana**: https://your-grafana-domain.com

## Health Checks

### Service Health Endpoints

- **API Gateway**: `GET /actuator/health`
- **Inventory Service**: `GET /actuator/health`
- **Analytics Service**: `GET /health`
- **Reorder Service**: `GET /actuator/health`

### Health Check Script

```bash
# Run health check script
./scripts/health-check.sh
```

## Monitoring

### Prometheus

- **URL**: http://localhost:9090
- **Metrics**: Service metrics, API metrics, database metrics
- **Alerts**: Configured in `monitoring/alerts/alert-rules.yml`

### Grafana

- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: admin
- **Dashboards**: Pre-configured dashboards in `monitoring/grafana/dashboards/`

## Troubleshooting

### Services Not Starting

1. **Check Docker logs**
   ```bash
   docker-compose logs -f [service-name]
   ```

2. **Check service health**
   ```bash
   curl http://localhost:8080/actuator/health
   ```

3. **Verify environment variables**
   - Check `.env` file exists
   - Verify all required variables are set

### Database Connection Issues

1. **Check PostgreSQL is running**
   ```bash
   docker ps | grep postgres
   ```

2. **Check database connection**
   ```bash
   docker exec -it inventory-postgres psql -U inventory_user -d inventory -c "SELECT 1;"
   ```

3. **Verify database credentials**
   - Check database credentials in `.env`
   - Verify database name matches configuration

### Kafka Connection Issues

1. **Check Kafka is running**
   ```bash
   docker ps | grep kafka
   ```

2. **Check Kafka topics**
   ```bash
   docker exec -it inventory-kafka kafka-topics --list --bootstrap-server localhost:9092
   ```

3. **Check Kafka logs**
   ```bash
   docker-compose logs kafka
   ```

### Redis Connection Issues

1. **Check Redis is running**
   ```bash
   docker ps | grep redis
   ```

2. **Check Redis connection**
   ```bash
   docker exec -it inventory-redis redis-cli -a redis_pass ping
   ```

3. **Check Redis logs**
   ```bash
   docker-compose logs redis
   ```

### Airflow Issues

1. **Check Airflow webserver**
   ```bash
   docker-compose logs airflow-webserver
   ```

2. **Check Airflow scheduler**
   ```bash
   docker-compose logs airflow-scheduler
   ```

3. **Verify DAGs are loaded**
   - Access Airflow UI: http://localhost:8084
   - Check if DAGs are visible
   - Verify DAGs are not paused

## Performance Tuning

### Database

1. **Optimize database queries**
   - Add appropriate indexes
   - Use query optimization techniques

2. **Scale database**
   - Use read replicas for PostgreSQL
   - Scale MongoDB shards

### Caching

1. **Increase Redis memory**
   - Update Redis memory configuration in `docker-compose.yml`
   - Monitor cache hit rate

2. **Optimize cache TTL**
   - Adjust cache TTL based on data update frequency
   - Monitor cache performance

### Services

1. **Horizontal scaling**
   - Scale services using Kubernetes
   - Use load balancing

2. **Optimize service configuration**
   - Adjust JVM settings for Java services
   - Optimize Python service configuration

## Backup and Recovery

### Database Backup

1. **PostgreSQL Backup**
   ```bash
   docker exec -it inventory-postgres pg_dump -U inventory_user inventory > backup.sql
   ```

2. **MongoDB Backup**
   ```bash
   docker exec -it inventory-mongodb mongodump --out /backup
   ```

### Database Recovery

1. **PostgreSQL Recovery**
   ```bash
   docker exec -i inventory-postgres psql -U inventory_user inventory < backup.sql
   ```

2. **MongoDB Recovery**
   ```bash
   docker exec -it inventory-mongodb mongorestore /backup
   ```

## Security

### Production Security

1. **Use HTTPS**
   - Configure SSL certificates
   - Use HTTPS for all services

2. **Implement Authentication**
   - Add JWT tokens
   - Implement API keys
   - Use OAuth2

3. **Secure Database**
   - Use strong passwords
   - Limit database access
   - Use SSL for database connections

4. **Secure Kafka**
   - Use SASL authentication
   - Enable SSL encryption
   - Limit topic access

## Scaling

### Horizontal Scaling

1. **Scale Services**
   ```bash
   # Scale inventory service
   docker-compose scale inventory-service=3
   ```

2. **Scale with Kubernetes**
   ```bash
   # Scale deployment
   kubectl scale deployment inventory-service --replicas=3 -n inventory-system
   ```

### Vertical Scaling

1. **Increase Service Resources**
   - Update Docker resource limits
   - Increase JVM heap size
   - Increase Python service memory

2. **Increase Database Resources**
   - Increase database memory
   - Increase database CPU
   - Optimize database configuration

## Maintenance

### Update Services

1. **Build new images**
   ```bash
   make build
   ```

2. **Update services**
   ```bash
   docker-compose up -d --build
   ```

3. **Verify update**
   ```bash
   ./scripts/health-check.sh
   ```

### Database Migrations

1. **Run migrations**
   ```bash
   ./scripts/migrate-db.sh
   ```

2. **Verify migrations**
   ```bash
   docker exec -it inventory-postgres psql -U inventory_user -d inventory -c "\dt"
   ```

## Additional Resources

- [Architecture Documentation](./ARCHITECTURE.md)
- [API Documentation](./API.md)
- [Backend Design](./BACKEND_DESIGN.md)
- [Data Engineering](./DATA_ENGINEERING.md)
- [Demo Guide](./DEMO.md)
- [Troubleshooting](./TROUBLESHOOTING.md)

## Support

For issues or questions, please:
1. Check the [Troubleshooting Guide](./TROUBLESHOOTING.md)
2. Review service logs
3. Check service health endpoints
4. Open an issue on GitHub
