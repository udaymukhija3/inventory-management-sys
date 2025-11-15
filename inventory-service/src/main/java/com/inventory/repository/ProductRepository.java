package com.inventory.repository;

import com.inventory.model.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ProductRepository extends JpaRepository<Product, Long>, JpaSpecificationExecutor<Product> {
    
    Optional<Product> findBySku(String sku);
    
    List<Product> findByIsActiveTrue();
    
    Page<Product> findByIsActiveTrue(Pageable pageable);
    
    List<Product> findByCategoryId(Long categoryId);
    
    Page<Product> findByCategoryId(Long categoryId, Pageable pageable);
    
    @Query("SELECT p FROM Product p WHERE p.isActive = true AND " +
           "(LOWER(p.name) LIKE LOWER(CONCAT('%', :searchTerm, '%')) OR " +
           "LOWER(p.sku) LIKE LOWER(CONCAT('%', :searchTerm, '%')))")
    Page<Product> searchProducts(@Param("searchTerm") String searchTerm, Pageable pageable);
    
    @Query("SELECT p FROM Product p WHERE p.isActive = true AND p.category.id = :categoryId")
    Page<Product> findByCategoryIdAndActive(@Param("categoryId") Long categoryId, Pageable pageable);
    
    boolean existsBySku(String sku);
    
    long countByIsActiveTrue();
    
    long countByCategoryId(Long categoryId);
}

