package com.inventory.service;

import com.inventory.event.InventoryEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class InventoryEventPublisher {
    
    @Autowired
    private KafkaTemplate<String, InventoryEvent> kafkaTemplate;
    
    @Value("${spring.kafka.topic.inventory-events:inventory-events}")
    private String topic;
    
    public void publishEvent(InventoryEvent event) {
        String key = event.getSku() + "_" + event.getWarehouse();
        kafkaTemplate.send(topic, key, event);
    }
}

