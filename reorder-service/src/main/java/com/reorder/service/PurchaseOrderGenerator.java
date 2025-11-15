package com.reorder.service;

import com.reorder.model.PurchaseOrder;
import com.reorder.model.ReorderRecommendation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Service
public class PurchaseOrderGenerator {
    
    @Autowired
    private SupplierIntegration supplierIntegration;
    
    public PurchaseOrder generateOrder(ReorderRecommendation recommendation) {
        PurchaseOrder order = new PurchaseOrder();
        order.setOrderId(UUID.randomUUID().toString());
        order.setSupplierId("SUPPLIER_001"); // TODO: Get from configuration
        order.setOrderDate(LocalDateTime.now());
        order.setExpectedDeliveryDate(LocalDateTime.now().plusDays(7));
        
        PurchaseOrder.OrderItem item = new PurchaseOrder.OrderItem();
        item.setSku(recommendation.getSku());
        item.setQuantity(recommendation.getRecommendedQuantity());
        item.setUnitPrice(10.0); // TODO: Get from product catalog
        
        List<PurchaseOrder.OrderItem> items = new ArrayList<>();
        items.add(item);
        order.setItems(items);
        
        return supplierIntegration.createPurchaseOrder(order);
    }
}

