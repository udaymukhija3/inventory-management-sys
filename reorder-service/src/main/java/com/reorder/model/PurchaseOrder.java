package com.reorder.model;

import java.time.LocalDateTime;
import java.util.List;

public class PurchaseOrder {
    private String orderId;
    private String supplierId;
    private List<OrderItem> items;
    private LocalDateTime orderDate;
    private LocalDateTime expectedDeliveryDate;
    private String status;
    
    public static class OrderItem {
        private String sku;
        private Integer quantity;
        private Double unitPrice;
        
        // Getters and Setters
        public String getSku() { return sku; }
        public void setSku(String sku) { this.sku = sku; }
        
        public Integer getQuantity() { return quantity; }
        public void setQuantity(Integer quantity) { this.quantity = quantity; }
        
        public Double getUnitPrice() { return unitPrice; }
        public void setUnitPrice(Double unitPrice) { this.unitPrice = unitPrice; }
    }
    
    // Getters and Setters
    public String getOrderId() { return orderId; }
    public void setOrderId(String orderId) { this.orderId = orderId; }
    
    public String getSupplierId() { return supplierId; }
    public void setSupplierId(String supplierId) { this.supplierId = supplierId; }
    
    public List<OrderItem> getItems() { return items; }
    public void setItems(List<OrderItem> items) { this.items = items; }
    
    public LocalDateTime getOrderDate() { return orderDate; }
    public void setOrderDate(LocalDateTime orderDate) { this.orderDate = orderDate; }
    
    public LocalDateTime getExpectedDeliveryDate() { return expectedDeliveryDate; }
    public void setExpectedDeliveryDate(LocalDateTime expectedDeliveryDate) { this.expectedDeliveryDate = expectedDeliveryDate; }
    
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}

