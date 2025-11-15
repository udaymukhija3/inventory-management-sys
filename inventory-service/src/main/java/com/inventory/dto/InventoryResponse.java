package com.inventory.dto;

import com.inventory.model.InventoryItem;
import java.math.BigDecimal;
import java.time.LocalDateTime;

public class InventoryResponse {
    private Long id;
    private String sku;
    private String warehouseId;
    private Integer quantityOnHand;
    private Integer quantityReserved;
    private Integer quantityInTransit;
    private Integer availableQuantity;
    private Integer totalQuantity;
    private Integer reorderPoint;
    private Integer reorderQuantity;
    private BigDecimal unitCost;
    private BigDecimal holdingCostPerUnit;
    private BigDecimal stockoutCostPerUnit;
    private BigDecimal currentValue;
    private InventoryItem.InventoryStatus status;
    private Boolean needsReorder;
    private LocalDateTime lastStockCheck;
    private LocalDateTime lastReorderDate;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    
    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getSku() { return sku; }
    public void setSku(String sku) { this.sku = sku; }
    
    public String getWarehouseId() { return warehouseId; }
    public void setWarehouseId(String warehouseId) { this.warehouseId = warehouseId; }
    
    public Integer getQuantityOnHand() { return quantityOnHand; }
    public void setQuantityOnHand(Integer quantityOnHand) { this.quantityOnHand = quantityOnHand; }
    
    public Integer getQuantityReserved() { return quantityReserved; }
    public void setQuantityReserved(Integer quantityReserved) { this.quantityReserved = quantityReserved; }
    
    public Integer getQuantityInTransit() { return quantityInTransit; }
    public void setQuantityInTransit(Integer quantityInTransit) { this.quantityInTransit = quantityInTransit; }
    
    public Integer getAvailableQuantity() { return availableQuantity; }
    public void setAvailableQuantity(Integer availableQuantity) { this.availableQuantity = availableQuantity; }
    
    public Integer getTotalQuantity() { return totalQuantity; }
    public void setTotalQuantity(Integer totalQuantity) { this.totalQuantity = totalQuantity; }
    
    public Integer getReorderPoint() { return reorderPoint; }
    public void setReorderPoint(Integer reorderPoint) { this.reorderPoint = reorderPoint; }
    
    public Integer getReorderQuantity() { return reorderQuantity; }
    public void setReorderQuantity(Integer reorderQuantity) { this.reorderQuantity = reorderQuantity; }
    
    public BigDecimal getUnitCost() { return unitCost; }
    public void setUnitCost(BigDecimal unitCost) { this.unitCost = unitCost; }
    
    public BigDecimal getHoldingCostPerUnit() { return holdingCostPerUnit; }
    public void setHoldingCostPerUnit(BigDecimal holdingCostPerUnit) { this.holdingCostPerUnit = holdingCostPerUnit; }
    
    public BigDecimal getStockoutCostPerUnit() { return stockoutCostPerUnit; }
    public void setStockoutCostPerUnit(BigDecimal stockoutCostPerUnit) { this.stockoutCostPerUnit = stockoutCostPerUnit; }
    
    public BigDecimal getCurrentValue() { return currentValue; }
    public void setCurrentValue(BigDecimal currentValue) { this.currentValue = currentValue; }
    
    public InventoryItem.InventoryStatus getStatus() { return status; }
    public void setStatus(InventoryItem.InventoryStatus status) { this.status = status; }
    
    public Boolean getNeedsReorder() { return needsReorder; }
    public void setNeedsReorder(Boolean needsReorder) { this.needsReorder = needsReorder; }
    
    public LocalDateTime getLastStockCheck() { return lastStockCheck; }
    public void setLastStockCheck(LocalDateTime lastStockCheck) { this.lastStockCheck = lastStockCheck; }
    
    public LocalDateTime getLastReorderDate() { return lastReorderDate; }
    public void setLastReorderDate(LocalDateTime lastReorderDate) { this.lastReorderDate = lastReorderDate; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
