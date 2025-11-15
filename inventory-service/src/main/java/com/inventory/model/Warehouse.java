package com.inventory.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.EqualsAndHashCode;

@Entity
@Table(name = "warehouses",
       indexes = {
           @Index(name = "idx_warehouse_id", columnList = "warehouse_id")
       },
       uniqueConstraints = {
           @UniqueConstraint(columnNames = "warehouse_id")
       })
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@EqualsAndHashCode(callSuper = false)
public class Warehouse extends BaseModel {
    
    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "warehouse_seq")
    @SequenceGenerator(name = "warehouse_seq", sequenceName = "warehouses_seq", allocationSize = 1)
    private Long id;
    
    @NotNull
    @Size(min = 2, max = 20)
    @Column(name = "warehouse_id", nullable = false, unique = true, length = 20)
    private String warehouseId;
    
    @NotNull
    @Size(min = 2, max = 200)
    @Column(nullable = false, length = 200)
    private String name;
    
    @Size(max = 500)
    @Column(length = 500)
    private String address;
    
    @Size(max = 100)
    @Column(length = 100)
    private String city;
    
    @Size(max = 100)
    @Column(length = 100)
    private String state;
    
    @Size(max = 100)
    @Column(length = 100)
    private String country;
    
    @Size(max = 20)
    @Column(name = "postal_code", length = 20)
    private String postalCode;
    
    @Column(name = "is_active")
    private Boolean isActive = true;
}

