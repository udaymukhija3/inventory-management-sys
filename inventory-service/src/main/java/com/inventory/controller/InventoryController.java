package com.inventory.controller;

import com.inventory.dto.AdjustmentRequest;
import com.inventory.dto.InventoryResponse;
import com.inventory.service.InventoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/inventory")
@Tag(name = "Inventory", description = "Inventory management APIs")
public class InventoryController {
    
    @Autowired
    private InventoryService inventoryService;
    
    @GetMapping("/{sku}/{warehouseId}")
    @Operation(summary = "Get inventory by SKU and warehouse")
    public ResponseEntity<InventoryResponse> getInventory(
            @PathVariable String sku,
            @PathVariable String warehouseId) {
        return ResponseEntity.ok(inventoryService.getInventory(sku, warehouseId));
    }
    
    @PostMapping("/adjust")
    @Operation(summary = "Adjust inventory quantity")
    public ResponseEntity<InventoryResponse> adjustInventory(
            @RequestBody AdjustmentRequest request) {
        return ResponseEntity.ok(inventoryService.adjustInventory(request));
    }
    
    @PostMapping("/reserve")
    @Operation(summary = "Reserve inventory")
    public ResponseEntity<InventoryResponse> reserveInventory(
            @RequestParam String sku,
            @RequestParam String warehouseId,
            @RequestParam Integer quantity) {
        return ResponseEntity.ok(inventoryService.reserveInventory(sku, warehouseId, quantity));
    }
    
    @PostMapping("/release")
    @Operation(summary = "Release reserved inventory")
    public ResponseEntity<InventoryResponse> releaseReservation(
            @RequestParam String sku,
            @RequestParam String warehouseId,
            @RequestParam Integer quantity) {
        return ResponseEntity.ok(inventoryService.releaseReservation(sku, warehouseId, quantity));
    }
    
    @PostMapping("/sale")
    @Operation(summary = "Record a sale")
    public ResponseEntity<InventoryResponse> recordSale(
            @RequestParam String sku,
            @RequestParam String warehouseId,
            @RequestParam Integer quantity) {
        return ResponseEntity.ok(inventoryService.recordSale(sku, warehouseId, quantity));
    }
    
    @PostMapping("/receipt")
    @Operation(summary = "Record inventory receipt")
    public ResponseEntity<InventoryResponse> recordReceipt(
            @RequestParam String sku,
            @RequestParam String warehouseId,
            @RequestParam Integer quantity) {
        return ResponseEntity.ok(inventoryService.recordReceipt(sku, warehouseId, quantity));
    }
    
    @GetMapping("/low-stock")
    @Operation(summary = "Get low stock items")
    public ResponseEntity<List<InventoryResponse>> getLowStockItems(
            @RequestParam(defaultValue = "10") Integer threshold) {
        return ResponseEntity.ok(inventoryService.getLowStockItems(threshold));
    }
    
    @GetMapping("/needs-reorder")
    @Operation(summary = "Get items that need reordering")
    public ResponseEntity<List<InventoryResponse>> getItemsNeedingReorder() {
        return ResponseEntity.ok(inventoryService.getItemsNeedingReorder());
    }
}
