package com.inventory.service;

import com.inventory.dto.AdjustmentRequest;
import com.inventory.dto.InventoryResponse;
import com.inventory.exception.InventoryNotFoundException;
import com.inventory.model.InventoryItem;
import com.inventory.model.InventoryTransaction;
import com.inventory.repository.InventoryRepository;
import com.inventory.repository.TransactionRepository;
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
        private TransactionRepository transactionRepository;

        @Mock
        private InventoryEventPublisher eventPublisher;

        @Mock
        private RedisInventoryCache redisCache;

        @InjectMocks
        private InventoryService inventoryService;

        @BeforeEach
        void setUp() {
                MockitoAnnotations.openMocks(this);
        }

        @Test
        void testAdjustInventory_Success() {
                // Given
                InventoryItem item = InventoryItem.builder()
                                .sku("SKU001")
                                .warehouseId("WH001")
                                .quantityOnHand(100)
                                .quantityReserved(0)
                                .quantityInTransit(0)
                                .reorderPoint(10)
                                .build();

                AdjustmentRequest request = new AdjustmentRequest();
                request.setSku("SKU001");
                request.setWarehouseId("WH001");
                request.setQuantityChange(-10);
                request.setReason("Test adjustment");

                when(inventoryRepository.findBySkuAndWarehouseIdWithLock("SKU001", "WH001"))
                                .thenReturn(Optional.of(item));
                when(inventoryRepository.save(any(InventoryItem.class))).thenReturn(item);
                when(transactionRepository.save(any(InventoryTransaction.class)))
                                .thenReturn(new InventoryTransaction());

                // When
                InventoryResponse response = inventoryService.adjustInventory(request);

                // Then
                assertEquals(90, item.getQuantityOnHand());
                assertNotNull(response);
                assertEquals("SKU001", response.getSku());
                verify(eventPublisher, times(1)).publishEvent(any());
                verify(redisCache, times(1)).updateInventory(item);
                verify(transactionRepository, times(1)).save(any(InventoryTransaction.class));
        }

        @Test
        void testAdjustInventory_NegativeResult_ThrowsException() {
                // Given
                InventoryItem item = InventoryItem.builder()
                                .sku("SKU001")
                                .warehouseId("WH001")
                                .quantityOnHand(10)
                                .quantityReserved(0)
                                .quantityInTransit(0)
                                .reorderPoint(5)
                                .build();

                AdjustmentRequest request = new AdjustmentRequest();
                request.setSku("SKU001");
                request.setWarehouseId("WH001");
                request.setQuantityChange(-20);

                when(inventoryRepository.findBySkuAndWarehouseIdWithLock("SKU001", "WH001"))
                                .thenReturn(Optional.of(item));

                // When/Then
                assertThrows(IllegalArgumentException.class, () -> {
                        inventoryService.adjustInventory(request);
                });

                verify(transactionRepository, never()).save(any());
                verify(eventPublisher, never()).publishEvent(any());
        }

        @Test
        void testAdjustInventory_ItemNotFound_ThrowsException() {
                // Given
                AdjustmentRequest request = new AdjustmentRequest();
                request.setSku("NONEXISTENT");
                request.setWarehouseId("WH001");
                request.setQuantityChange(10);

                when(inventoryRepository.findBySkuAndWarehouseIdWithLock("NONEXISTENT", "WH001"))
                                .thenReturn(Optional.empty());

                // When/Then
                assertThrows(InventoryNotFoundException.class, () -> {
                        inventoryService.adjustInventory(request);
                });
        }

        @Test
        void testGetInventory_Success() {
                // Given
                InventoryItem item = InventoryItem.builder()
                                .id(1L)
                                .sku("SKU001")
                                .warehouseId("WH001")
                                .quantityOnHand(100)
                                .quantityReserved(10)
                                .quantityInTransit(5)
                                .reorderPoint(20)
                                .reorderQuantity(50)
                                .build();

                when(inventoryRepository.findBySkuAndWarehouseId("SKU001", "WH001"))
                                .thenReturn(Optional.of(item));

                // When
                InventoryResponse response = inventoryService.getInventory("SKU001", "WH001");

                // Then
                assertNotNull(response);
                assertEquals("SKU001", response.getSku());
                assertEquals("WH001", response.getWarehouseId());
                assertEquals(100, response.getQuantityOnHand());
                assertEquals(10, response.getQuantityReserved());
                assertEquals(90, response.getAvailableQuantity()); // 100 - 10
        }

        @Test
        void testReserveInventory_Success() {
                // Given
                InventoryItem item = InventoryItem.builder()
                                .sku("SKU001")
                                .warehouseId("WH001")
                                .quantityOnHand(100)
                                .quantityReserved(0)
                                .quantityInTransit(0)
                                .reorderPoint(10)
                                .build();

                when(inventoryRepository.findBySkuAndWarehouseIdWithLock("SKU001", "WH001"))
                                .thenReturn(Optional.of(item));
                when(inventoryRepository.save(any(InventoryItem.class))).thenReturn(item);
                when(transactionRepository.save(any(InventoryTransaction.class)))
                                .thenReturn(new InventoryTransaction());

                // When
                inventoryService.reserveInventory("SKU001", "WH001", 20);

                // Then
                assertEquals(20, item.getQuantityReserved());
                assertEquals(80, item.getAvailableQuantity());
                verify(eventPublisher, times(1)).publishEvent(any());
                verify(redisCache, times(1)).updateInventory(item);
        }

        @Test
        void testReserveInventory_InsufficientStock_ThrowsException() {
                // Given
                InventoryItem item = InventoryItem.builder()
                                .sku("SKU001")
                                .warehouseId("WH001")
                                .quantityOnHand(10)
                                .quantityReserved(0)
                                .quantityInTransit(0)
                                .reorderPoint(5)
                                .build();

                when(inventoryRepository.findBySkuAndWarehouseIdWithLock("SKU001", "WH001"))
                                .thenReturn(Optional.of(item));

                // When/Then
                assertThrows(com.inventory.exception.InsufficientInventoryException.class, () -> {
                        inventoryService.reserveInventory("SKU001", "WH001", 20);
                });
        }

        @Test
        void testRecordSale_Success() {
                // Given
                InventoryItem item = InventoryItem.builder()
                                .sku("SKU001")
                                .warehouseId("WH001")
                                .quantityOnHand(100)
                                .quantityReserved(0)
                                .quantityInTransit(0)
                                .reorderPoint(10)
                                .build();

                when(inventoryRepository.findBySkuAndWarehouseIdWithLock("SKU001", "WH001"))
                                .thenReturn(Optional.of(item));
                when(inventoryRepository.save(any(InventoryItem.class))).thenReturn(item);
                when(transactionRepository.save(any(InventoryTransaction.class)))
                                .thenReturn(new InventoryTransaction());

                // When
                inventoryService.recordSale("SKU001", "WH001", 15);

                // Then
                assertEquals(85, item.getQuantityOnHand());
                verify(eventPublisher, times(1)).publishEvent(any());
                verify(redisCache, times(1)).updateInventory(item);
        }

        @Test
        void testRecordReceipt_Success() {
                // Given
                InventoryItem item = InventoryItem.builder()
                                .sku("SKU001")
                                .warehouseId("WH001")
                                .quantityOnHand(50)
                                .quantityReserved(0)
                                .quantityInTransit(30)
                                .reorderPoint(10)
                                .build();

                when(inventoryRepository.findBySkuAndWarehouseIdWithLock("SKU001", "WH001"))
                                .thenReturn(Optional.of(item));
                when(inventoryRepository.save(any(InventoryItem.class))).thenReturn(item);
                when(transactionRepository.save(any(InventoryTransaction.class)))
                                .thenReturn(new InventoryTransaction());

                // When
                inventoryService.recordReceipt("SKU001", "WH001", 30);

                // Then
                assertEquals(80, item.getQuantityOnHand());
                assertEquals(0, item.getQuantityInTransit()); // Should be reduced
                verify(eventPublisher, times(1)).publishEvent(any());
                verify(redisCache, times(1)).updateInventory(item);
        }

        @Test
        void testReleaseReservation_Success() {
                // Given
                InventoryItem item = InventoryItem.builder()
                                .sku("SKU001")
                                .warehouseId("WH001")
                                .quantityOnHand(100)
                                .quantityReserved(20)
                                .quantityInTransit(0)
                                .reorderPoint(10)
                                .build();

                when(inventoryRepository.findBySkuAndWarehouseIdWithLock("SKU001", "WH001"))
                                .thenReturn(Optional.of(item));
                when(inventoryRepository.save(any(InventoryItem.class))).thenReturn(item);
                when(transactionRepository.save(any(InventoryTransaction.class)))
                                .thenReturn(new InventoryTransaction());

                // When
                inventoryService.releaseReservation("SKU001", "WH001", 10);

                // Then
                assertEquals(10, item.getQuantityReserved());
                assertEquals(90, item.getAvailableQuantity());
                verify(eventPublisher, times(1)).publishEvent(any());
                verify(redisCache, times(1)).updateInventory(item);
        }
}
