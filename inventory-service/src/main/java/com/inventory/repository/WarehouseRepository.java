package com.inventory.repository;

import com.inventory.model.Warehouse;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface WarehouseRepository extends JpaRepository<Warehouse, Long> {
    
    Optional<Warehouse> findByWarehouseId(String warehouseId);
    
    List<Warehouse> findByIsActiveTrue();
    
    @Query("SELECT w FROM Warehouse w WHERE w.isActive = true AND " +
           "(LOWER(w.name) LIKE LOWER(CONCAT('%', :searchTerm, '%')) OR " +
           "LOWER(w.warehouseId) LIKE LOWER(CONCAT('%', :searchTerm, '%')))")
    List<Warehouse> searchWarehouses(@Param("searchTerm") String searchTerm);
    
    boolean existsByWarehouseId(String warehouseId);
    
    long countByIsActiveTrue();
}

