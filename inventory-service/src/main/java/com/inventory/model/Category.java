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
@Table(name = "categories",
       indexes = {
           @Index(name = "idx_category_name", columnList = "name")
       },
       uniqueConstraints = {
           @UniqueConstraint(columnNames = "name")
       })
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@EqualsAndHashCode(callSuper = false)
public class Category extends BaseModel {
    
    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "category_seq")
    @SequenceGenerator(name = "category_seq", sequenceName = "categories_seq", allocationSize = 1)
    private Long id;
    
    @NotNull
    @Size(min = 2, max = 100)
    @Column(nullable = false, unique = true, length = 100)
    private String name;
    
    @Size(max = 500)
    @Column(length = 500)
    private String description;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "parent_category_id")
    private Category parentCategory;
    
    @Column(name = "is_active")
    private Boolean isActive = true;
}

