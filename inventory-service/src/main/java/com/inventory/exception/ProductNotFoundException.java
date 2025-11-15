package com.inventory.exception;

public class ProductNotFoundException extends RuntimeException {
    public ProductNotFoundException(String message) {
        super(message);
    }
    
    public ProductNotFoundException(Long id) {
        super(String.format("Product not found with ID: %d", id));
    }
    
    public static ProductNotFoundException bySku(String sku) {
        return new ProductNotFoundException(String.format("Product not found with SKU: %s", sku));
    }
}

