# Airflow Connections Setup

This document describes the Airflow connections that need to be configured for the inventory management DAGs.

## Required Connections

### 1. PostgreSQL Connection (`inventory_db`)

**Connection Type:** Postgres
**Host:** postgres (or localhost if running locally)
**Schema:** inventory
**Login:** inventory_user
**Password:** inventory_pass
**Port:** 5432

**Setup in Airflow UI:**
1. Go to Admin > Connections
2. Click "+" to add new connection
3. Connection Id: `inventory_db`
4. Connection Type: `Postgres`
5. Fill in the connection details above

### 2. HTTP Connection (`analytics_service`)

**Connection Type:** HTTP
**Host:** analytics-service (or localhost if running locally)
**Port:** 8000
**Schema:** http:// (or https://)

**Setup in Airflow UI:**
1. Go to Admin > Connections
2. Click "+" to add new connection
3. Connection Id: `analytics_service`
4. Connection Type: `HTTP`
5. Host: `analytics-service` (or `localhost`)
6. Port: `8000`

## Airflow Variables

### ANALYTICS_SERVICE_URL

**Variable Key:** `ANALYTICS_SERVICE_URL`
**Default Value:** `http://analytics-service:8000`

**Setup in Airflow UI:**
1. Go to Admin > Variables
2. Click "+" to add new variable
3. Key: `ANALYTICS_SERVICE_URL`
4. Val: `http://analytics-service:8000`

## Quick Setup Script

You can also set these up programmatically:

```python
from airflow.models import Connection
from airflow import settings

# PostgreSQL connection
postgres_conn = Connection(
    conn_id='inventory_db',
    conn_type='postgres',
    host='postgres',
    login='inventory_user',
    password='inventory_pass',
    schema='inventory',
    port=5432
)

# HTTP connection
http_conn = Connection(
    conn_id='analytics_service',
    conn_type='http',
    host='analytics-service',
    port=8000
)

session = settings.Session()
session.add(postgres_conn)
session.add(http_conn)
session.commit()
```

