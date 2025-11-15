#!/bin/bash

# Seed data script for demonstration
# This script populates the database with sample data using API endpoints

set -e

echo "Seeding database with sample data..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed"
    echo "Please install Python3 to use this script"
    exit 1
fi

# Check if requests library is available
if ! python3 -c "import requests" 2>/dev/null; then
    echo "Error: Python requests library is not installed"
    echo "Please install it: pip install requests"
    exit 1
fi

# Use Python script for better API response handling
if [ -f "scripts/seed-data-api.py" ]; then
    python3 scripts/seed-data-api.py
else
    echo "Error: seed-data-api.py not found"
    echo "Please make sure you're running this from the project root directory"
    exit 1
fi
