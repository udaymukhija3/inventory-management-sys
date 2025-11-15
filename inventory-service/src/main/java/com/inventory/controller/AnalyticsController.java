package com.inventory.controller;

import com.inventory.service.AnalyticsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/analytics")
@Tag(name = "Analytics", description = "Inventory analytics and reporting APIs")
public class AnalyticsController {
    
    @Autowired
    private AnalyticsService analyticsService;
    
    @GetMapping("/velocity/{sku}/{warehouseId}")
    @Operation(summary = "Calculate inventory velocity")
    public ResponseEntity<Map<String, Object>> calculateInventoryVelocity(
            @PathVariable String sku,
            @PathVariable String warehouseId,
            @RequestParam(defaultValue = "30") int periodDays) {
        Map<String, Object> result = analyticsService.calculateInventoryVelocity(sku, warehouseId, periodDays);
        return ResponseEntity.ok(result);
    }
    
    @GetMapping("/turnover/{sku}/{warehouseId}")
    @Operation(summary = "Calculate inventory turnover rate")
    public ResponseEntity<Map<String, Object>> calculateTurnoverRate(
            @PathVariable String sku,
            @PathVariable String warehouseId,
            @RequestParam(defaultValue = "30") int periodDays) {
        Map<String, Object> result = analyticsService.calculateTurnoverRate(sku, warehouseId, periodDays);
        return ResponseEntity.ok(result);
    }
    
    @GetMapping("/low-stock")
    @Operation(summary = "Get low stock report")
    public ResponseEntity<Map<String, Object>> getLowStockReport(
            @RequestParam(required = false) Integer threshold) {
        Map<String, Object> result = analyticsService.getLowStockReport(threshold);
        return ResponseEntity.ok(result);
    }
    
    @GetMapping("/warehouse/{warehouseId}/summary")
    @Operation(summary = "Get warehouse inventory summary")
    public ResponseEntity<Map<String, Object>> getWarehouseInventorySummary(@PathVariable String warehouseId) {
        Map<String, Object> result = analyticsService.getWarehouseInventorySummary(warehouseId);
        return ResponseEntity.ok(result);
    }
    
    @GetMapping("/sales-trends/{sku}/{warehouseId}")
    @Operation(summary = "Get sales trends")
    public ResponseEntity<Map<String, Object>> getSalesTrends(
            @PathVariable String sku,
            @PathVariable String warehouseId,
            @RequestParam(defaultValue = "MONTH") String period) {
        Map<String, Object> result = analyticsService.getSalesTrends(sku, warehouseId, period);
        return ResponseEntity.ok(result);
    }
    
    @GetMapping("/status-summary")
    @Operation(summary = "Get inventory status summary")
    public ResponseEntity<Map<String, Object>> getInventoryStatusSummary() {
        Map<String, Object> result = analyticsService.getInventoryStatusSummary();
        return ResponseEntity.ok(result);
    }
}

