package com.inventory.repository;

import com.inventory.model.InventoryTransaction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface TransactionRepository extends JpaRepository<InventoryTransaction, Long> {
    
    List<InventoryTransaction> findBySkuAndWarehouseId(String sku, String warehouseId);
    
    List<InventoryTransaction> findBySku(String sku);
    
    List<InventoryTransaction> findByWarehouseId(String warehouseId);
    
    @Query("SELECT t FROM InventoryTransaction t WHERE t.timestamp BETWEEN :startDate AND :endDate")
    List<InventoryTransaction> findByDateRange(
        @Param("startDate") LocalDateTime startDate,
        @Param("endDate") LocalDateTime endDate
    );
}

