package com.inventory.service;

import com.inventory.event.InventoryEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;

/**
 * No-op event publisher for cloud deployments where Kafka is not available.
 * Logs events instead of publishing to a message broker.
 */
@Service
@ConditionalOnProperty(name = "kafka.enabled", havingValue = "false")
public class NoOpInventoryEventPublisher implements InventoryEventPublisher {

    private static final Logger logger = LoggerFactory.getLogger(NoOpInventoryEventPublisher.class);

    @Override
    public void publishEvent(InventoryEvent event) {
        logger.info("Event published (no-op): type={}, sku={}, warehouse={}, quantityChange={}",
                event.getEventType(), event.getSku(), event.getWarehouse(), event.getQuantityChange());
    }
}
