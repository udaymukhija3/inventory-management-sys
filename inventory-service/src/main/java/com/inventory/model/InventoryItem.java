package com.inventory.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.EqualsAndHashCode;
import jakarta.persistence.*;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "inventory_items", 
       indexes = {
           @Index(name = "idx_sku_warehouse", columnList = "sku,warehouse_id"),
           @Index(name = "idx_warehouse", columnList = "warehouse_id"),
           @Index(name = "idx_reorder_point", columnList = "reorder_point")
       },
       uniqueConstraints = {
           @UniqueConstraint(columnNames = {"sku", "warehouse_id"})
       })
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@EqualsAndHashCode(callSuper = false)
public class InventoryItem extends BaseModel {
    
    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "inventory_seq")
    @SequenceGenerator(name = "inventory_seq", sequenceName = "inventory_items_seq", allocationSize = 1)
    private Long id;
    
    @NotNull
    @Size(min = 3, max = 50)
    @Column(nullable = false, length = 50)
    private String sku;
    
    @NotNull
    @Size(min = 2, max = 20)
    @Column(name = "warehouse_id", nullable = false, length = 20)
    private String warehouseId;
    
    @NotNull
    @Min(0)
    @Column(name = "quantity_on_hand", nullable = false)
    private Integer quantityOnHand = 0;
    
    @NotNull
    @Min(0)
    @Column(name = "quantity_reserved", nullable = false)
    private Integer quantityReserved = 0;
    
    @NotNull
    @Min(0)
    @Column(name = "quantity_in_transit", nullable = false)
    private Integer quantityInTransit = 0;
    
    @NotNull
    @Min(0)
    @Column(name = "reorder_point", nullable = false)
    private Integer reorderPoint = 0;
    
    @NotNull
    @Min(0)
    @Column(name = "reorder_quantity", nullable = false)
    private Integer reorderQuantity = 0;
    
    @Column(name = "unit_cost", precision = 10, scale = 2)
    private BigDecimal unitCost;
    
    @Column(name = "holding_cost_per_unit", precision = 10, scale = 2)
    private BigDecimal holdingCostPerUnit;
    
    @Column(name = "stockout_cost_per_unit", precision = 10, scale = 2)
    private BigDecimal stockoutCostPerUnit;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "inventory_status", length = 20)
    private InventoryStatus status = InventoryStatus.NORMAL;
    
    @Column(name = "last_stock_check")
    private LocalDateTime lastStockCheck;
    
    @Column(name = "last_reorder_date")
    private LocalDateTime lastReorderDate;
    
    @Version
    @Column(name = "version")
    private Long version;
    
    // Calculated fields
    @Transient
    public Integer getAvailableQuantity() {
        return quantityOnHand - quantityReserved;
    }
    
    @Transient
    public Integer getTotalQuantity() {
        return quantityOnHand + quantityInTransit;
    }
    
    @Transient
    public boolean needsReorder() {
        return getAvailableQuantity() <= reorderPoint;
    }
    
    @Transient
    public BigDecimal getCurrentValue() {
        if (unitCost == null) return BigDecimal.ZERO;
        return unitCost.multiply(BigDecimal.valueOf(quantityOnHand));
    }
    
    // Business methods
    public void reserve(Integer quantity) {
        if (quantity > getAvailableQuantity()) {
            throw new IllegalArgumentException("Cannot reserve more than available quantity");
        }
        this.quantityReserved += quantity;
        updateStatus();
    }
    
    public void releaseReservation(Integer quantity) {
        if (quantity > this.quantityReserved) {
            throw new IllegalArgumentException("Cannot release more than reserved quantity");
        }
        this.quantityReserved -= quantity;
        updateStatus();
    }
    
    public void adjustQuantity(Integer adjustment) {
        int newQuantity = this.quantityOnHand + adjustment;
        if (newQuantity < 0) {
            throw new IllegalArgumentException("Adjustment would result in negative inventory");
        }
        this.quantityOnHand = newQuantity;
        updateStatus();
    }
    
    public void recordSale(Integer quantity) {
        if (quantity > getAvailableQuantity()) {
            throw new IllegalArgumentException("Insufficient inventory for sale");
        }
        this.quantityOnHand -= quantity;
        updateStatus();
    }
    
    public void recordReceipt(Integer quantity) {
        this.quantityOnHand += quantity;
        if (this.quantityInTransit >= quantity) {
            this.quantityInTransit -= quantity;
        }
        updateStatus();
    }
    
    private void updateStatus() {
        if (quantityOnHand == 0) {
            this.status = InventoryStatus.OUT_OF_STOCK;
        } else if (getAvailableQuantity() <= reorderPoint) {
            this.status = InventoryStatus.LOW_STOCK;
        } else if (quantityOnHand > reorderPoint * 3) {
            this.status = InventoryStatus.OVERSTOCK;
        } else {
            this.status = InventoryStatus.NORMAL;
        }
    }
    
    public enum InventoryStatus {
        NORMAL,
        LOW_STOCK,
        OUT_OF_STOCK,
        OVERSTOCK,
        DISCONTINUED
    }
}
