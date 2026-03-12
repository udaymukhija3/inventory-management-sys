package com.inventory.service;

import com.inventory.event.InventoryEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
@ConditionalOnProperty(name = "kafka.enabled", havingValue = "true", matchIfMissing = true)
public class KafkaInventoryEventPublisher implements InventoryEventPublisher {

    private static final Logger logger = LoggerFactory.getLogger(KafkaInventoryEventPublisher.class);

    @Autowired
    private KafkaTemplate<String, InventoryEvent> kafkaTemplate;

    @Value("${spring.kafka.topic.inventory-events:inventory-events}")
    private String topic;

    @Override
    public void publishEvent(InventoryEvent event) {
        String key = event.getSku() + "_" + event.getWarehouse();
        logger.debug("Publishing inventory event to Kafka topic {}: {}", topic, event.getEventType());
        kafkaTemplate.send(topic, key, event);
    }
}
