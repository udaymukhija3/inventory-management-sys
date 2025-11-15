# System Architecture

This document describes the overall system architecture of the Inventory Management System.

## Architecture Overview

The system follows a **microservices architecture** with **event-driven** communication patterns. The architecture is designed for scalability, performance, and reliability.

## System Components

### Core Services

1. **API Gateway** (Spring Cloud Gateway)
   - Single entry point for all requests
   - Request routing and load balancing
   - Rate limiting and security
   - Circuit breakers

2. **Inventory Service** (Java/Spring Boot)
   - Core inventory management
   - Product, category, warehouse management
   - Inventory operations (adjust, reserve, release, sale, receipt)
   - Transaction management

3. **Analytics Service** (Python/FastAPI)
   - Analytics and data aggregation
   - Velocity calculations
   - Trend analysis
   - Warehouse summaries

4. **Reorder Service** (Java/Spring Boot)
   - Automated reordering
   - Reorder recommendations
   - Purchase order generation

### Data Storage

1. **PostgreSQL**
   - Primary transactional database
   - ACID compliance
   - Stores: products, categories, warehouses, inventory, transactions

2. **MongoDB**
   - Analytics database
   - Document storage
   - Stores: transaction history, analytics metrics

3. **Redis**
   - Caching layer
   - High-performance key-value store
   - Reduces database load by 85-95%

### Message Queue

1. **Apache Kafka**
   - Event streaming platform
   - Decouples services
   - Enables event-driven architecture
   - Topics: inventory-events, reorder-events, analytics-events

### Data Processing

1. **Apache Airflow**
   - Workflow orchestration
   - ETL pipeline scheduling
   - Data quality checks
   - Batch processing

2. **Data Pipeline Service** (Python)
   - Real-time ETL processing
   - Kafka event consumption
   - Data transformation
   - Data quality validation

### Monitoring

1. **Prometheus**
   - Metrics collection
   - Time-series database

2. **Grafana**
   - Metrics visualization
   - Dashboards
   - Alerts

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Clients                               │
│                    (Web, Mobile, API)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│              (Spring Cloud Gateway)                          │
│  - Routing, Rate Limiting, Circuit Breakers                  │
└──────┬──────────────┬──────────────┬────────────────────────┘
       │              │              │
       ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Inventory  │ │  Analytics  │ │   Reorder   │
│   Service   │ │   Service   │ │   Service   │
│ (Spring Boot)│ │  (FastAPI)  │ │ (Spring Boot)│
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       │               │               │
       ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Storage Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │PostgreSQL│  │ MongoDB  │  │  Redis   │                  │
│  │(Primary) │  │(Analytics)│ │  (Cache)  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Message Queue                             │
│                      Apache Kafka                            │
│  - inventory-events                                          │
│  - reorder-events                                            │
│  - analytics-events                                          │
└──────┬───────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Processing Layer                       │
│  ┌──────────────┐  ┌──────────────────┐                    │
│  │   Airflow    │  │ Data Pipeline    │                    │
│  │  (ETL DAGs)  │  │   Service        │                    │
│  └──────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Layer                          │
│  ┌──────────┐  ┌──────────┐                                │
│  │Prometheus│  │  Grafana │                                │
│  │(Metrics) │  │(Dashboard)│                                │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Request Flow

1. **Client Request** → API Gateway
2. **API Gateway** → Routes to appropriate service
3. **Service** → Processes request
4. **Service** → Queries database (with caching)
5. **Service** → Publishes events to Kafka (if needed)
6. **Service** → Returns response to client

### Event Flow

1. **Inventory Update** → Publishes event to Kafka
2. **Kafka** → Consumers receive event
3. **Analytics Service** → Processes event for analytics
4. **Reorder Service** → Processes event for reordering
5. **Data Pipeline Service** → Processes event for ETL

### ETL Flow

1. **Airflow DAG** → Scheduled ETL job
2. **Extract** → Data from PostgreSQL
3. **Transform** → Data transformation and aggregation
4. **Load** → Data to analytics tables
5. **Data Quality** → Validation checks

## Microservices Communication

### Synchronous Communication (REST)

**Use Case**: Direct service-to-service calls

**Example**:
- Analytics Service calls Inventory Service for data
- Reorder Service calls Inventory Service for inventory levels

**Technology**: HTTP/REST

**Pros**:
- Simple to implement
- Easy to debug
- Direct response

**Cons**:
- Tight coupling
- Blocking calls
- No resilience to failures

### Asynchronous Communication (Kafka)

**Use Case**: Event-driven architecture

**Example**:
- Inventory updates publish events to Kafka
- Analytics Service consumes events
- Reorder Service consumes events

**Technology**: Apache Kafka

**Topics**:
- `inventory-events` - Inventory update events
- `reorder-events` - Reorder events
- `analytics-events` - Analytics events

**Pros**:
- Decoupled services
- Scalable
- Resilient to failures
- Event replay capability

**Cons**:
- More complex
- Eventual consistency
- Requires event schema management

## Database Architecture

### PostgreSQL (Primary Database)

**Purpose**: Transactional data storage

**Tables**:
- `products` - Product information
- `categories` - Category hierarchy
- `warehouses` - Warehouse information
- `inventory_items` - Inventory levels
- `inventory_transactions` - Transaction history

