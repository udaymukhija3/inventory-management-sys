#!/bin/bash

# Demo script to demonstrate the inventory management system
# This script shows key features: APIs, caching, event streaming, ETL

set -e

BASE_URL="http://localhost:9000"
INVENTORY_SERVICE="http://localhost:8080"
ANALYTICS_SERVICE="http://localhost:8000"

echo "========================================="
echo "Inventory Management System - Demo"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if services are running
echo -e "${BLUE}Checking if services are running...${NC}"
if ! curl -s -f "$INVENTORY_SERVICE/actuator/health" > /dev/null; then
    echo -e "${YELLOW}Warning: Inventory service is not running. Please start services first.${NC}"
    echo "Run: docker-compose up -d"
    exit 1
fi

echo -e "${GREEN}Services are running!${NC}"
echo ""

# 1. Demo: Get Products
echo -e "${BLUE}1. Demo: Get Products (with pagination)${NC}"
echo "GET $BASE_URL/api/v1/products?pageNumber=0&pageSize=5"
curl -s "$BASE_URL/api/v1/products?pageNumber=0&pageSize=5" | jq '.' || echo "Response received"
echo ""

# 2. Demo: Get Inventory
echo -e "${BLUE}2. Demo: Get Inventory${NC}"
echo "GET $BASE_URL/api/v1/inventory/LAPTOP-001/WAREHOUSE-001"
curl -s "$BASE_URL/api/v1/inventory/LAPTOP-001/WAREHOUSE-001" | jq '.' || echo "Response received"
echo ""

# 3. Demo: Record a Sale
echo -e "${BLUE}3. Demo: Record a Sale${NC}"
echo "POST $BASE_URL/api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=2"
curl -s -X POST "$BASE_URL/api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=2" | jq '.' || echo "Response received"
echo ""

# 4. Demo: Get Inventory Again (to show change)
echo -e "${BLUE}4. Demo: Get Inventory Again (to show quantity changed)${NC}"
echo "GET $BASE_URL/api/v1/inventory/LAPTOP-001/WAREHOUSE-001"
curl -s "$BASE_URL/api/v1/inventory/LAPTOP-001/WAREHOUSE-001" | jq '.' || echo "Response received"
echo ""

# 5. Demo: Get Analytics
echo -e "${BLUE}5. Demo: Get Analytics (Velocity)${NC}"
echo "GET $ANALYTICS_SERVICE/api/v1/analytics/velocity/LAPTOP-001/WAREHOUSE-001?period_days=30"
curl -s "$ANALYTICS_SERVICE/api/v1/analytics/velocity/LAPTOP-001/WAREHOUSE-001?period_days=30" | jq '.' || echo "Response received"
echo ""

# 6. Demo: Get Low Stock Items
echo -e "${BLUE}6. Demo: Get Low Stock Items${NC}"
echo "GET $BASE_URL/api/v1/inventory/low-stock?threshold=20"
curl -s "$BASE_URL/api/v1/inventory/low-stock?threshold=20" | jq '.' || echo "Response received"
echo ""

# 7. Demo: Get Categories
echo -e "${BLUE}7. Demo: Get Categories${NC}"
echo "GET $BASE_URL/api/v1/categories"
curl -s "$BASE_URL/api/v1/categories" | jq '.' || echo "Response received"
echo ""

# 8. Demo: Get Warehouses
echo -e "${BLUE}8. Demo: Get Warehouses${NC}"
echo "GET $BASE_URL/api/v1/warehouses"
curl -s "$BASE_URL/api/v1/warehouses" | jq '.' || echo "Response received"
echo ""

# 9. Demo: Health Check
echo -e "${BLUE}9. Demo: Health Check${NC}"
echo "GET $BASE_URL/actuator/health"
curl -s "$BASE_URL/actuator/health" | jq '.' || echo "Response received"
echo ""

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Demo completed!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Next steps:"
echo "  - Check Swagger UI: http://localhost:8080/swagger-ui.html"
echo "  - Check Airflow UI: http://localhost:8084 (admin/admin)"
echo "  - Check Prometheus: http://localhost:9090"
echo "  - Check Grafana: http://localhost:3000 (admin/admin)"
echo ""

