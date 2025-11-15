package com.inventory.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import java.util.List;

public class BulkUpdateRequest {
    
    @NotEmpty(message = "At least one update is required")
    @Valid
    private List<AdjustmentRequest> updates;
    
    // Getters and Setters
    public List<AdjustmentRequest> getUpdates() { return updates; }
    public void setUpdates(List<AdjustmentRequest> updates) { this.updates = updates; }
}

