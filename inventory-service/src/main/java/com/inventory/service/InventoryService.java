package com.inventory.service;

import com.inventory.dto.AdjustmentRequest;
import com.inventory.dto.InventoryResponse;
import com.inventory.event.EventType;
import com.inventory.event.InventoryEvent;
import com.inventory.exception.InsufficientInventoryException;
import com.inventory.exception.InventoryNotFoundException;
import com.inventory.model.InventoryItem;
import com.inventory.model.InventoryTransaction;
import com.inventory.repository.InventoryRepository;
import com.inventory.repository.TransactionRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Retryable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Isolation;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Inventory Service with thread-safe operations using pessimistic locking.
 * 
 * All write operations use pessimistic locks to prevent race conditions
 * when multiple threads try to modify the same inventory item concurrently.
 */
@Service
@Slf4j
public class InventoryService {

    @Autowired
    private InventoryRepository inventoryRepository;

    @Autowired
    private TransactionRepository transactionRepository;

    @Autowired
    private InventoryEventPublisher eventPublisher;

    @Autowired
    private RedisInventoryCache redisCache;

    /**
     * Get inventory item (read-only, no lock needed).
     */
    @Cacheable(value = "inventory", key = "#sku + '_' + #warehouseId")
    public InventoryResponse getInventory(String sku, String warehouseId) {
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseId(sku, warehouseId)
                .orElseThrow(() -> new InventoryNotFoundException(sku, warehouseId));
        return convertToResponse(item);
    }

    /**
     * Adjust inventory quantity with pessimistic locking and retry.
     * Uses PESSIMISTIC_WRITE lock to prevent concurrent modifications.
     */
    @Transactional(isolation = Isolation.READ_COMMITTED)
    @CacheEvict(value = "inventory", key = "#request.sku + '_' + #request.warehouseId")
    @Retryable(retryFor = { Exception.class }, maxAttempts = 3, backoff = @Backoff(delay = 100, multiplier = 2))
    public InventoryResponse adjustInventory(AdjustmentRequest request) {
        log.debug("Adjusting inventory for SKU: {}, Warehouse: {}, Change: {}",
                request.getSku(), request.getWarehouseId(), request.getQuantityChange());

        // Use pessimistic write lock to prevent concurrent modifications
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseIdWithLock(
                request.getSku(), request.getWarehouseId())
                .orElseThrow(() -> new InventoryNotFoundException(request.getSku(), request.getWarehouseId()));

        // Use business method for adjustment
        item.adjustQuantity(request.getQuantityChange());
        inventoryRepository.save(item);

        // Create transaction record
        InventoryTransaction transaction = new InventoryTransaction();
        transaction.setSku(request.getSku());
        transaction.setWarehouseId(request.getWarehouseId());
        transaction.setQuantityChange(request.getQuantityChange());
        transaction.setTransactionType(InventoryTransaction.TransactionType.ADJUSTMENT);
        transaction.setNotes(request.getReason());
        transaction.setInventoryItem(item);
        transactionRepository.save(transaction);

        // Publish event (after DB commit via @Transactional)
        InventoryEvent event = new InventoryEvent(
                request.getSku(),
                request.getWarehouseId(),
                request.getQuantityChange(),
                EventType.INVENTORY_UPDATED);
        eventPublisher.publishEvent(event);

        // Update cache
        redisCache.updateInventory(item);

        log.info("Adjusted inventory for SKU: {} in warehouse: {} by {} units",
                request.getSku(), request.getWarehouseId(), request.getQuantityChange());

        return convertToResponse(item);
    }

    /**
     * Reserve inventory with pessimistic locking.
     * Prevents overselling by locking the row during the reservation check.
     */
    @Transactional(isolation = Isolation.READ_COMMITTED)
    @Retryable(retryFor = { Exception.class }, maxAttempts = 3, backoff = @Backoff(delay = 100, multiplier = 2))
    public InventoryResponse reserveInventory(String sku, String warehouseId, Integer quantity) {
        log.debug("Reserving {} units for SKU: {}, Warehouse: {}", quantity, sku, warehouseId);

        if (quantity <= 0) {
            throw new IllegalArgumentException("Quantity must be positive");
        }

        // Use pessimistic write lock
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseIdWithLock(sku, warehouseId)
                .orElseThrow(() -> new InventoryNotFoundException(sku, warehouseId));

        // Check availability before reserving
        if (item.getAvailableQuantity() < quantity) {
            throw new InsufficientInventoryException(
                    String.format("Insufficient inventory for SKU %s: requested %d, available %d",
                            sku, quantity, item.getAvailableQuantity()));
        }

        // Use business method for reservation
        item.reserve(quantity);
        inventoryRepository.save(item);

        // Create transaction
        InventoryTransaction transaction = new InventoryTransaction();
        transaction.setSku(sku);
        transaction.setWarehouseId(warehouseId);
        transaction.setQuantityChange(-quantity);
        transaction.setTransactionType(InventoryTransaction.TransactionType.RESERVATION);
        transaction.setInventoryItem(item);
        transactionRepository.save(transaction);

        // Publish event
        InventoryEvent event = new InventoryEvent(sku, warehouseId, -quantity, EventType.RESERVED);
        eventPublisher.publishEvent(event);

        // Update cache
        redisCache.updateInventory(item);

        log.info("Reserved {} units for SKU: {} in warehouse: {}", quantity, sku, warehouseId);

        return convertToResponse(item);
    }

