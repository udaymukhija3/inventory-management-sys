package com.inventory.controller;

import com.inventory.dto.WarehouseRequest;
import com.inventory.dto.WarehouseResponse;
import com.inventory.service.WarehouseService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/warehouses")
@Tag(name = "Warehouses", description = "Warehouse management APIs")
public class WarehouseController {
    
    @Autowired
    private WarehouseService warehouseService;
    
    @PostMapping
    @Operation(summary = "Create a new warehouse")
    public ResponseEntity<WarehouseResponse> createWarehouse(@Valid @RequestBody WarehouseRequest request) {
        WarehouseResponse response = warehouseService.createWarehouse(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
    
    @GetMapping("/{id}")
    @Operation(summary = "Get warehouse by ID")
    public ResponseEntity<WarehouseResponse> getWarehouseById(@PathVariable Long id) {
        WarehouseResponse response = warehouseService.getWarehouseById(id);
        return ResponseEntity.ok(response);
    }
    
    @GetMapping("/warehouse-id/{warehouseId}")
    @Operation(summary = "Get warehouse by warehouse ID")
    public ResponseEntity<WarehouseResponse> getWarehouseByWarehouseId(@PathVariable String warehouseId) {
        WarehouseResponse response = warehouseService.getWarehouseByWarehouseId(warehouseId);
        return ResponseEntity.ok(response);
    }
    
    @GetMapping
    @Operation(summary = "Get all warehouses")
    public ResponseEntity<List<WarehouseResponse>> getAllWarehouses() {
        List<WarehouseResponse> warehouses = warehouseService.getAllWarehouses();
        return ResponseEntity.ok(warehouses);
    }
    
    @GetMapping("/active")
    @Operation(summary = "Get all active warehouses")
    public ResponseEntity<List<WarehouseResponse>> getAllActiveWarehouses() {
        List<WarehouseResponse> warehouses = warehouseService.getAllActiveWarehouses();
        return ResponseEntity.ok(warehouses);
    }
    
    @GetMapping("/search")
    @Operation(summary = "Search warehouses")
    public ResponseEntity<List<WarehouseResponse>> searchWarehouses(@RequestParam String searchTerm) {
        List<WarehouseResponse> warehouses = warehouseService.searchWarehouses(searchTerm);
        return ResponseEntity.ok(warehouses);
    }
    
    @PutMapping("/{id}")
    @Operation(summary = "Update a warehouse")
    public ResponseEntity<WarehouseResponse> updateWarehouse(
            @PathVariable Long id,
            @Valid @RequestBody WarehouseRequest request) {
        WarehouseResponse response = warehouseService.updateWarehouse(id, request);
        return ResponseEntity.ok(response);
    }
    
    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a warehouse (soft delete)")
    public ResponseEntity<Void> deleteWarehouse(@PathVariable Long id) {
        warehouseService.deleteWarehouse(id);
        return ResponseEntity.noContent().build();
    }
}

