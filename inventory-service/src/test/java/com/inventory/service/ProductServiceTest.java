package com.inventory.service;

import com.inventory.dto.ProductRequest;
import com.inventory.dto.ProductResponse;
import com.inventory.exception.CategoryNotFoundException;
import com.inventory.exception.ProductNotFoundException;
import com.inventory.model.Category;
import com.inventory.model.Product;
import com.inventory.repository.CategoryRepository;
import com.inventory.repository.ProductRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

class ProductServiceTest {

    @Mock
    private ProductRepository productRepository;

    @Mock
    private CategoryRepository categoryRepository;

    @InjectMocks
    private ProductServiceImpl productService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void testCreateProduct_Success() {
        // Given
        Category category = new Category();
        category.setId(1L);
        category.setName("Electronics");

        ProductRequest request = new ProductRequest();
        request.setSku("LAPTOP-001");
        request.setName("Gaming Laptop");
        request.setDescription("High-performance gaming laptop");
        request.setPrice(new BigDecimal("1299.99"));
        request.setCategoryId(1L);
        request.setIsActive(true);

        Product product = Product.builder()
                .id(1L)
                .sku("LAPTOP-001")
                .name("Gaming Laptop")
                .description("High-performance gaming laptop")
                .price(new BigDecimal("1299.99"))
                .isActive(true)
                .category(category)
                .build();

        when(productRepository.existsBySku("LAPTOP-001")).thenReturn(false);
        when(categoryRepository.findById(1L)).thenReturn(Optional.of(category));
        when(productRepository.save(any(Product.class))).thenReturn(product);

        // When
        ProductResponse response = productService.createProduct(request);

        // Then
        assertNotNull(response);
        assertEquals("LAPTOP-001", response.getSku());
        assertEquals("Gaming Laptop", response.getName());
        assertEquals(1L, response.getCategoryId());
        verify(productRepository, times(1)).save(any(Product.class));
    }

    @Test
    void testCreateProduct_DuplicateSKU_ThrowsException() {
        // Given
        ProductRequest request = new ProductRequest();
        request.setSku("LAPTOP-001");
        request.setName("Gaming Laptop");

        when(productRepository.existsBySku("LAPTOP-001")).thenReturn(true);

        // When/Then
        assertThrows(IllegalArgumentException.class, () -> {
            productService.createProduct(request);
        });

        verify(productRepository, never()).save(any());
    }

    @Test
    void testCreateProduct_CategoryNotFound_ThrowsException() {
        // Given
        ProductRequest request = new ProductRequest();
        request.setSku("LAPTOP-001");
        request.setName("Gaming Laptop");
        request.setCategoryId(999L);

        when(productRepository.existsBySku("LAPTOP-001")).thenReturn(false);
        when(categoryRepository.findById(999L)).thenReturn(Optional.empty());

        // When/Then
        assertThrows(CategoryNotFoundException.class, () -> {
            productService.createProduct(request);
        });
    }

    @Test
    void testGetProductById_Success() {
        // Given
        Product product = Product.builder()
                .id(1L)
                .sku("LAPTOP-001")
                .name("Gaming Laptop")
                .price(new BigDecimal("1299.99"))
                .isActive(true)
                .build();

        when(productRepository.findById(1L)).thenReturn(Optional.of(product));

        // When
        ProductResponse response = productService.getProductById(1L);

        // Then
        assertNotNull(response);
        assertEquals(1L, response.getId());
        assertEquals("LAPTOP-001", response.getSku());
    }

    @Test
    void testGetProductById_NotFound_ThrowsException() {
        // Given
        when(productRepository.findById(999L)).thenReturn(Optional.empty());

        // When/Then
        assertThrows(ProductNotFoundException.class, () -> {
            productService.getProductById(999L);
        });
    }

    @Test
    void testGetProductBySku_Success() {
        // Given
        Product product = Product.builder()
                .id(1L)
                .sku("LAPTOP-001")
                .name("Gaming Laptop")
                .price(new BigDecimal("1299.99"))
                .isActive(true)
                .build();

        when(productRepository.findBySku("LAPTOP-001")).thenReturn(Optional.of(product));

        // When
        ProductResponse response = productService.getProductBySku("LAPTOP-001");

        // Then
        assertNotNull(response);
        assertEquals("LAPTOP-001", response.getSku());
    }

