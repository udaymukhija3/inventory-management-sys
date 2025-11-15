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
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class InventoryService {
    
    @Autowired
    private InventoryRepository inventoryRepository;
    
    @Autowired
    private TransactionRepository transactionRepository;
    
    @Autowired
    private InventoryEventPublisher eventPublisher;
    
    @Autowired
    private RedisInventoryCache redisCache;
    
    @Cacheable(value = "inventory", key = "#sku + '_' + #warehouseId")
    public InventoryResponse getInventory(String sku, String warehouseId) {
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseId(sku, warehouseId)
            .orElseThrow(() -> new InventoryNotFoundException(sku, warehouseId));
        return convertToResponse(item);
    }
    
    @Transactional
    @CacheEvict(value = "inventory", key = "#request.sku + '_' + #request.warehouseId")
    public InventoryResponse adjustInventory(AdjustmentRequest request) {
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseId(
            request.getSku(), request.getWarehouseId()
        ).orElseThrow(() -> new InventoryNotFoundException(request.getSku(), request.getWarehouseId()));
        
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
        
        // Publish event
        InventoryEvent event = new InventoryEvent(
            request.getSku(),
            request.getWarehouseId(),
            request.getQuantityChange(),
            EventType.INVENTORY_UPDATED
        );
        eventPublisher.publishEvent(event);
        
        // Update cache
        redisCache.updateInventory(item);
        
        return convertToResponse(item);
    }
    
    @Transactional
    public InventoryResponse reserveInventory(String sku, String warehouseId, Integer quantity) {
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseId(sku, warehouseId)
            .orElseThrow(() -> new InventoryNotFoundException(sku, warehouseId));
        
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
        
        return convertToResponse(item);
    }
    
    @Transactional
    public InventoryResponse releaseReservation(String sku, String warehouseId, Integer quantity) {
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseId(sku, warehouseId)
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
        
        return convertToResponse(item);
    }
    
    @Transactional
    public InventoryResponse recordSale(String sku, String warehouseId, Integer quantity) {
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseId(sku, warehouseId)
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
        
        return convertToResponse(item);
    }
    
    @Transactional
    public InventoryResponse recordReceipt(String sku, String warehouseId, Integer quantity) {
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseId(sku, warehouseId)
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
        
        return convertToResponse(item);
    }
    
    public List<InventoryResponse> getLowStockItems(Integer threshold) {
        return inventoryRepository.findLowStockItems(threshold)
            .stream()
            .map(this::convertToResponse)
            .collect(Collectors.toList());
    }
    
    public List<InventoryResponse> getItemsNeedingReorder() {
        return inventoryRepository.findAll()
            .stream()
            .filter(InventoryItem::needsReorder)
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
