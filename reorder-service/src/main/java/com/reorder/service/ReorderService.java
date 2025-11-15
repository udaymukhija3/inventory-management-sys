package com.reorder.service;

import com.reorder.model.ReorderRecommendation;
import org.springframework.stereotype.Service;

@Service
public class ReorderService {
    
    public ReorderRecommendation generateRecommendation(String sku, String warehouseId, 
                                                         Integer currentQuantity, Integer reorderPoint) {
        ReorderRecommendation recommendation = new ReorderRecommendation();
        recommendation.setSku(sku);
        recommendation.setWarehouseId(warehouseId);
        recommendation.setCurrentQuantity(currentQuantity);
        recommendation.setReorderPoint(reorderPoint);
        
        if (currentQuantity <= reorderPoint) {
            int recommendedQuantity = reorderPoint * 2 - currentQuantity;
            recommendation.setRecommendedQuantity(recommendedQuantity);
            recommendation.setPriority("HIGH");
        } else {
            recommendation.setRecommendedQuantity(0);
            recommendation.setPriority("LOW");
        }
        
        return recommendation;
    }
}

