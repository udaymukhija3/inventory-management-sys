#!/bin/bash

echo "Performing health checks..."

# Check inventory service
curl -f http://localhost:8080/actuator/health || exit 1

# Check analytics service
curl -f http://localhost:8000/health/ || exit 1

# Check api gateway
curl -f http://localhost:9000/actuator/health || exit 1

echo "All services are healthy!"

