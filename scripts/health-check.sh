#!/bin/bash

set -euo pipefail

if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker Desktop must be running before you run health checks."
    exit 1
fi

echo "Performing health checks..."

curl -f http://localhost:8080/actuator/health >/dev/null
echo "Inventory service is healthy"

curl -f http://localhost:8000/health/ >/dev/null
echo "Analytics service is healthy"

curl -f http://localhost:9090/-/ready >/dev/null
echo "Prometheus is healthy"

curl -f http://localhost:3001/api/health >/dev/null
echo "Grafana is healthy"

if docker ps --format '{{.Names}}' | grep -q '^ims-data-pipeline$'; then
    echo "Data pipeline container is running"
else
    echo "Data pipeline container is not running"
fi

echo "Supported services are healthy"
