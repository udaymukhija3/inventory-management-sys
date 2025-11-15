package com.inventory.controller;

import com.inventory.dto.CategoryRequest;
import com.inventory.dto.CategoryResponse;
import com.inventory.service.CategoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/categories")
@Tag(name = "Categories", description = "Category management APIs")
public class CategoryController {
    
    @Autowired
    private CategoryService categoryService;
    
    @PostMapping
    @Operation(summary = "Create a new category")
    public ResponseEntity<CategoryResponse> createCategory(@Valid @RequestBody CategoryRequest request) {
        CategoryResponse response = categoryService.createCategory(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
    
    @GetMapping("/{id}")
    @Operation(summary = "Get category by ID")
    public ResponseEntity<CategoryResponse> getCategoryById(@PathVariable Long id) {
        CategoryResponse response = categoryService.getCategoryById(id);
        return ResponseEntity.ok(response);
    }
    
    @GetMapping("/name/{name}")
    @Operation(summary = "Get category by name")
    public ResponseEntity<CategoryResponse> getCategoryByName(@PathVariable String name) {
        CategoryResponse response = categoryService.getCategoryByName(name);
        return ResponseEntity.ok(response);
    }
    
    @GetMapping
    @Operation(summary = "Get all categories")
    public ResponseEntity<List<CategoryResponse>> getAllCategories() {
        List<CategoryResponse> categories = categoryService.getAllCategories();
        return ResponseEntity.ok(categories);
    }
    
    @GetMapping("/active")
    @Operation(summary = "Get all active categories")
    public ResponseEntity<List<CategoryResponse>> getAllActiveCategories() {
        List<CategoryResponse> categories = categoryService.getAllActiveCategories();
        return ResponseEntity.ok(categories);
    }
    
    @GetMapping("/parent/{parentCategoryId}")
    @Operation(summary = "Get categories by parent")
    public ResponseEntity<List<CategoryResponse>> getCategoriesByParent(@PathVariable Long parentCategoryId) {
        List<CategoryResponse> categories = categoryService.getCategoriesByParent(parentCategoryId);
        return ResponseEntity.ok(categories);
    }
    
    @GetMapping("/search")
    @Operation(summary = "Search categories")
    public ResponseEntity<List<CategoryResponse>> searchCategories(@RequestParam String searchTerm) {
        List<CategoryResponse> categories = categoryService.searchCategories(searchTerm);
        return ResponseEntity.ok(categories);
    }
    
    @PutMapping("/{id}")
    @Operation(summary = "Update a category")
    public ResponseEntity<CategoryResponse> updateCategory(
            @PathVariable Long id,
            @Valid @RequestBody CategoryRequest request) {
        CategoryResponse response = categoryService.updateCategory(id, request);
        return ResponseEntity.ok(response);
    }
    
    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a category (soft delete)")
    public ResponseEntity<Void> deleteCategory(@PathVariable Long id) {
        categoryService.deleteCategory(id);
        return ResponseEntity.noContent().build();
    }
}