    /**
     * Release a reservation with pessimistic locking.
     */
    @Transactional(isolation = Isolation.READ_COMMITTED)
    @Retryable(retryFor = { Exception.class }, maxAttempts = 3, backoff = @Backoff(delay = 100, multiplier = 2))
    public InventoryResponse releaseReservation(String sku, String warehouseId, Integer quantity) {
        log.debug("Releasing {} reserved units for SKU: {}, Warehouse: {}", quantity, sku, warehouseId);

        // Use pessimistic write lock
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseIdWithLock(sku, warehouseId)
                .orElseThrow(() -> new InventoryNotFoundException(sku, warehouseId));

        item.releaseReservation(quantity);
        inventoryRepository.save(item);

        // Create transaction
        InventoryTransaction transaction = new InventoryTransaction();
        transaction.setSku(sku);
        transaction.setWarehouseId(warehouseId);
        transaction.setQuantityChange(quantity);
        transaction.setTransactionType(InventoryTransaction.TransactionType.RELEASE);
        transaction.setInventoryItem(item);
        transactionRepository.save(transaction);

        // Publish event
        InventoryEvent event = new InventoryEvent(sku, warehouseId, quantity, EventType.RELEASED);
        eventPublisher.publishEvent(event);

        // Update cache
        redisCache.updateInventory(item);

        log.info("Released {} reserved units for SKU: {} in warehouse: {}", quantity, sku, warehouseId);

        return convertToResponse(item);
    }

    /**
     * Record a sale with pessimistic locking.
     */
    @Transactional(isolation = Isolation.READ_COMMITTED)
    @Retryable(retryFor = { Exception.class }, maxAttempts = 3, backoff = @Backoff(delay = 100, multiplier = 2))
    public InventoryResponse recordSale(String sku, String warehouseId, Integer quantity) {
        log.debug("Recording sale of {} units for SKU: {}, Warehouse: {}", quantity, sku, warehouseId);

        // Use pessimistic write lock
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseIdWithLock(sku, warehouseId)
                .orElseThrow(() -> new InventoryNotFoundException(sku, warehouseId));

        item.recordSale(quantity);
        inventoryRepository.save(item);

        // Create transaction
        InventoryTransaction transaction = new InventoryTransaction();
        transaction.setSku(sku);
        transaction.setWarehouseId(warehouseId);
        transaction.setQuantityChange(-quantity);
        transaction.setTransactionType(InventoryTransaction.TransactionType.SALE);
        transaction.setInventoryItem(item);
        transactionRepository.save(transaction);

        // Publish event
        InventoryEvent event = new InventoryEvent(sku, warehouseId, -quantity, EventType.INVENTORY_UPDATED);
        eventPublisher.publishEvent(event);

        // Update cache
        redisCache.updateInventory(item);

        log.info("Recorded sale of {} units for SKU: {} in warehouse: {}", quantity, sku, warehouseId);

        return convertToResponse(item);
    }

    /**
     * Record inventory receipt (restock) with pessimistic locking.
     */
    @Transactional(isolation = Isolation.READ_COMMITTED)
    @Retryable(retryFor = { Exception.class }, maxAttempts = 3, backoff = @Backoff(delay = 100, multiplier = 2))
    public InventoryResponse recordReceipt(String sku, String warehouseId, Integer quantity) {
        log.debug("Recording receipt of {} units for SKU: {}, Warehouse: {}", quantity, sku, warehouseId);

        // Use pessimistic write lock
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseIdWithLock(sku, warehouseId)
                .orElseThrow(() -> new InventoryNotFoundException(sku, warehouseId));

        item.recordReceipt(quantity);
        inventoryRepository.save(item);

        // Create transaction
        InventoryTransaction transaction = new InventoryTransaction();
        transaction.setSku(sku);
        transaction.setWarehouseId(warehouseId);
        transaction.setQuantityChange(quantity);
        transaction.setTransactionType(InventoryTransaction.TransactionType.RESTOCK);
        transaction.setInventoryItem(item);
        transactionRepository.save(transaction);

        // Publish event
        InventoryEvent event = new InventoryEvent(sku, warehouseId, quantity, EventType.RESTOCKED);
        eventPublisher.publishEvent(event);

        // Update cache
        redisCache.updateInventory(item);

        log.info("Recorded receipt of {} units for SKU: {} in warehouse: {}", quantity, sku, warehouseId);

        return convertToResponse(item);
    }

    /**
     * Get low stock items (read-only).
     */
    public List<InventoryResponse> getLowStockItems(Integer threshold) {
        return inventoryRepository.findLowStockItems(threshold)
                .stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }

    /**
     * Get items needing reorder (read-only).
     */
    public List<InventoryResponse> getItemsNeedingReorder() {
        return inventoryRepository.findItemsNeedingReorder()
                .stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }

    private InventoryResponse convertToResponse(InventoryItem item) {
        InventoryResponse response = new InventoryResponse();
        response.setId(item.getId());
        response.setSku(item.getSku());
        response.setWarehouseId(item.getWarehouseId());
        response.setQuantityOnHand(item.getQuantityOnHand());
        response.setQuantityReserved(item.getQuantityReserved());
        response.setQuantityInTransit(item.getQuantityInTransit());
        response.setAvailableQuantity(item.getAvailableQuantity());
        response.setTotalQuantity(item.getTotalQuantity());
        response.setReorderPoint(item.getReorderPoint());
        response.setReorderQuantity(item.getReorderQuantity());
        response.setUnitCost(item.getUnitCost());
        response.setStatus(item.getStatus());
        response.setCurrentValue(item.getCurrentValue());
        response.setNeedsReorder(item.needsReorder());
        response.setLastStockCheck(item.getLastStockCheck());
        response.setLastReorderDate(item.getLastReorderDate());
        response.setCreatedAt(item.getCreatedAt());
        response.setUpdatedAt(item.getUpdatedAt());
        return response;
    }
}
