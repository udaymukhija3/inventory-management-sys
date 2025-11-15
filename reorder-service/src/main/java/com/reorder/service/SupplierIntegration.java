package com.reorder.service;

import com.reorder.model.PurchaseOrder;
import org.springframework.stereotype.Service;

@Service
public class SupplierIntegration {
    
    public PurchaseOrder createPurchaseOrder(PurchaseOrder order) {
        // TODO: Integrate with supplier API
        order.setStatus("PENDING");
        return order;
    }
    
    public PurchaseOrder getOrderStatus(String orderId) {
        // TODO: Fetch order status from supplier
        PurchaseOrder order = new PurchaseOrder();
        order.setOrderId(orderId);
        order.setStatus("PENDING");
        return order;
    }
}

