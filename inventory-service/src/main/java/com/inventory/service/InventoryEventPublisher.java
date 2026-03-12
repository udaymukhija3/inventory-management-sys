package com.inventory.service;

import com.inventory.event.InventoryEvent;

/**
 * Interface for publishing inventory events.
 * Implementations include Kafka-based publishing and a no-op fallback for cloud deployments.
 */
public interface InventoryEventPublisher {
    void publishEvent(InventoryEvent event);
}
