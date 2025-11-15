package com.inventory.controller;

import com.inventory.model.InventoryTransaction;
import com.inventory.service.TransactionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api/v1/transactions")
@Tag(name = "Transactions", description = "Transaction history APIs")
public class TransactionController {
    
    @Autowired
    private TransactionService transactionService;
    
    @GetMapping("/sku/{sku}")
    @Operation(summary = "Get transactions by SKU")
    public ResponseEntity<List<InventoryTransaction>> getTransactionsBySku(@PathVariable String sku) {
        List<InventoryTransaction> transactions = transactionService.getTransactionsBySku(sku);
        return ResponseEntity.ok(transactions);
    }
    
    @GetMapping("/sku/{sku}/warehouse/{warehouseId}")
    @Operation(summary = "Get transactions by SKU and warehouse")
    public ResponseEntity<List<InventoryTransaction>> getTransactionsBySkuAndWarehouse(
            @PathVariable String sku,
            @PathVariable String warehouseId) {
        List<InventoryTransaction> transactions = transactionService.getTransactionsBySkuAndWarehouse(sku, warehouseId);
        return ResponseEntity.ok(transactions);
    }
    
    @GetMapping("/warehouse/{warehouseId}")
    @Operation(summary = "Get transactions by warehouse")
    public ResponseEntity<List<InventoryTransaction>> getTransactionsByWarehouse(@PathVariable String warehouseId) {
        List<InventoryTransaction> transactions = transactionService.getTransactionsByWarehouse(warehouseId);
        return ResponseEntity.ok(transactions);
    }
    
    @GetMapping("/date-range")
    @Operation(summary = "Get transactions by date range")
    public ResponseEntity<List<InventoryTransaction>> getTransactionsByDateRange(
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startDate,
            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endDate) {
        List<InventoryTransaction> transactions = transactionService.getTransactionsByDateRange(startDate, endDate);
        return ResponseEntity.ok(transactions);
    }
}

