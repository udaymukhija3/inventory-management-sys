#!/bin/bash

# =============================================================================
# Inventory Management System - Secret Generation Script
# =============================================================================
# This script generates secure random secrets for all services
# Run once to create .env file, then keep .env safe and out of version control
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

echo "🔐 Generating secure secrets for Inventory Management System..."
echo ""

# Check if .env already exists
if [ -f "$ENV_FILE" ]; then
    echo "⚠️  WARNING: .env file already exists at $ENV_FILE"
    read -p "Do you want to overwrite it? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted. Existing .env file preserved."
        exit 0
    fi
    echo ""
fi

# Generate secrets
cat > "$ENV_FILE" << EOF
# =============================================================================
# Inventory Management System - Generated Secrets
# =============================================================================
# Generated: $(date)
# DO NOT COMMIT THIS FILE TO VERSION CONTROL
# =============================================================================

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=inventory
POSTGRES_USER=inventory_user
POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)

# MongoDB
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)
MONGO_DB=inventory_catalog

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=$(openssl rand -base64 20 | tr -d '/+=' | head -c 20)

# =============================================================================
# MESSAGE QUEUE CONFIGURATION
# =============================================================================

KAFKA_BOOTSTRAP_SERVERS=kafka:29092

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# JWT Configuration (minimum 48 chars for HS384/HS512)
JWT_SECRET=$(openssl rand -base64 64 | tr -d '/+=' | head -c 64)
JWT_EXPIRATION=86400000

# Service-to-Service API Key
SERVICE_API_KEY=$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)

# =============================================================================
# AIRFLOW CONFIGURATION
# =============================================================================

AIRFLOW_POSTGRES_USER=airflow
AIRFLOW_POSTGRES_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)
AIRFLOW_POSTGRES_DB=airflow
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)

# =============================================================================
# MONITORING CONFIGURATION
# =============================================================================

GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)

# =============================================================================
# ELASTICSEARCH CONFIGURATION
# =============================================================================

ELASTICSEARCH_HOST=elasticsearch
ELASTICSEARCH_PORT=9200
EOF

echo "✅ Secrets generated successfully!"
echo ""
echo "📁 Environment file created at: $ENV_FILE"
echo ""
echo "⚠️  IMPORTANT NEXT STEPS:"
echo "   1. Review the generated .env file"
echo "   2. Ensure .env is in .gitignore (should already be there)"
echo "   3. Keep a secure backup of these credentials"
echo "   4. Never commit .env to version control"
echo ""
echo "🚀 You can now start the services with: docker-compose up"
