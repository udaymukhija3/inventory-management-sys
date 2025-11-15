#!/bin/bash

set -e

echo "Deploying Inventory Management System..."

# Build all services
echo "Building services..."
make build

# Deploy to local environment
echo "Deploying to local environment..."
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Health check
./scripts/health-check.sh

echo "Deployment complete!"

