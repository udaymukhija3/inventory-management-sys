package com.inventory.service;

import com.inventory.dto.AdjustmentRequest;
import com.inventory.exception.InsufficientInventoryException;
import com.inventory.model.InventoryItem;
import com.inventory.repository.InventoryRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class InventoryServiceTest {
    
    @Mock
    private InventoryRepository inventoryRepository;
    
    @Mock
    private InventoryEventPublisher eventPublisher;
    
    @InjectMocks
    private InventoryService inventoryService;
    
    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }
    
    @Test
    void testAdjustInventory_Success() {
        // Given
        InventoryItem item = new InventoryItem();
        item.setSku("SKU001");
        item.setWarehouseId("WH001");
        item.setQuantity(100);
        item.setReservedQuantity(0);
        
        AdjustmentRequest request = new AdjustmentRequest();
        request.setSku("SKU001");
        request.setWarehouseId("WH001");
        request.setQuantityChange(-10);
        
        when(inventoryRepository.findBySkuAndWarehouseId("SKU001", "WH001"))
            .thenReturn(Optional.of(item));
        when(inventoryRepository.save(any(InventoryItem.class))).thenReturn(item);
        
        // When
        inventoryService.adjustInventory(request);
        
        // Then
        assertEquals(90, item.getQuantity());
        verify(eventPublisher, times(1)).publishEvent(any());
    }
    
    @Test
    void testAdjustInventory_InsufficientInventory() {
        // Given
        InventoryItem item = new InventoryItem();
        item.setSku("SKU001");
        item.setWarehouseId("WH001");
        item.setQuantity(10);
        item.setReservedQuantity(0);
        
        AdjustmentRequest request = new AdjustmentRequest();
        request.setSku("SKU001");
        request.setWarehouseId("WH001");
        request.setQuantityChange(-20);
        
        when(inventoryRepository.findBySkuAndWarehouseId("SKU001", "WH001"))
            .thenReturn(Optional.of(item));
        
        // When/Then
        assertThrows(InsufficientInventoryException.class, () -> {
            inventoryService.adjustInventory(request);
        });
    }
}

