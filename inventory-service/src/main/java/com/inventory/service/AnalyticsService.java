package com.inventory.service;

import com.inventory.model.InventoryItem;
import com.inventory.model.InventoryTransaction;
import com.inventory.repository.InventoryRepository;
import com.inventory.repository.TransactionRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public interface AnalyticsService {
    Map<String, Object> calculateInventoryVelocity(String sku, String warehouseId, int periodDays);
    Map<String, Object> calculateTurnoverRate(String sku, String warehouseId, int periodDays);
    Map<String, Object> getLowStockReport(Integer threshold);
    Map<String, Object> getWarehouseInventorySummary(String warehouseId);
    Map<String, Object> getSalesTrends(String sku, String warehouseId, String period);
    Map<String, Object> getInventoryStatusSummary();
}

@Service
class AnalyticsServiceImpl implements AnalyticsService {
    
    @Autowired
    private InventoryRepository inventoryRepository;
    
    @Autowired
    private TransactionRepository transactionRepository;
    
    @Override
    public Map<String, Object> calculateInventoryVelocity(String sku, String warehouseId, int periodDays) {
        LocalDateTime endDate = LocalDateTime.now();
        LocalDateTime startDate = endDate.minus(periodDays, ChronoUnit.DAYS);
        
        List<InventoryTransaction> transactions = transactionRepository.findByDateRange(startDate, endDate)
                .stream()
                .filter(t -> t.getSku().equals(sku) && t.getWarehouseId().equals(warehouseId))
                .filter(t -> t.getTransactionType() == InventoryTransaction.TransactionType.SALE ||
                           t.getTransactionType() == InventoryTransaction.TransactionType.RETURN)
                .collect(Collectors.toList());
        
        int totalQuantity = transactions.stream()
                .mapToInt(t -> Math.abs(t.getQuantityChange()))
                .sum();
        
        double velocity = periodDays > 0 ? (double) totalQuantity / periodDays : 0.0;
        
        Map<String, Object> result = new HashMap<>();
        result.put("sku", sku);
        result.put("warehouseId", warehouseId);
        result.put("periodDays", periodDays);
        result.put("totalQuantity", totalQuantity);
        result.put("velocity", Math.round(velocity * 100.0) / 100.0);
        result.put("transactionCount", transactions.size());
        
        // Determine trend
        if (velocity > 10) {
            result.put("trend", "HIGH");
        } else if (velocity > 5) {
            result.put("trend", "MEDIUM");
        } else {
            result.put("trend", "LOW");
        }
        
        return result;
    }
    
    @Override
    public Map<String, Object> calculateTurnoverRate(String sku, String warehouseId, int periodDays) {
        InventoryItem item = inventoryRepository.findBySkuAndWarehouseId(sku, warehouseId)
                .orElse(null);
        
        if (item == null) {
            Map<String, Object> result = new HashMap<>();
            result.put("error", "Inventory item not found");
            return result;
        }
        
        LocalDateTime endDate = LocalDateTime.now();
        LocalDateTime startDate = endDate.minus(periodDays, ChronoUnit.DAYS);
        
        List<InventoryTransaction> salesTransactions = transactionRepository.findByDateRange(startDate, endDate)
                .stream()
                .filter(t -> t.getSku().equals(sku) && t.getWarehouseId().equals(warehouseId))
                .filter(t -> t.getTransactionType() == InventoryTransaction.TransactionType.SALE)
                .collect(Collectors.toList());
        
        int totalSales = salesTransactions.stream()
                .mapToInt(t -> Math.abs(t.getQuantityChange()))
                .sum();
        
        double averageInventory = item.getQuantityOnHand(); // Simplified - could use period average
        double turnoverRate = averageInventory > 0 ? (double) totalSales / averageInventory : 0.0;
        double daysToTurnover = turnoverRate > 0 ? periodDays / turnoverRate : 0.0;
        
        Map<String, Object> result = new HashMap<>();
        result.put("sku", sku);
        result.put("warehouseId", warehouseId);
        result.put("periodDays", periodDays);
        result.put("totalSales", totalSales);
        result.put("averageInventory", averageInventory);
        result.put("turnoverRate", Math.round(turnoverRate * 100.0) / 100.0);
        result.put("daysToTurnover", Math.round(daysToTurnover * 100.0) / 100.0);
        
        return result;
    }
    