    @Test
    void testGetAllProducts_Success() {
        // Given
        Product product1 = Product.builder()
                .id(1L)
                .sku("LAPTOP-001")
                .name("Gaming Laptop")
                .price(new BigDecimal("1299.99"))
                .isActive(true)
                .build();

        Product product2 = Product.builder()
                .id(2L)
                .sku("MOUSE-001")
                .name("Gaming Mouse")
                .price(new BigDecimal("49.99"))
                .isActive(true)
                .build();

        List<Product> products = Arrays.asList(product1, product2);
        Page<Product> productPage = new PageImpl<>(products);
        Pageable pageable = PageRequest.of(0, 10);

        when(productRepository.findByIsActiveTrue(pageable)).thenReturn(productPage);

        // When
        Page<ProductResponse> response = productService.getAllProducts(pageable);

        // Then
        assertNotNull(response);
        assertEquals(2, response.getContent().size());
        assertEquals("LAPTOP-001", response.getContent().get(0).getSku());
    }

    @Test
    void testUpdateProduct_Success() {
        // Given
        Category category = new Category();
        category.setId(1L);
        category.setName("Electronics");

        Product existingProduct = Product.builder()
                .id(1L)
                .sku("LAPTOP-001")
                .name("Gaming Laptop")
                .price(new BigDecimal("1299.99"))
                .isActive(true)
                .build();

        ProductRequest request = new ProductRequest();
        request.setSku("LAPTOP-001");
        request.setName("Updated Gaming Laptop");
        request.setPrice(new BigDecimal("1399.99"));
        request.setCategoryId(1L);

        when(productRepository.findById(1L)).thenReturn(Optional.of(existingProduct));
        when(categoryRepository.findById(1L)).thenReturn(Optional.of(category));
        when(productRepository.save(any(Product.class))).thenReturn(existingProduct);

        // When
        ProductResponse response = productService.updateProduct(1L, request);

        // Then
        assertNotNull(response);
        assertEquals("Updated Gaming Laptop", existingProduct.getName());
        assertEquals(new BigDecimal("1399.99"), existingProduct.getPrice());
        verify(productRepository, times(1)).save(existingProduct);
    }

    @Test
    void testUpdateProduct_ChangeSKU_DuplicateExists_ThrowsException() {
        // Given
        Product existingProduct = Product.builder()
                .id(1L)
                .sku("LAPTOP-001")
                .name("Gaming Laptop")
                .build();

        ProductRequest request = new ProductRequest();
        request.setSku("LAPTOP-002");
        request.setName("Updated Laptop");

        when(productRepository.findById(1L)).thenReturn(Optional.of(existingProduct));
        when(productRepository.existsBySku("LAPTOP-002")).thenReturn(true);

        // When/Then
        assertThrows(IllegalArgumentException.class, () -> {
            productService.updateProduct(1L, request);
        });
    }

    @Test
    void testDeleteProduct_Success() {
        // Given
        Product product = Product.builder()
                .id(1L)
                .sku("LAPTOP-001")
                .name("Gaming Laptop")
                .isActive(true)
                .build();

        when(productRepository.findById(1L)).thenReturn(Optional.of(product));
        when(productRepository.save(any(Product.class))).thenReturn(product);

        // When
        productService.deleteProduct(1L);

        // Then
        assertFalse(product.getIsActive());
        verify(productRepository, times(1)).save(product);
    }

    @Test
    void testSearchProducts_Success() {
        // Given
        Product product = Product.builder()
                .id(1L)
                .sku("LAPTOP-001")
                .name("Gaming Laptop")
                .price(new BigDecimal("1299.99"))
                .isActive(true)
                .build();

        List<Product> products = Arrays.asList(product);
        Page<Product> productPage = new PageImpl<>(products);
        Pageable pageable = PageRequest.of(0, 10);

        when(productRepository.searchProducts("Gaming", pageable)).thenReturn(productPage);

        // When
        Page<ProductResponse> response = productService.searchProducts("Gaming", pageable);

        // Then
        assertNotNull(response);
        assertEquals(1, response.getContent().size());
        assertEquals("Gaming Laptop", response.getContent().get(0).getName());
    }

    @Test
    void testGetAllActiveProducts_Success() {
        // Given
        Product product1 = Product.builder()
                .id(1L)
                .sku("LAPTOP-001")
                .name("Gaming Laptop")
                .isActive(true)
                .build();

        Product product2 = Product.builder()
                .id(2L)
                .sku("MOUSE-001")
                .name("Gaming Mouse")
                .isActive(true)
                .build();

        when(productRepository.findByIsActiveTrue()).thenReturn(Arrays.asList(product1, product2));

        // When
        List<ProductResponse> response = productService.getAllActiveProducts();

        // Then
        assertNotNull(response);
        assertEquals(2, response.size());
    }
}
