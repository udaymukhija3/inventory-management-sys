package com.inventory.service;

import com.inventory.dto.CategoryRequest;
import com.inventory.dto.CategoryResponse;
import com.inventory.exception.CategoryNotFoundException;
import com.inventory.model.Category;
import com.inventory.repository.CategoryRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

public interface CategoryService {
    CategoryResponse createCategory(CategoryRequest request);
    CategoryResponse getCategoryById(Long id);
    CategoryResponse getCategoryByName(String name);
    List<CategoryResponse> getAllCategories();
    List<CategoryResponse> getAllActiveCategories();
    List<CategoryResponse> getCategoriesByParent(Long parentCategoryId);
    List<CategoryResponse> searchCategories(String searchTerm);
    CategoryResponse updateCategory(Long id, CategoryRequest request);
    void deleteCategory(Long id);
}

@Service
class CategoryServiceImpl implements CategoryService {
    
    @Autowired
    private CategoryRepository categoryRepository;
    
    @Override
    @Transactional
    @CacheEvict(value = "categories", allEntries = true)
    public CategoryResponse createCategory(CategoryRequest request) {
        // Check if category name already exists
        if (categoryRepository.existsByName(request.getName())) {
            throw new IllegalArgumentException("Category with name " + request.getName() + " already exists");
        }
        
        Category category = Category.builder()
                .name(request.getName())
                .description(request.getDescription())
                .isActive(request.getIsActive() != null ? request.getIsActive() : true)
                .build();
        
        // Set parent category if provided
        if (request.getParentCategoryId() != null) {
            Category parentCategory = categoryRepository.findById(request.getParentCategoryId())
                    .orElseThrow(() -> new CategoryNotFoundException(request.getParentCategoryId()));
            category.setParentCategory(parentCategory);
        }
        
        Category saved = categoryRepository.save(category);
        return convertToResponse(saved);
    }
    
    @Override
    @Cacheable(value = "categories", key = "#id")
    public CategoryResponse getCategoryById(Long id) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new CategoryNotFoundException(id));
        return convertToResponse(category);
    }
    
    @Override
    @Cacheable(value = "categories", key = "'name_' + #name")
    public CategoryResponse getCategoryByName(String name) {
        Category category = categoryRepository.findByName(name)
                .orElseThrow(() -> CategoryNotFoundException.byName(name));
        return convertToResponse(category);
    }
    
    @Override
    public List<CategoryResponse> getAllCategories() {
        return categoryRepository.findAll().stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }
    
    @Override
    public List<CategoryResponse> getAllActiveCategories() {
        return categoryRepository.findByIsActiveTrue().stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }
    
    @Override
    public List<CategoryResponse> getCategoriesByParent(Long parentCategoryId) {
        return categoryRepository.findByParentCategoryId(parentCategoryId).stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }
    
    @Override
    public List<CategoryResponse> searchCategories(String searchTerm) {
        return categoryRepository.searchCategories(searchTerm).stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }
    
    @Override
    @Transactional
    @CacheEvict(value = "categories", key = "#id")
    public CategoryResponse updateCategory(Long id, CategoryRequest request) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new CategoryNotFoundException(id));
        
        // Check if name is being changed and if new name already exists
        if (!category.getName().equals(request.getName()) && categoryRepository.existsByName(request.getName())) {
            throw new IllegalArgumentException("Category with name " + request.getName() + " already exists");
        }
        
        category.setName(request.getName());
        category.setDescription(request.getDescription());
        category.setIsActive(request.getIsActive() != null ? request.getIsActive() : category.getIsActive());
        
        // Update parent category if provided
        if (request.getParentCategoryId() != null) {
            Category parentCategory = categoryRepository.findById(request.getParentCategoryId())
                    .orElseThrow(() -> new CategoryNotFoundException(request.getParentCategoryId()));
            category.setParentCategory(parentCategory);
        } else if (request.getParentCategoryId() == null && category.getParentCategory() != null) {
            category.setParentCategory(null);
        }
        
        Category updated = categoryRepository.save(category);
        return convertToResponse(updated);
    }
    
    @Override
    @Transactional
    @CacheEvict(value = "categories", key = "#id")
    public void deleteCategory(Long id) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new CategoryNotFoundException(id));
        category.setIsActive(false);
        categoryRepository.save(category);
    }
    
    private CategoryResponse convertToResponse(Category category) {
        CategoryResponse response = new CategoryResponse();
        response.setId(category.getId());
        response.setName(category.getName());
        response.setDescription(category.getDescription());
        response.setIsActive(category.getIsActive());
        response.setCreatedAt(category.getCreatedAt());
        response.setUpdatedAt(category.getUpdatedAt());
        
        if (category.getParentCategory() != null) {
            response.setParentCategoryId(category.getParentCategory().getId());
            response.setParentCategoryName(category.getParentCategory().getName());
        }
        
        return response;
    }
}

