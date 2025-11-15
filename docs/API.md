# API Documentation

Complete API reference for the Inventory Management System.

## Base URLs

- **API Gateway**: `http://localhost:9000`
- **Inventory Service**: `http://localhost:8080`
- **Analytics Service**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8080/swagger-ui.html`

## Inventory Service API

### Products

#### Create Product
```bash
POST /api/v1/products
Content-Type: application/json

{
  "sku": "LAPTOP-001",
  "name": "Gaming Laptop",
  "description": "High-performance gaming laptop",
  "categoryId": 1,
  "price": 1299.99,
  "isActive": true
}
```

**Example:**
```bash
curl -X POST http://localhost:9000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LAPTOP-001",
    "name": "Gaming Laptop",
    "description": "High-performance gaming laptop",
    "categoryId": 1,
    "price": 1299.99,
    "isActive": true
  }'
```

#### Get Product by ID
```bash
GET /api/v1/products/{id}
```

**Example:**
```bash
curl http://localhost:9000/api/v1/products/1
```

#### Get Product by SKU
```bash
GET /api/v1/products/sku/{sku}
```

**Example:**
```bash
curl http://localhost:9000/api/v1/products/sku/LAPTOP-001
```

#### Get All Products (Paginated)
```bash
GET /api/v1/products?pageNumber=0&pageSize=10&sortBy=name&direction=ASC
```

**Example:**
```bash
curl "http://localhost:9000/api/v1/products?pageNumber=0&pageSize=10&sortBy=name&direction=ASC"
```

#### Search Products
```bash
GET /api/v1/products/search?searchTerm=laptop&pageNumber=0&pageSize=10
```

**Example:**
```bash
curl "http://localhost:9000/api/v1/products/search?searchTerm=laptop&pageNumber=0&pageSize=10"
```

#### Update Product
```bash
PUT /api/v1/products/{id}
Content-Type: application/json

{
  "sku": "LAPTOP-001",
  "name": "Gaming Laptop Pro",
  "description": "Updated description",
  "categoryId": 1,
  "price": 1399.99,
  "isActive": true
}
```

#### Delete Product
```bash
DELETE /api/v1/products/{id}
```

### Categories

#### Create Category
```bash
POST /api/v1/categories
Content-Type: application/json

{
  "name": "Electronics",
  "description": "Electronic devices and accessories",
  "isActive": true
}
```

#### Get Category by ID
```bash
GET /api/v1/categories/{id}
```

#### Get All Categories
```bash
GET /api/v1/categories
```

### Warehouses

#### Create Warehouse
```bash
POST /api/v1/warehouses
Content-Type: application/json

{
  "warehouseId": "WAREHOUSE-001",
  "name": "Main Warehouse",
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "country": "USA",
  "postalCode": "10001",
  "isActive": true
}
```

#### Get Warehouse by ID
```bash
GET /api/v1/warehouses/{id}
```

#### Get Warehouse by Warehouse ID
```bash
GET /api/v1/warehouses/warehouse-id/{warehouseId}
```

#### Get All Warehouses
```bash
GET /api/v1/warehouses
```

### Inventory

#### Get Inventory
```bash
GET /api/v1/inventory/{sku}/{warehouseId}
```

**Example:**
```bash
curl http://localhost:9000/api/v1/inventory/LAPTOP-001/WAREHOUSE-001
```

**Response:**
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

#### Adjust Inventory
```bash
POST /api/v1/inventory/adjust
Content-Type: application/json

