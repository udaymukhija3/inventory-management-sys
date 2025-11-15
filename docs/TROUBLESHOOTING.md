# Troubleshooting Guide

## Common Issues

### Services Not Starting

1. **Check Docker containers**
   ```bash
   docker ps -a
   ```

2. **Check logs**
   ```bash
   docker-compose logs [service-name]
   ```

3. **Verify environment variables**
   - Check `.env` file exists
   - Verify all required environment variables are set

### Database Connection Issues

1. **Verify database is running**
   ```bash
   docker ps | grep postgres
   ```

2. **Check connection string**
   - Verify database connection string in application configuration
   - Check database credentials in `.env` file

3. **Verify network connectivity**
   - Ensure services are on the same Docker network
   - Check network configuration in `docker-compose.yml`

### Kafka Connection Issues

1. **Ensure Zookeeper is running**
   ```bash
   docker ps | grep zookeeper
   ```

2. **Check Kafka broker configuration**
   - Verify Kafka broker address in environment variables
   - Check Kafka logs for errors

3. **Verify topic exists**
   ```bash
   docker exec -it inventory-kafka kafka-topics --list --bootstrap-server localhost:9092
   ```

### Redis Connection Issues

1. **Verify Redis is running**
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

### API Gateway Issues

1. **Check API Gateway logs**
   ```bash
   docker-compose logs api-gateway
   ```

2. **Verify service routing**
   - Check route configuration in `api-gateway/src/main/resources/application.yml`
   - Verify services are accessible

3. **Check rate limiting**
   - Verify rate limit configuration
   - Check if requests are being rate limited

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

4. **Check database connection**
   - Verify Airflow database connection
   - Check Airflow database is initialized

### Data Quality Issues

1. **Check data quality DAG**
   - Verify data quality DAG is running
   - Check data quality report in Airflow UI

2. **Review data quality issues**
   - Check data quality logs
   - Review data quality report

3. **Fix data quality issues**
   - Update invalid data
   - Fix data integrity issues

### ETL Pipeline Issues

1. **Check ETL pipeline logs**
   ```bash
   docker-compose logs data-pipeline
   ```

2. **Verify Kafka events**
   - Check if events are being produced
   - Verify events are being consumed

3. **Check database writes**
   - Verify data is being written to database
   - Check for database connection errors

## Log Locations

- **Application logs**: `logs/` directory
- **Docker logs**: `docker-compose logs [service-name]`
- **Airflow logs**: `airflow/logs/` directory
- **System logs**: `/var/log/` (Linux)

## Performance Tuning

### Caching

1. **Increase Redis memory**
   - Update Redis memory configuration in `docker-compose.yml`
   - Monitor cache hit rate

2. **Optimize cache TTL**
   - Adjust cache TTL based on data update frequency
   - Monitor cache performance

### Database

1. **Optimize database queries**
   - Add appropriate indexes
   - Use query optimization techniques

2. **Scale database**
   - Use read replicas for PostgreSQL
   - Scale MongoDB shards

### Services

1. **Horizontal scaling**
   - Scale services using Kubernetes
   - Use load balancing

2. **Optimize service configuration**
   - Adjust JVM settings for Java services
   - Optimize Python service configuration

### Kafka

1. **Tune Kafka consumer groups**
   - Adjust consumer group configuration
   - Optimize batch size

2. **Scale Kafka**
   - Add more Kafka brokers
   - Increase partition count

## Health Checks

### Service Health

1. **Check service health endpoints**
   ```bash
   curl http://localhost:9000/actuator/health
   curl http://localhost:8080/actuator/health
   curl http://localhost:8000/health
   ```

2. **Check service logs**
   ```bash
   docker-compose logs [service-name]
   ```

### Database Health

1. **Check database connection**
   ```bash
   docker exec -it inventory-postgres psql -U inventory_user -d inventory -c "SELECT 1;"
   ```

2. **Check database performance**
   - Monitor database query performance
   - Check database connection pool

### Kafka Health

1. **Check Kafka topics**
   ```bash
   docker exec -it inventory-kafka kafka-topics --list --bootstrap-server localhost:9092
   ```

2. **Check Kafka consumer lag**
   - Monitor consumer lag
   - Check consumer group status

## Common Solutions

### Service Won't Start

1. **Check port conflicts**
   - Verify ports are not already in use
   - Change port configuration if needed

2. **Check Docker resources**
   - Ensure Docker has enough resources
   - Increase Docker memory if needed

3. **Check service dependencies**
   - Verify all dependencies are running
   - Check service startup order

### Database Connection Failed

1. **Check database credentials**
   - Verify username and password
   - Check database name

2. **Check network connectivity**
   - Verify services can reach database
   - Check firewall rules

3. **Check database logs**
   - Review database logs for errors
   - Check database configuration

### API Returns Errors

1. **Check API logs**
   - Review API service logs
   - Check for error messages

2. **Verify request format**
   - Check request body format
   - Verify required fields

3. **Check database state**
   - Verify data exists in database
   - Check data integrity

## Getting Help

1. **Check documentation**
   - Review [Architecture Documentation](./ARCHITECTURE.md)
   - Check [API Documentation](./API.md)
   - Review [Deployment Guide](./DEPLOYMENT.md)

2. **Check logs**
   - Review service logs
   - Check application logs
   - Review system logs

3. **Verify configuration**
   - Check environment variables
   - Verify configuration files
   - Review service configuration

## Additional Resources

- **Docker Documentation**: https://docs.docker.com/
- **Spring Boot Documentation**: https://spring.io/projects/spring-boot
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Airflow Documentation**: https://airflow.apache.org/docs/
- **Kafka Documentation**: https://kafka.apache.org/documentation/
