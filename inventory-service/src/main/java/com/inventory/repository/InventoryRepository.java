package com.inventory.repository;

import com.inventory.model.InventoryItem;
import com.inventory.model.InventoryItem.InventoryStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import jakarta.persistence.LockModeType;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface InventoryRepository extends JpaRepository<InventoryItem, Long>, JpaSpecificationExecutor<InventoryItem> {
    
    /**
     * Find inventory item with pessimistic lock for updates
     */
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT i FROM InventoryItem i WHERE i.sku = :sku AND i.warehouseId = :warehouseId")
    Optional<InventoryItem> findBySkuAndWarehouseIdWithLock(@Param("sku") String sku, 
                                                            @Param("warehouseId") String warehouseId);
    
    /**
     * Find inventory item for read operations
     */
    Optional<InventoryItem> findBySkuAndWarehouseId(String sku, String warehouseId);
    
    /**
     * Find all items in a specific warehouse
     */
    List<InventoryItem> findByWarehouseId(String warehouseId);
    
    /**
     * Find all items in a specific warehouse with pagination
     */
    Page<InventoryItem> findByWarehouseId(String warehouseId, Pageable pageable);
    
    /**
     * Find all items for a specific SKU across all warehouses
     */
    List<InventoryItem> findBySku(String sku);
    
    /**
     * Find items by status
     */
    List<InventoryItem> findByStatus(InventoryStatus status);
    
    /**
     * Find items by status with pagination
     */
    Page<InventoryItem> findByStatus(InventoryStatus status, Pageable pageable);
    
    /**
     * Find items with specific quantity on hand
     */
    List<InventoryItem> findByQuantityOnHand(Integer quantity);
    
    /**
     * Find items by warehouse and quantity
     */
    List<InventoryItem> findByWarehouseIdAndQuantityOnHand(String warehouseId, Integer quantity);
    
    /**
     * Find low stock items (at or below reorder point)
     */
    @Query("SELECT i FROM InventoryItem i WHERE i.quantityOnHand - i.quantityReserved <= i.reorderPoint")
    List<InventoryItem> findAllLowStockItems();
    
    /**
     * Find low stock items with threshold
     */
    @Query("SELECT i FROM InventoryItem i WHERE (i.quantityOnHand - i.quantityReserved) <= :threshold")
    List<InventoryItem> findLowStockItems(@Param("threshold") Integer threshold);
    
    /**
     * Find low stock items for specific warehouse
     */
    @Query("SELECT i FROM InventoryItem i WHERE i.warehouseId = :warehouseId " +
           "AND i.quantityOnHand - i.quantityReserved <= i.reorderPoint")
    List<InventoryItem> findLowStockItemsByWarehouse(@Param("warehouseId") String warehouseId);
    
    /**
     * Find items needing reorder
     */
    @Query("SELECT i FROM InventoryItem i WHERE (i.quantityOnHand - i.quantityReserved) <= i.reorderPoint")
    List<InventoryItem> findItemsNeedingReorder();
    
    /**
     * Find overstock items (3x above reorder point)
     */
    @Query("SELECT i FROM InventoryItem i WHERE i.quantityOnHand > (i.reorderPoint * 3)")
    List<InventoryItem> findOverstockItems();
    
    /**
     * Calculate total inventory value
     */
    @Query("SELECT SUM(i.quantityOnHand * COALESCE(i.unitCost, 0)) FROM InventoryItem i WHERE i.warehouseId = :warehouseId")
    BigDecimal calculateTotalInventoryValue(@Param("warehouseId") String warehouseId);
    
    /**
     * Find items not updated recently (for cycle counting)
     */
    @Query("SELECT i FROM InventoryItem i WHERE i.lastStockCheck < :cutoffDate OR i.lastStockCheck IS NULL")
    List<InventoryItem> findItemsNeedingStockCheck(@Param("cutoffDate") LocalDateTime cutoffDate);
    
    /**
     * Find items with reservations
     */
    @Query("SELECT i FROM InventoryItem i WHERE i.quantityReserved > 0")
    List<InventoryItem> findItemsWithReservations();
    
    /**
     * Get inventory movement statistics
     */
    @Query(value = "SELECT i.sku, i.warehouse_id, " +
           "COUNT(t.id) as transaction_count, " +
           "SUM(CASE WHEN t.transaction_type = 'SALE' THEN ABS(t.quantity_change) ELSE 0 END) as total_sales, " +
           "AVG(CASE WHEN t.transaction_type = 'SALE' THEN ABS(t.quantity_change) ELSE 0 END) as avg_sale_quantity " +
           "FROM inventory_items i " +
           "LEFT JOIN inventory_transactions t ON i.sku = t.sku AND i.warehouse_id = t.warehouse_id " +
           "WHERE (t.timestamp >= :startDate OR t.timestamp IS NULL) " +
           "GROUP BY i.sku, i.warehouse_id", nativeQuery = true)
    List<Object[]> getInventoryMovementStats(@Param("startDate") LocalDateTime startDate);
    
    /**
     * Find dead stock (no movement in X days)
     */
    @Query(value = "SELECT DISTINCT i.* FROM inventory_items i " +
           "WHERE NOT EXISTS (" +
           "  SELECT 1 FROM inventory_transactions t " +
           "  WHERE t.sku = i.sku AND t.warehouse_id = i.warehouse_id " +
           "  AND t.timestamp >= :cutoffDate" +
           ") AND i.quantity_on_hand > 0 AND i.inventory_status != 'DISCONTINUED'", nativeQuery = true)
    List<InventoryItem> findDeadStock(@Param("cutoffDate") LocalDateTime cutoffDate);
    
    /**
     * Bulk update reorder points based on velocity
     */
    @Modifying
    @Transactional
    @Query("UPDATE InventoryItem i SET i.reorderPoint = :reorderPoint " +
           "WHERE i.sku = :sku AND i.warehouseId = :warehouseId")
    void updateReorderPoint(@Param("sku") String sku, 
                           @Param("warehouseId") String warehouseId, 
                           @Param("reorderPoint") Integer reorderPoint);
}