    @Override
    public Map<String, Object> getLowStockReport(Integer threshold) {
        List<InventoryItem> lowStockItems = threshold != null ?
                inventoryRepository.findLowStockItems(threshold) :
                inventoryRepository.findAllLowStockItems();
        
        Map<String, Object> result = new HashMap<>();
        result.put("threshold", threshold != null ? threshold : "reorder_point");
        result.put("lowStockCount", lowStockItems.size());
        result.put("items", lowStockItems.stream()
                .map(item -> {
                    Map<String, Object> itemMap = new HashMap<>();
                    itemMap.put("sku", item.getSku());
                    itemMap.put("warehouseId", item.getWarehouseId());
                    itemMap.put("quantityOnHand", item.getQuantityOnHand());
                    itemMap.put("quantityReserved", item.getQuantityReserved());
                    itemMap.put("availableQuantity", item.getAvailableQuantity());
                    itemMap.put("reorderPoint", item.getReorderPoint());
                    itemMap.put("status", item.getStatus());
                    return itemMap;
                })
                .collect(Collectors.toList()));
        
        return result;
    }
    
    @Override
    public Map<String, Object> getWarehouseInventorySummary(String warehouseId) {
        List<InventoryItem> items = inventoryRepository.findByWarehouseId(warehouseId);
        
        int totalItems = items.size();
        int lowStockCount = items.stream()
                .mapToInt(item -> item.needsReorder() ? 1 : 0)
                .sum();
        int outOfStockCount = items.stream()
                .mapToInt(item -> item.getStatus() == InventoryItem.InventoryStatus.OUT_OF_STOCK ? 1 : 0)
                .sum();
        
        double totalValue = items.stream()
                .mapToDouble(item -> item.getCurrentValue().doubleValue())
                .sum();
        
        Map<String, Object> result = new HashMap<>();
        result.put("warehouseId", warehouseId);
        result.put("totalItems", totalItems);
        result.put("lowStockCount", lowStockCount);
        result.put("outOfStockCount", outOfStockCount);
        result.put("totalValue", Math.round(totalValue * 100.0) / 100.0);
        
        return result;
    }
    
    @Override
    public Map<String, Object> getSalesTrends(String sku, String warehouseId, String period) {
        int periodDays = switch (period.toUpperCase()) {
            case "WEEK" -> 7;
            case "MONTH" -> 30;
            case "QUARTER" -> 90;
            default -> 30; // Default to month
        };
        
        LocalDateTime endDate = LocalDateTime.now();
        LocalDateTime startDate = endDate.minus(periodDays, ChronoUnit.DAYS);
        
        List<InventoryTransaction> sales = transactionRepository.findByDateRange(startDate, endDate)
                .stream()
                .filter(t -> t.getSku().equals(sku) && t.getWarehouseId().equals(warehouseId))
                .filter(t -> t.getTransactionType() == InventoryTransaction.TransactionType.SALE)
                .collect(Collectors.toList());
        
        Map<String, Object> result = new HashMap<>();
        result.put("sku", sku);
        result.put("warehouseId", warehouseId);
        result.put("period", period);
        result.put("periodDays", periodDays);
        result.put("totalSales", sales.stream()
                .mapToInt(t -> Math.abs(t.getQuantityChange()))
                .sum());
        result.put("transactionCount", sales.size());
        result.put("averageSaleQuantity", sales.isEmpty() ? 0 : 
                sales.stream().mapToInt(t -> Math.abs(t.getQuantityChange())).sum() / sales.size());
        
        return result;
    }
    
    @Override
    public Map<String, Object> getInventoryStatusSummary() {
        List<InventoryItem> allItems = inventoryRepository.findAll();
        
        Map<String, Integer> statusCounts = allItems.stream()
                .collect(Collectors.groupingBy(
                        item -> item.getStatus().name(),
                        Collectors.collectingAndThen(Collectors.counting(), Long::intValue)
                ));
        
        Map<String, Object> result = new HashMap<>();
        result.put("totalItems", allItems.size());
        result.put("statusCounts", statusCounts);
        result.put("lowStockItems", inventoryRepository.findAllLowStockItems().size());
        result.put("overstockItems", inventoryRepository.findOverstockItems().size());
        
        return result;
    }
}

