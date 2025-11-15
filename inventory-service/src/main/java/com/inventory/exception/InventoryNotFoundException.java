package com.inventory.exception;

public class InventoryNotFoundException extends RuntimeException {
    public InventoryNotFoundException(String message) {
        super(message);
    }
    
    public InventoryNotFoundException(String sku, String warehouseId) {
        super(String.format("Inventory item not found for SKU: %s in warehouse: %s", sku, warehouseId));
    }
}

