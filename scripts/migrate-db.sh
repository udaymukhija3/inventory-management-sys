#!/bin/bash

echo "Running database migrations..."

# PostgreSQL migrations
psql -h localhost -U inventory_user -d inventory -f infrastructure/docker/postgres/init.sql

# MongoDB initialization
mongo < infrastructure/docker/mongodb/init-mongo.js

echo "Database migrations complete!"

