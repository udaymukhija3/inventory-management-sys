#!/bin/bash

echo "Setting up Inventory Management System..."

# Create necessary directories
mkdir -p analytics-service/models
mkdir -p logs

# Set up environment variables
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please update with your configuration."
fi

# Build Docker images
echo "Building Docker images..."
docker-compose build

echo "Setup complete!"

