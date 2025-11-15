#!/bin/bash

# Test API script to demonstrate all API endpoints
# This script tests all API endpoints and shows responses

set -e

BASE_URL="http://localhost:9000"
INVENTORY_SERVICE="http://localhost:8080"
ANALYTICS_SERVICE="http://localhost:8000"

echo "========================================="
echo "Testing Inventory Management System APIs"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if services are running
echo -e "${BLUE}Checking if services are running...${NC}"
if ! curl -s -f "$INVENTORY_SERVICE/actuator/health" > /dev/null; then
    echo -e "${RED}Error: Inventory service is not running${NC}"
    echo "Please start the services first: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}Services are running!${NC}"
echo ""

# Test 1: Health Checks
echo -e "${BLUE}Test 1: Health Checks${NC}"
echo "GET $BASE_URL/actuator/health"
RESPONSE=$(curl -s "$BASE_URL/actuator/health")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "$RESPONSE" | head -5
else
    echo -e "${RED}✗ Health check failed${NC}"
fi
echo ""

# Test 2: Get Categories
echo -e "${BLUE}Test 2: Get Categories${NC}"
echo "GET $BASE_URL/api/v1/categories"
RESPONSE=$(curl -s "$BASE_URL/api/v1/categories")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Get categories passed${NC}"
    echo "$RESPONSE" | head -10
else
    echo -e "${RED}✗ Get categories failed${NC}"
fi
echo ""

# Test 3: Get Warehouses
echo -e "${BLUE}Test 3: Get Warehouses${NC}"
echo "GET $BASE_URL/api/v1/warehouses"
RESPONSE=$(curl -s "$BASE_URL/api/v1/warehouses")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Get warehouses passed${NC}"
    echo "$RESPONSE" | head -10
else
    echo -e "${RED}✗ Get warehouses failed${NC}"
fi
echo ""

# Test 4: Get Products
echo -e "${BLUE}Test 4: Get Products${NC}"
echo "GET $BASE_URL/api/v1/products?pageNumber=0&pageSize=5"
RESPONSE=$(curl -s "$BASE_URL/api/v1/products?pageNumber=0&pageSize=5")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Get products passed${NC}"
    echo "$RESPONSE" | head -15
else
    echo -e "${RED}✗ Get products failed${NC}"
fi
echo ""

# Test 5: Get Inventory
echo -e "${BLUE}Test 5: Get Inventory${NC}"
echo "GET $BASE_URL/api/v1/inventory/LAPTOP-001/WAREHOUSE-001"
RESPONSE=$(curl -s "$BASE_URL/api/v1/inventory/LAPTOP-001/WAREHOUSE-001")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Get inventory passed${NC}"
    echo "$RESPONSE" | head -10
else
    echo -e "${YELLOW}⚠ Get inventory failed (may need to seed data first)${NC}"
fi
echo ""

# Test 6: Record a Sale
echo -e "${BLUE}Test 6: Record a Sale${NC}"
echo "POST $BASE_URL/api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=1"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=1")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Record sale passed${NC}"
    echo "$RESPONSE" | head -10
else
    echo -e "${YELLOW}⚠ Record sale failed (may need to seed data first)${NC}"
fi
echo ""

# Test 7: Get Low Stock Items
echo -e "${BLUE}Test 7: Get Low Stock Items${NC}"
echo "GET $BASE_URL/api/v1/inventory/low-stock?threshold=20"
RESPONSE=$(curl -s "$BASE_URL/api/v1/inventory/low-stock?threshold=20")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Get low stock items passed${NC}"
    echo "$RESPONSE" | head -10
else
    echo -e "${YELLOW}⚠ Get low stock items failed (may need to seed data first)${NC}"
fi
echo ""

# Test 8: Get Analytics
echo -e "${BLUE}Test 8: Get Analytics${NC}"
echo "GET $ANALYTICS_SERVICE/api/v1/analytics/velocity/LAPTOP-001/WAREHOUSE-001?period_days=30"
RESPONSE=$(curl -s "$ANALYTICS_SERVICE/api/v1/analytics/velocity/LAPTOP-001/WAREHOUSE-001?period_days=30")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Get analytics passed${NC}"
    echo "$RESPONSE" | head -10
else
    echo -e "${YELLOW}⚠ Get analytics failed (may need to seed data first)${NC}"
fi
echo ""

# Test 9: Get Trend
echo -e "${BLUE}Test 9: Get Trend${NC}"
echo "GET $ANALYTICS_SERVICE/api/v1/analytics/trend/LAPTOP-001/WAREHOUSE-001?period_days=30"
RESPONSE=$(curl -s "$ANALYTICS_SERVICE/api/v1/analytics/trend/LAPTOP-001/WAREHOUSE-001?period_days=30")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Get trend passed${NC}"
    echo "$RESPONSE" | head -10
else
    echo -e "${YELLOW}⚠ Get trend failed (may need to seed data first)${NC}"
fi
echo ""

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}API Testing Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Note: Some tests may fail if data is not seeded."
echo "Run './scripts/seed-data.sh' first to seed sample data."
echo ""

