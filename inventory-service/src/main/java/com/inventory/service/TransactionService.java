package com.inventory.service;

import com.inventory.model.InventoryTransaction;
import com.inventory.repository.TransactionRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

public interface TransactionService {
    List<InventoryTransaction> getTransactionsBySku(String sku);
    List<InventoryTransaction> getTransactionsBySkuAndWarehouse(String sku, String warehouseId);
    List<InventoryTransaction> getTransactionsByWarehouse(String warehouseId);
    List<InventoryTransaction> getTransactionsByDateRange(LocalDateTime startDate, LocalDateTime endDate);
}

@Service
class TransactionServiceImpl implements TransactionService {
    
    @Autowired
    private TransactionRepository transactionRepository;
    
    @Override
    public List<InventoryTransaction> getTransactionsBySku(String sku) {
        return transactionRepository.findBySku(sku);
    }
    
    @Override
    public List<InventoryTransaction> getTransactionsBySkuAndWarehouse(String sku, String warehouseId) {
        return transactionRepository.findBySkuAndWarehouseId(sku, warehouseId);
    }
    
    @Override
    public List<InventoryTransaction> getTransactionsByWarehouse(String warehouseId) {
        return transactionRepository.findByWarehouseId(warehouseId);
    }
    
    @Override
    public List<InventoryTransaction> getTransactionsByDateRange(LocalDateTime startDate, LocalDateTime endDate) {
        return transactionRepository.findByDateRange(startDate, endDate);
    }
}

