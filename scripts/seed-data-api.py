#!/usr/bin/env python3
"""
Seed data script using API endpoints
This script populates the database with sample data using API calls
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:9000"
INVENTORY_SERVICE = "http://localhost:8080"

def check_service_health():
    """Check if services are running"""
    try:
        response = requests.get(f"{INVENTORY_SERVICE}/actuator/health", timeout=5)
        if response.status_code == 200:
            print("✓ Services are running")
            return True
        else:
            print(f"✗ Services are not healthy: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Services are not running: {e}")
        return False

def create_category(name, description):
    """Create a category"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/categories",
            json={
                "name": name,
                "description": description,
                "isActive": True
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✓ Created category: {name} (ID: {data.get('id', 'N/A')})")
            return data.get('id')
        else:
            print(f"⚠ Category {name} may already exist or error: {response.status_code}")
            # Try to get existing category
            response = requests.get(f"{BASE_URL}/api/v1/categories")
            if response.status_code == 200:
                categories = response.json()
                for cat in categories:
                    if cat.get('name') == name:
                        return cat.get('id')
        return None
    except Exception as e:
        print(f"✗ Error creating category {name}: {e}")
        return None

def create_warehouse(warehouse_id, name, address, city, state, country, postal_code):
    """Create a warehouse"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/warehouses",
            json={
                "warehouseId": warehouse_id,
                "name": name,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "postalCode": postal_code,
                "isActive": True
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✓ Created warehouse: {name} (ID: {data.get('id', 'N/A')})")
            return data.get('id')
        else:
            print(f"⚠ Warehouse {name} may already exist or error: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error creating warehouse {name}: {e}")
        return None

def create_product(sku, name, description, category_id, price):
    """Create a product"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/products",
            json={
                "sku": sku,
                "name": name,
                "description": description,
                "categoryId": category_id,
                "price": price,
                "isActive": True
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✓ Created product: {name} (SKU: {sku})")
            return data.get('id')
        else:
            print(f"⚠ Product {sku} may already exist or error: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error creating product {sku}: {e}")
        return None

def create_inventory_item(sku, warehouse_id, quantity, reorder_point=20, reorder_quantity=30, unit_cost=100.0):
    """Create inventory item by recording a receipt"""
    try:
        # Record receipt to create inventory item
        response = requests.post(
            f"{BASE_URL}/api/v1/inventory/receipt",
            params={
                "sku": sku,
                "warehouseId": warehouse_id,
                "quantity": quantity
            },
            timeout=10
        )
        if response.status_code == 200:
            print(f"✓ Created inventory item: {sku} at {warehouse_id} (Quantity: {quantity})")
            
            # Set reorder point by adjusting inventory
            # Note: This is a simplified approach. In production, you'd have a separate API for setting reorder points
            try:
                adjustment_response = requests.post(
                    f"{BASE_URL}/api/v1/inventory/adjust",
                    json={
                        "sku": sku,
                        "warehouseId": warehouse_id,
                        "quantityChange": 0,  # No quantity change, just updating metadata
                        "reason": "Set reorder point"
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            except:
                pass  # Ignore if adjustment fails
            
            return True
        else:
            print(f"⚠ Inventory item {sku} at {warehouse_id} may already exist or error: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error creating inventory item {sku} at {warehouse_id}: {e}")
        return False

def create_sample_transactions(sku, warehouse_id, count=5):
    """Create sample transactions"""
    try:
        for i in range(count):
            response = requests.post(
                f"{BASE_URL}/api/v1/inventory/sale",
                params={
                    "sku": sku,
                    "warehouseId": warehouse_id,
                    "quantity": 1
                },
                timeout=10
            )
            if response.status_code == 200:
                time.sleep(0.1)  # Small delay between transactions
        print(f"✓ Created {count} sample transactions for {sku} at {warehouse_id}")
        return True
    except Exception as e:
        print(f"✗ Error creating transactions for {sku}: {e}")
        return False

def main():
    """Main function to seed data"""
    print("=========================================")
    print("Seeding database with sample data")
    print("=========================================")
    print("")
    
    # Check if services are running
    if not check_service_health():
        print("\nError: Services are not running. Please start services first:")
        print("  docker-compose up -d")
        sys.exit(1)
    
    print("")
    
    # Create categories
    print("Creating categories...")
    category_computers_id = create_category("Computers", "Computers and laptops")
    category_phones_id = create_category("Phones", "Smartphones and mobile devices")
    category_electronics_id = create_category("Electronics", "Electronic devices and accessories")
    category_accessories_id = create_category("Accessories", "Device accessories")
    print("")
    
    # Create warehouses
    print("Creating warehouses...")
    create_warehouse("WAREHOUSE-001", "Main Warehouse", "123 Main St", "New York", "NY", "USA", "10001")
    create_warehouse("WAREHOUSE-002", "West Coast Warehouse", "456 Oak Ave", "Los Angeles", "CA", "USA", "90001")
    create_warehouse("WAREHOUSE-003", "East Coast Warehouse", "789 Pine Rd", "Boston", "MA", "USA", "02101")
    print("")
    
    # Create products
    print("Creating products...")
    if category_computers_id:
        create_product("LAPTOP-001", "Gaming Laptop", "High-performance gaming laptop with RTX 4070", category_computers_id, 1299.99)
        create_product("LAPTOP-002", "Business Laptop", "Professional business laptop", category_computers_id, 899.99)
    
    if category_phones_id:
        create_product("PHONE-001", "Smartphone Pro", "Latest smartphone with advanced features", category_phones_id, 799.99)
        create_product("PHONE-002", "Budget Smartphone", "Affordable smartphone with great features", category_phones_id, 299.99)
    
    if category_electronics_id:
        create_product("TABLET-001", "Tablet Pro", "High-end tablet device", category_electronics_id, 599.99)
    
    if category_accessories_id:
        create_product("WATCH-001", "Smart Watch", "Feature-rich smartwatch", category_accessories_id, 249.99)
    print("")
    
    # Create inventory items
    print("Creating inventory items...")
    create_inventory_item("LAPTOP-001", "WAREHOUSE-001", 50, 20, 30, 1000.00)
    create_inventory_item("LAPTOP-001", "WAREHOUSE-002", 30, 15, 25, 1000.00)
    create_inventory_item("LAPTOP-002", "WAREHOUSE-001", 40, 15, 20, 700.00)
    create_inventory_item("PHONE-001", "WAREHOUSE-001", 100, 30, 50, 600.00)
    create_inventory_item("PHONE-001", "WAREHOUSE-002", 80, 25, 40, 600.00)
    create_inventory_item("PHONE-002", "WAREHOUSE-001", 150, 40, 60, 200.00)
    create_inventory_item("TABLET-001", "WAREHOUSE-001", 60, 20, 30, 400.00)
    create_inventory_item("WATCH-001", "WAREHOUSE-001", 200, 50, 100, 150.00)
    create_inventory_item("WATCH-001", "WAREHOUSE-002", 120, 30, 60, 150.00)
    print("")
    
    # Create sample transactions
    print("Creating sample transactions...")
    create_sample_transactions("LAPTOP-001", "WAREHOUSE-001", 10)
    create_sample_transactions("PHONE-001", "WAREHOUSE-001", 5)
    create_sample_transactions("WATCH-001", "WAREHOUSE-001", 8)
    print("")
    
    print("=========================================")
    print("Database seeded successfully!")
    print("=========================================")
    print("")
    print("Sample data includes:")
    print("  - 4 categories")
    print("  - 3 warehouses")
    print("  - 6 products")
    print("  - 9 inventory items")
    print("  - Sample transactions")
    print("")
    print("You can now test the API endpoints:")
    print("  curl http://localhost:9000/api/v1/products")
    print("  curl http://localhost:9000/api/v1/inventory/LAPTOP-001/WAREHOUSE-001")
    print("  curl http://localhost:9000/api/v1/analytics/velocity/LAPTOP-001/WAREHOUSE-001?period_days=30")
    print("")

if __name__ == "__main__":
    main()

