package com.inventory.event;

import java.time.LocalDateTime;
import java.util.UUID;

public class InventoryEvent {
    private String eventId;
    private String sku;
    private String warehouse;
    private Integer quantityChange;
    private EventType eventType;
    private LocalDateTime timestamp;
    private String referenceId;
    
    public InventoryEvent() {
        this.eventId = UUID.randomUUID().toString();
        this.timestamp = LocalDateTime.now();
    }
    
    public InventoryEvent(String sku, String warehouse, Integer quantityChange, EventType eventType) {
        this();
        this.sku = sku;
        this.warehouse = warehouse;
        this.quantityChange = quantityChange;
        this.eventType = eventType;
    }
    
    // Getters and Setters
    public String getEventId() { return eventId; }
    public void setEventId(String eventId) {
        this.eventId = (eventId == null || eventId.isBlank()) ? UUID.randomUUID().toString() : eventId;
    }
    
    public String getSku() { return sku; }
    public void setSku(String sku) { this.sku = sku; }
    
    public String getWarehouse() { return warehouse; }
    public void setWarehouse(String warehouse) { this.warehouse = warehouse; }
    
    public Integer getQuantityChange() { return quantityChange; }
    public void setQuantityChange(Integer quantityChange) { this.quantityChange = quantityChange; }
    
    public EventType getEventType() { return eventType; }
    public void setEventType(EventType eventType) { this.eventType = eventType; }
    
    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }
    
    public String getReferenceId() { return referenceId; }
    public void setReferenceId(String referenceId) { this.referenceId = referenceId; }
}
