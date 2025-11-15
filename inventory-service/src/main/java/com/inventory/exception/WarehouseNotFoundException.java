package com.inventory.exception;

public class WarehouseNotFoundException extends RuntimeException {
    public WarehouseNotFoundException(String message) {
        super(message);
    }
    
    public WarehouseNotFoundException(Long id) {
        super(String.format("Warehouse not found with ID: %d", id));
    }
    
    public static WarehouseNotFoundException byWarehouseId(String warehouseId) {
        return new WarehouseNotFoundException(String.format("Warehouse not found with ID: %s", warehouseId));
    }
}