**Design Principles**:
- ACID compliance
- Normalized schema
- Proper indexing
- Foreign key constraints
- Timestamps for auditing

### MongoDB (Analytics Database)

**Purpose**: Analytics and document storage

**Collections**:
- `inventory_transactions` - Transaction history
- `analytics_metrics` - Aggregated metrics

**Design Principles**:
- Flexible schema
- Document-based storage
- Efficient for read-heavy workloads
- Good for time-series data

### Redis (Cache)

**Purpose**: Caching frequently accessed data

**Keys**:
- `product:{sku}` - Product data
- `inventory:{sku}:{warehouseId}` - Inventory data
- `category:{id}` - Category data

**Design Principles**:
- Cache-aside pattern
- TTL-based expiration
- High-performance key-value storage
- Reduces database load by 85-95%

## Event-Driven Architecture

### Event Producers

1. **Inventory Service**
   - Publishes inventory update events
   - Publishes transaction events

2. **Reorder Service**
   - Publishes reorder events

### Event Consumers

1. **Analytics Service**
   - Consumes inventory events
   - Processes events for analytics

2. **Reorder Service**
   - Consumes inventory events
   - Processes events for reordering

3. **Data Pipeline Service**
   - Consumes inventory events
   - Processes events for ETL

### Event Schema

```json
{
  "eventId": "uuid",
  "eventType": "INVENTORY_UPDATE",
  "sku": "LAPTOP-001",
  "warehouseId": "WAREHOUSE-001",
  "quantityChange": -2,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Data Processing Architecture

### ETL Pipeline (Airflow)

1. **Extract**
   - Data from PostgreSQL
   - Data from MongoDB
   - Data from Kafka

2. **Transform**
   - Data transformation
   - Data aggregation
   - Data validation

3. **Load**
   - Data to analytics tables
   - Data to data warehouse
   - Data to cache

### Real-Time Processing (Kafka)

1. **Event Consumption**
   - Consume events from Kafka
   - Process events in real-time
   - Transform events

2. **Data Transformation**
   - Calculate metrics
   - Aggregate data
   - Validate data

3. **Data Output**
   - Write to database
   - Write to cache
   - Publish to other topics

## Scalability

### Horizontal Scaling

1. **Services**
   - Multiple instances of each service
   - Load balancing via API Gateway
   - Stateless services

2. **Databases**
   - Read replicas for PostgreSQL
   - Sharding for MongoDB
   - Redis cluster

3. **Message Queue**
   - Kafka cluster
   - Multiple partitions
   - Consumer groups

### Vertical Scaling

1. **Services**
   - Increase CPU and memory
   - Optimize code
   - Use caching

2. **Databases**
   - Increase database resources
   - Optimize queries
   - Use indexing

## Reliability

### Fault Tolerance

1. **Circuit Breakers**
   - Prevents cascade failures
   - Falls back to error response
   - Automatically retries

2. **Retry Logic**
   - Automatic retries for failed requests
   - Exponential backoff
   - Maximum retry attempts

3. **Health Checks**
   - Service health endpoints
   - Automatic health checks
   - Health-based routing

### Data Consistency

1. **ACID Transactions**
   - PostgreSQL for transactional data
   - Database transactions
   - Data integrity

2. **Eventual Consistency**
   - Kafka events
   - Event replay capability
   - Event processing guarantees

## Security

### Current Implementation

- No authentication (for demonstration)
- API Gateway handles routing
- Rate limiting prevents abuse

### Production Recommendations

1. **Authentication**
   - JWT tokens
   - API keys
   - OAuth2

2. **Authorization**
   - Role-based access control (RBAC)
   - Resource-level permissions

3. **Security Headers**
   - CORS configuration
   - HTTPS only
   - Security headers

## Monitoring

### Metrics

1. **Prometheus**
   - Metrics collection
   - Time-series database
   - Alerting

2. **Grafana**
   - Metrics visualization
   - Dashboards
   - Alerts

### Logging

1. **Structured Logging**
   - JSON format
   - Log levels
   - Centralized logging

2. **Log Aggregation**
   - ELK stack (optional)
   - Log analysis
   - Log retention

### Health Checks

1. **Service Health**
   - Health endpoints
   - Health checks
   - Health-based routing

2. **Database Health**
   - Connection health
   - Query health
   - Replication health

## Deployment

### Docker

1. **Containerization**
   - Multi-stage builds
   - Optimized images
   - Health checks

2. **Docker Compose**
   - Local development
   - Service orchestration
   - Network configuration

### Kubernetes (Production)

1. **Pods**
   - Service instances
   - Resource limits
   - Health checks

2. **Services**
   - Load balancing
   - Service discovery
   - Network policies

3. **ConfigMaps**
   - Configuration
   - Environment variables
   - Secrets

## Conclusion

The system architecture is designed for:
- **Scalability**: Horizontal and vertical scaling
- **Performance**: Caching and optimization
- **Reliability**: Fault tolerance and health checks
- **Maintainability**: Clean architecture and documentation
- **Security**: Authentication and authorization

This architecture provides a solid foundation for building production-ready microservices.
