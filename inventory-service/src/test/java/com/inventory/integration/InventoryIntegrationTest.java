package com.inventory.integration;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("test")
@Disabled("Placeholder integration test until a dedicated docker-backed test profile is added")
class InventoryIntegrationTest {
    
    @Test
    void contextLoads() {
        // Integration test placeholder
    }
}
