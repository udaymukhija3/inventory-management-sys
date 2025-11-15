package com.inventory.repository;

import com.inventory.model.Category;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface CategoryRepository extends JpaRepository<Category, Long> {
    
    Optional<Category> findByName(String name);
    
    List<Category> findByIsActiveTrue();
    
    List<Category> findByParentCategoryId(Long parentCategoryId);
    
    List<Category> findByParentCategoryIsNull();
    
    @Query("SELECT c FROM Category c WHERE c.isActive = true AND " +
           "LOWER(c.name) LIKE LOWER(CONCAT('%', :searchTerm, '%'))")
    List<Category> searchCategories(@Param("searchTerm") String searchTerm);
    
    boolean existsByName(String name);
    
    long countByIsActiveTrue();
    
    long countByParentCategoryId(Long parentCategoryId);
}

