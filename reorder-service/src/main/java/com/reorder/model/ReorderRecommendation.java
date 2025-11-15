package com.reorder.model;

import java.time.LocalDateTime;

public class ReorderRecommendation {
    private String sku;
    private String warehouseId;
    private Integer currentQuantity;
    private Integer reorderPoint;
    private Integer recommendedQuantity;
    private LocalDateTime recommendedDate;
    private String priority;
    
    // Getters and Setters
    public String getSku() { return sku; }
    public void setSku(String sku) { this.sku = sku; }
    
    public String getWarehouseId() { return warehouseId; }
    public void setWarehouseId(String warehouseId) { this.warehouseId = warehouseId; }
    
    public Integer getCurrentQuantity() { return currentQuantity; }
    public void setCurrentQuantity(Integer currentQuantity) { this.currentQuantity = currentQuantity; }
    
    public Integer getReorderPoint() { return reorderPoint; }
    public void setReorderPoint(Integer reorderPoint) { this.reorderPoint = reorderPoint; }
    
    public Integer getRecommendedQuantity() { return recommendedQuantity; }
    public void setRecommendedQuantity(Integer recommendedQuantity) { this.recommendedQuantity = recommendedQuantity; }
    
    public LocalDateTime getRecommendedDate() { return recommendedDate; }
    public void setRecommendedDate(LocalDateTime recommendedDate) { this.recommendedDate = recommendedDate; }
    
    public String getPriority() { return priority; }
    public void setPriority(String priority) { this.priority = priority; }
}

