package com.inventory.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.inventory.model.InventoryItem;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class RedisInventoryCache {
    
    private final RedisTemplate<String, Object> redisTemplate;
    private final ObjectMapper objectMapper;
    
    private static final String INVENTORY_KEY_PREFIX = "inventory:";
    private static final String VELOCITY_KEY_PREFIX = "velocity:";
    private static final String HOT_ITEMS_KEY = "hot_items";
    private static final Duration DEFAULT_TTL = Duration.ofMinutes(10);
    private static final Duration VELOCITY_TTL = Duration.ofHours(1);
    
    /**
     * Cache inventory item
     */
    public void updateInventory(InventoryItem item) {
        try {
            String key = getInventoryKey(item.getSku(), item.getWarehouseId());
            
            // Store as hash for efficient field updates
            Map<String, Object> itemData = Map.of(
                "quantityOnHand", item.getQuantityOnHand(),
                "quantityReserved", item.getQuantityReserved(),
                "quantityAvailable", item.getAvailableQuantity(),
                "status", item.getStatus().name(),
                "lastUpdated", item.getUpdatedAt().toString()
            );
            
            redisTemplate.opsForHash().putAll(key, itemData);
            redisTemplate.expire(key, DEFAULT_TTL);
            
            // Update hot items set if this is frequently accessed
            trackHotItem(item.getSku());
            
            log.debug("Cached inventory for {}:{}", item.getSku(), item.getWarehouseId());
        } catch (Exception e) {
            log.error("Error caching inventory item", e);
        }
    }
    
    /**
     * Update inventory quantity (backward compatibility)
     */
    public void updateInventory(String sku, String warehouseId, Integer quantity) {
        try {
            String key = getInventoryKey(sku, warehouseId);
            redisTemplate.opsForHash().put(key, "quantityOnHand", quantity);
            redisTemplate.expire(key, DEFAULT_TTL);
            log.debug("Updated cached quantity for {}:{}", sku, warehouseId);
        } catch (Exception e) {
            log.error("Error updating cached quantity", e);
        }
    }
    
    /**
     * Get cached inventory quantity
     */
    public Integer getCachedQuantity(String sku, String warehouseId) {
        try {
            String key = getInventoryKey(sku, warehouseId);
            Object quantity = redisTemplate.opsForHash().get(key, "quantityOnHand");
            return quantity != null ? Integer.valueOf(quantity.toString()) : null;
        } catch (Exception e) {
            log.error("Error retrieving cached quantity", e);
            return null;
        }
    }
    
    /**
     * Get inventory (backward compatibility)
     */
    public Integer getInventory(String sku, String warehouseId) {
        return getCachedQuantity(sku, warehouseId);
    }
    
    /**
     * Get full cached inventory item
     */
    public InventoryItem getCachedInventoryItem(String sku, String warehouseId) {
        try {
            String key = getInventoryKey(sku, warehouseId);
            Map<Object, Object> itemData = redisTemplate.opsForHash().entries(key);
            
            if (itemData.isEmpty()) {
                return null;
            }
            
            // Convert hash map to InventoryItem (simplified - would need full deserialization)
            // For now, return null and let service fetch from database
            return null;
        } catch (Exception e) {
            log.error("Error retrieving cached inventory item", e);
            return null;
        }
    }
    
    /**
     * Cache velocity score for fast-moving item detection
     */
    public void updateVelocityScore(String sku, String warehouseId, Double velocityScore) {
        try {
            String key = getVelocityKey(sku, warehouseId);
            redisTemplate.opsForValue().set(key, velocityScore, VELOCITY_TTL);
            
            // Add to sorted set for top movers
            redisTemplate.opsForZSet().add("velocity:rankings", 
                                          sku + ":" + warehouseId, 
                                          velocityScore);
        } catch (Exception e) {
            log.error("Error caching velocity score", e);
        }
    }
    
    /**
     * Get velocity score
     */
    public Double getVelocityScore(String sku, String warehouseId) {
        try {
            String key = getVelocityKey(sku, warehouseId);
            Object score = redisTemplate.opsForValue().get(key);
            return score != null ? Double.valueOf(score.toString()) : null;
        } catch (Exception e) {
            log.error("Error retrieving velocity score", e);
            return null;
        }
    }
    
    /**
     * Get top moving items
     */
    public Set<String> getTopMovingItems(int limit) {
        try {
            Set<Object> objects = redisTemplate.opsForZSet()
                .reverseRange("velocity:rankings", 0, limit - 1);
            return objects != null ? objects.stream()
                .map(String::valueOf)
                .collect(java.util.stream.Collectors.toSet()) : Set.of();
        } catch (Exception e) {
            log.error("Error retrieving top moving items", e);
            return Set.of();
        }
    }
    
    /**
     * Track frequently accessed items for predictive caching
     */
    private void trackHotItem(String sku) {
        try {
            // Use HyperLogLog for efficient cardinality estimation
            redisTemplate.opsForHyperLogLog().add(HOT_ITEMS_KEY, sku);
            
            // Increment access counter
            String counterKey = "access_count:" + sku;
            redisTemplate.opsForValue().increment(counterKey);
            redisTemplate.expire(counterKey, Duration.ofHours(24));
        } catch (Exception e) {
            log.error("Error tracking hot item", e);
        }
    }
    
    /**
     * Get access count for an item
     */
    public Long getAccessCount(String sku) {
        try {
            String counterKey = "access_count:" + sku;
            Object count = redisTemplate.opsForValue().get(counterKey);
            return count != null ? Long.valueOf(count.toString()) : 0L;
        } catch (Exception e) {
            log.error("Error retrieving access count", e);
            return 0L;
        }
    }
    
    /**
     * Bulk cache warming for predicted high-demand items
     */
    public void warmCache(Set<String> skus, String warehouseId) {
        log.info("Warming cache for {} items in warehouse {}", skus.size(), warehouseId);
        
        // This would typically fetch from database and cache
        // Implementation depends on your data access patterns
        // Could be implemented to pre-fetch items that are predicted to be accessed
    }
    
    /**
     * Invalidate cache for specific item
     */
    public void invalidate(String sku, String warehouseId) {
        try {
            String key = getInventoryKey(sku, warehouseId);
            redisTemplate.delete(key);
            log.debug("Invalidated cache for {}:{}", sku, warehouseId);
        } catch (Exception e) {
            log.error("Error invalidating cache", e);
        }
    }
    
    /**
     * Evict inventory (backward compatibility)
     */
    public void evictInventory(String sku, String warehouseId) {
        invalidate(sku, warehouseId);
    }
    
    /**
     * Invalidate velocity cache
     */
    public void invalidateVelocity(String sku, String warehouseId) {
        try {
            String key = getVelocityKey(sku, warehouseId);
            redisTemplate.delete(key);
            redisTemplate.opsForZSet().remove("velocity:rankings", sku + ":" + warehouseId);
            log.debug("Invalidated velocity cache for {}:{}", sku, warehouseId);
        } catch (Exception e) {
            log.error("Error invalidating velocity cache", e);
        }
    }
    
    /**
     * Clear all cache
     */
    public void clearAll() {
        try {
            Set<String> keys = redisTemplate.keys(INVENTORY_KEY_PREFIX + "*");
            if (keys != null && !keys.isEmpty()) {
                redisTemplate.delete(keys);
            }
            log.info("Cleared all inventory cache");
        } catch (Exception e) {
            log.error("Error clearing cache", e);
        }
    }
    
    /**
     * Get cache statistics
     */
    public Map<String, Object> getCacheStats() {
        try {
            Long hotItemsCount = redisTemplate.opsForHyperLogLog().size(HOT_ITEMS_KEY);
            Long velocityRankingsSize = redisTemplate.opsForZSet().size("velocity:rankings");
            
            Set<String> inventoryKeys = redisTemplate.keys(INVENTORY_KEY_PREFIX + "*");
            Long inventoryCacheSize = inventoryKeys != null ? (long) inventoryKeys.size() : 0L;
            
            return Map.of(
                "hotItemsCount", hotItemsCount != null ? hotItemsCount : 0L,
                "velocityRankingsSize", velocityRankingsSize != null ? velocityRankingsSize : 0L,
                "inventoryCacheSize", inventoryCacheSize,
                "cacheType", "Redis",
                "ttlMinutes", DEFAULT_TTL.toMinutes()
            );
        } catch (Exception e) {
            log.error("Error getting cache stats", e);
            return Map.of("error", e.getMessage());
        }
    }
    
    private String getInventoryKey(String sku, String warehouseId) {
        return INVENTORY_KEY_PREFIX + sku + ":" + warehouseId;
    }
    
    private String getVelocityKey(String sku, String warehouseId) {
        return VELOCITY_KEY_PREFIX + sku + ":" + warehouseId;
    }
}
