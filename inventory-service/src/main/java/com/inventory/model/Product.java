package com.inventory.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import jakarta.validation.constraints.DecimalMin;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.EqualsAndHashCode;
import java.math.BigDecimal;

@Entity
@Table(name = "products",
       indexes = {
           @Index(name = "idx_product_sku", columnList = "sku"),
           @Index(name = "idx_product_category", columnList = "category_id")
       },
       uniqueConstraints = {
           @UniqueConstraint(columnNames = "sku")
       })
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@EqualsAndHashCode(callSuper = false)
public class Product extends BaseModel {
    
    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "product_seq")
    @SequenceGenerator(name = "product_seq", sequenceName = "products_seq", allocationSize = 1)
    private Long id;
    
    @NotNull
    @Size(min = 3, max = 50)
    @Column(nullable = false, unique = true, length = 50)
    private String sku;
    
    @NotNull
    @Size(min = 2, max = 200)
    @Column(nullable = false, length = 200)
    private String name;
    
    @Size(max = 1000)
    @Column(length = 1000)
    private String description;
    
    @DecimalMin(value = "0.0", inclusive = true)
    @Column(name = "price", precision = 10, scale = 2)
    private BigDecimal price;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id")
    private Category category;
    
    @Column(name = "is_active")
    private Boolean isActive = true;
    
    @Column(name = "image_url")
    private String imageUrl;
    
    @Column(name = "unit_of_measure")
    private String unitOfMeasure;
}