{
  "sku": "LAPTOP-001",
  "warehouseId": "WAREHOUSE-001",
  "quantityChange": -10,
  "reason": "Damaged items"
}
```

#### Reserve Inventory
```bash
POST /api/v1/inventory/reserve?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=5
```

**Example:**
```bash
curl -X POST "http://localhost:9000/api/v1/inventory/reserve?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=5"
```

#### Release Reservation
```bash
POST /api/v1/inventory/release?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=5
```

#### Record Sale
```bash
POST /api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=2
```

**Example:**
```bash
curl -X POST "http://localhost:9000/api/v1/inventory/sale?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=2"
```

#### Record Receipt
```bash
POST /api/v1/inventory/receipt?sku=LAPTOP-001&warehouseId=WAREHOUSE-001&quantity=20
```

#### Get Low Stock Items
```bash
GET /api/v1/inventory/low-stock?threshold=10
```

**Example:**
```bash
curl "http://localhost:9000/api/v1/inventory/low-stock?threshold=10"
```

#### Get Items Needing Reorder
```bash
GET /api/v1/inventory/needs-reorder
```

### Transactions

#### Get Transactions by SKU
```bash
GET /api/v1/transactions/sku/{sku}
```

#### Get Transactions by Warehouse
```bash
GET /api/v1/transactions/warehouse/{warehouseId}
```

#### Get Transactions by Date Range
```bash
GET /api/v1/transactions/date-range?startDate=2024-01-01&endDate=2024-01-31
```

### Analytics (from Inventory Service)

#### Get Velocity
```bash
GET /api/v1/analytics/velocity/{sku}/{warehouseId}?periodDays=30
```

#### Get Turnover
```bash
GET /api/v1/analytics/turnover/{sku}/{warehouseId}
```

#### Get Low Stock Summary
```bash
GET /api/v1/analytics/low-stock
```

#### Get Warehouse Summary
```bash
GET /api/v1/analytics/warehouse/{warehouseId}/summary
```

## Analytics Service API

### Velocity Metrics

#### Get Velocity
```bash
GET /api/v1/analytics/velocity/{sku}/{warehouse_id}?period_days=30
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/analytics/velocity/LAPTOP-001/WAREHOUSE-001?period_days=30"
```

**Response:**
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

### Trend Analysis

#### Get Trend
```bash
GET /api/v1/analytics/trend/{sku}/{warehouse_id}?period_days=30
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/analytics/trend/LAPTOP-001/WAREHOUSE-001?period_days=30"
```

**Response:**
```json
{
  "sku": "LAPTOP-001",
  "warehouse_id": "WAREHOUSE-001",
  "period_days": 30,
  "velocity_7d": 5.2,
  "velocity_30d": 4.8,
  "trend_direction": "increasing",
  "average_daily_sales": 4.8,
  "message": "Basic trend analysis based on historical data (no ML predictions)"
}
```

### Health Check

#### Health Check
```bash
GET /health
```

**Example:**
```bash
curl http://localhost:8000/health
```

## Reorder Service API

### Reorder Recommendation

#### Generate Reorder Recommendation
```bash
POST /api/v1/reorder/recommend
Content-Type: application/json

{
  "sku": "LAPTOP-001",
  "warehouseId": "WAREHOUSE-001",
  "currentQuantity": 15,
  "reorderPoint": 20
}
```

**Example:**
```bash
curl -X POST http://localhost:9000/api/v1/reorder/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "LAPTOP-001",
    "warehouseId": "WAREHOUSE-001",
    "currentQuantity": 15,
    "reorderPoint": 20
  }'
```

## API Gateway

### Health Check
```bash
GET /actuator/health
```

**Example:**
```bash
curl http://localhost:9000/actuator/health
```

### Metrics
```bash
GET /actuator/metrics
```

## Error Responses

All APIs return standard error responses:

```json
{
  "error": "Error message",
  "status_code": 400,
  "path": "/api/v1/products"
}
```

### Common Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Rate Limiting

The API Gateway implements rate limiting:
- **Analytics Service**: 100 requests/minute
- **Inventory Service**: 1000 requests/minute

## Authentication

Currently, the API does not require authentication. For production, implement:
- JWT tokens
- API keys
- OAuth2

## Swagger Documentation

Interactive API documentation is available at:
- **Inventory Service**: http://localhost:8080/swagger-ui.html
- **Analytics Service**: http://localhost:8000/api/docs

## Testing

Use the provided demo script to test the APIs:

```bash
./scripts/demo.sh
```

Or test individual endpoints using curl or Postman.
