package com.inventory.exception;

public class CategoryNotFoundException extends RuntimeException {
    public CategoryNotFoundException(String message) {
        super(message);
    }
    
    public CategoryNotFoundException(Long id) {
        super(String.format("Category not found with ID: %d", id));
    }
    
    public static CategoryNotFoundException byName(String name) {
        return new CategoryNotFoundException(String.format("Category not found with name: %s", name));
    }
}

