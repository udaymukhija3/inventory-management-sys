package com.inventory.service;

import com.inventory.dto.WarehouseRequest;
import com.inventory.dto.WarehouseResponse;
import com.inventory.exception.WarehouseNotFoundException;
import com.inventory.model.Warehouse;
import com.inventory.repository.WarehouseRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

public interface WarehouseService {
    WarehouseResponse createWarehouse(WarehouseRequest request);
    WarehouseResponse getWarehouseById(Long id);
    WarehouseResponse getWarehouseByWarehouseId(String warehouseId);
    List<WarehouseResponse> getAllWarehouses();
    List<WarehouseResponse> getAllActiveWarehouses();
    List<WarehouseResponse> searchWarehouses(String searchTerm);
    WarehouseResponse updateWarehouse(Long id, WarehouseRequest request);
    void deleteWarehouse(Long id);
}

@Service
class WarehouseServiceImpl implements WarehouseService {
    
    @Autowired
    private WarehouseRepository warehouseRepository;
    
    @Override
    @Transactional
    @CacheEvict(value = "warehouses", allEntries = true)
    public WarehouseResponse createWarehouse(WarehouseRequest request) {
        // Check if warehouse ID already exists
        if (warehouseRepository.existsByWarehouseId(request.getWarehouseId())) {
            throw new IllegalArgumentException("Warehouse with ID " + request.getWarehouseId() + " already exists");
        }
        
        Warehouse warehouse = Warehouse.builder()
                .warehouseId(request.getWarehouseId())
                .name(request.getName())
                .address(request.getAddress())
                .city(request.getCity())
                .state(request.getState())
                .country(request.getCountry())
                .postalCode(request.getPostalCode())
                .isActive(request.getIsActive() != null ? request.getIsActive() : true)
                .build();
        
        Warehouse saved = warehouseRepository.save(warehouse);
        return convertToResponse(saved);
    }
    
    @Override
    @Cacheable(value = "warehouses", key = "#id")
    public WarehouseResponse getWarehouseById(Long id) {
        Warehouse warehouse = warehouseRepository.findById(id)
                .orElseThrow(() -> new WarehouseNotFoundException(id));
        return convertToResponse(warehouse);
    }
    
    @Override
    @Cacheable(value = "warehouses", key = "'id_' + #warehouseId")
    public WarehouseResponse getWarehouseByWarehouseId(String warehouseId) {
        Warehouse warehouse = warehouseRepository.findByWarehouseId(warehouseId)
                .orElseThrow(() -> WarehouseNotFoundException.byWarehouseId(warehouseId));
        return convertToResponse(warehouse);
    }
    
    @Override
    public List<WarehouseResponse> getAllWarehouses() {
        return warehouseRepository.findAll().stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }
    
    @Override
    public List<WarehouseResponse> getAllActiveWarehouses() {
        return warehouseRepository.findByIsActiveTrue().stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }
    
    @Override
    public List<WarehouseResponse> searchWarehouses(String searchTerm) {
        return warehouseRepository.searchWarehouses(searchTerm).stream()
                .map(this::convertToResponse)
                .collect(Collectors.toList());
    }
    
    @Override
    @Transactional
    @CacheEvict(value = "warehouses", key = "#id")
    public WarehouseResponse updateWarehouse(Long id, WarehouseRequest request) {
        Warehouse warehouse = warehouseRepository.findById(id)
                .orElseThrow(() -> new WarehouseNotFoundException(id));
        
        // Check if warehouse ID is being changed and if new ID already exists
        if (!warehouse.getWarehouseId().equals(request.getWarehouseId()) && 
            warehouseRepository.existsByWarehouseId(request.getWarehouseId())) {
            throw new IllegalArgumentException("Warehouse with ID " + request.getWarehouseId() + " already exists");
        }
        
        warehouse.setWarehouseId(request.getWarehouseId());
        warehouse.setName(request.getName());
        warehouse.setAddress(request.getAddress());
        warehouse.setCity(request.getCity());
        warehouse.setState(request.getState());
        warehouse.setCountry(request.getCountry());
        warehouse.setPostalCode(request.getPostalCode());
        warehouse.setIsActive(request.getIsActive() != null ? request.getIsActive() : warehouse.getIsActive());
        
        Warehouse updated = warehouseRepository.save(warehouse);
        return convertToResponse(updated);
    }
    
    @Override
    @Transactional
    @CacheEvict(value = "warehouses", key = "#id")
    public void deleteWarehouse(Long id) {
        Warehouse warehouse = warehouseRepository.findById(id)
                .orElseThrow(() -> new WarehouseNotFoundException(id));
        warehouse.setIsActive(false);
        warehouseRepository.save(warehouse);
    }
    
    private WarehouseResponse convertToResponse(Warehouse warehouse) {
        WarehouseResponse response = new WarehouseResponse();
        response.setId(warehouse.getId());
        response.setWarehouseId(warehouse.getWarehouseId());
        response.setName(warehouse.getName());
        response.setAddress(warehouse.getAddress());
        response.setCity(warehouse.getCity());
        response.setState(warehouse.getState());
        response.setCountry(warehouse.getCountry());
        response.setPostalCode(warehouse.getPostalCode());
        response.setIsActive(warehouse.getIsActive());
        response.setCreatedAt(warehouse.getCreatedAt());
        response.setUpdatedAt(warehouse.getUpdatedAt());
        return response;
    }
}

