package com.inventory.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.NotBlank;

public class AdjustmentRequest {
    
    @NotBlank(message = "SKU is required")
    private String sku;
    
    @NotBlank(message = "Warehouse ID is required")
    private String warehouseId;
    
    @NotNull(message = "Quantity change is required")
    private Integer quantityChange;
    
    private String reason;
    
    // Getters and Setters
    public String getSku() { return sku; }
    public void setSku(String sku) { this.sku = sku; }
    
    public String getWarehouseId() { return warehouseId; }
    public void setWarehouseId(String warehouseId) { this.warehouseId = warehouseId; }
    
    public Integer getQuantityChange() { return quantityChange; }
    public void setQuantityChange(Integer quantityChange) { this.quantityChange = quantityChange; }
    
    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }
}

