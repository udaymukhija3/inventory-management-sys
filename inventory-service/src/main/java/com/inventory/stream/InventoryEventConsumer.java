package com.inventory.stream;

import com.inventory.event.EventType;
import com.inventory.event.InventoryEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class InventoryEventConsumer {
    
    private static final Logger logger = LoggerFactory.getLogger(InventoryEventConsumer.class);
    
    // In-memory aggregations for real-time analytics
    private final Map<String, Long> eventCounts = new ConcurrentHashMap<>();
    private final Map<String, Integer> quantityChanges = new ConcurrentHashMap<>();
    
    @KafkaListener(topics = "${spring.kafka.topic.inventory-events:inventory-events}", 
                   groupId = "${spring.kafka.consumer.group-id:inventory-consumer-group}")
    public void consumeInventoryEvent(
            @Payload InventoryEvent event,
            @Header(KafkaHeaders.RECEIVED_KEY) String key,
            Acknowledgment acknowledgment) {
        
        try {
            logger.debug("Received inventory event: {} for key: {}", event.getEventType(), key);
            
            // Process event based on type
            processEvent(event);
            
            // Update real-time aggregations
            updateAggregations(event);
            
            // Log low stock alerts
            if (event.getEventType() == EventType.LOW_STOCK || 
                event.getEventType() == EventType.OUT_OF_STOCK) {
                logger.warn("ALERT: {} - SKU: {}, Warehouse: {}", 
                           event.getEventType(), event.getSku(), event.getWarehouse());
            }
            
            // Acknowledge message processing
            acknowledgment.acknowledge();
            
        } catch (Exception e) {
            logger.error("Error processing inventory event: {}", e.getMessage(), e);
            // In production, you might want to send to a dead letter queue
        }
    }
    
    private void processEvent(InventoryEvent event) {
        String key = event.getSku() + "_" + event.getWarehouse();
        
        switch (event.getEventType()) {
            case INVENTORY_UPDATED:
            case LOW_STOCK:
            case OUT_OF_STOCK:
            case RESTOCKED:
                // Update cache key for inventory lookups
                logger.debug("Processing inventory update for {}", key);
                break;
                
            case RESERVED:
            case RELEASED:
                logger.debug("Processing reservation update for {}", key);
                break;
                
            default:
                logger.debug("Processing event type {} for {}", event.getEventType(), key);
        }
    }
    
    private void updateAggregations(InventoryEvent event) {
        String key = event.getSku() + "_" + event.getWarehouse();
        
        // Update event counts
        eventCounts.merge(key, 1L, Long::sum);
        
        // Update quantity changes aggregation
        quantityChanges.merge(key, Math.abs(event.getQuantityChange()), Integer::sum);
        
        logger.debug("Aggregations updated for key: {}, Event count: {}, Total quantity change: {}", 
                    key, eventCounts.get(key), quantityChanges.get(key));
    }
    
    public Map<String, Long> getEventCounts() {
        return new HashMap<>(eventCounts);
    }
    
    public Map<String, Integer> getQuantityChanges() {
        return new HashMap<>(quantityChanges);
    }
    
    public Map<String, Object> getAggregatedMetrics() {
        Map<String, Object> metrics = new HashMap<>();
        metrics.put("eventCounts", new HashMap<>(eventCounts));
        metrics.put("quantityChanges", new HashMap<>(quantityChanges));
        metrics.put("totalEvents", eventCounts.values().stream().mapToLong(Long::longValue).sum());
        metrics.put("totalQuantityChanged", quantityChanges.values().stream().mapToInt(Integer::intValue).sum());
        return metrics;
    }
}

