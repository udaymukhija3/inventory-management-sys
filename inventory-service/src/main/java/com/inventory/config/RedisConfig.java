package com.inventory.config;

import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.jsontype.BasicPolymorphicTypeValidator;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.annotation.Primary;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.RedisSerializationContext;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import java.time.Duration;

@Configuration
@EnableCaching
public class RedisConfig {
    
    @Value("${spring.redis.host}")
    private String redisHost;
    
    @Value("${spring.redis.port}")
    private int redisPort;
    
    @Value("${spring.redis.password:}")
    private String redisPassword;
    
    private GenericJackson2JsonRedisSerializer redisValueSerializer(ObjectMapper objectMapper) {
        ObjectMapper redisMapper = objectMapper.copy();
        redisMapper.activateDefaultTyping(
            BasicPolymorphicTypeValidator.builder()
                .allowIfSubType(Object.class)
                .build(),
            ObjectMapper.DefaultTyping.NON_FINAL,
            JsonTypeInfo.As.PROPERTY
        );
        return new GenericJackson2JsonRedisSerializer(redisMapper);
    }

    @Bean
    public LettuceConnectionFactory redisConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName(redisHost);
        config.setPort(redisPort);
        if (redisPassword != null && !redisPassword.isEmpty()) {
            config.setPassword(redisPassword);
        }
        return new LettuceConnectionFactory(config);
    }
    
    @Bean
    public RedisTemplate<String, Object> redisTemplate(ObjectMapper objectMapper) {
        GenericJackson2JsonRedisSerializer valueSerializer = redisValueSerializer(objectMapper);
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(redisConnectionFactory());
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(valueSerializer);
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(valueSerializer);
        return template;
    }
    
    @Bean
    public CacheManager cacheManager(RedisConnectionFactory connectionFactory, ObjectMapper objectMapper) {
        GenericJackson2JsonRedisSerializer valueSerializer = redisValueSerializer(objectMapper);
        RedisSerializationContext.SerializationPair<Object> valueSerialization =
                RedisSerializationContext.SerializationPair.fromSerializer(valueSerializer);
        RedisCacheConfiguration defaultConfig = RedisCacheConfiguration.defaultCacheConfig()
            .serializeValuesWith(valueSerialization)
            .entryTtl(Duration.ofMinutes(10))
            .disableCachingNullValues();
        
        // Cache configuration for inventory (shorter TTL for frequently updated data)
        RedisCacheConfiguration inventoryConfig = RedisCacheConfiguration.defaultCacheConfig()
            .serializeValuesWith(valueSerialization)
            .entryTtl(Duration.ofMinutes(5))
            .disableCachingNullValues();
        
        // Cache configuration for products (longer TTL for relatively stable data)
        RedisCacheConfiguration productConfig = RedisCacheConfiguration.defaultCacheConfig()
            .serializeValuesWith(valueSerialization)
            .entryTtl(Duration.ofMinutes(30))
            .disableCachingNullValues();
        
        // Cache configuration for categories (longest TTL for stable data)
        RedisCacheConfiguration categoryConfig = RedisCacheConfiguration.defaultCacheConfig()
            .serializeValuesWith(valueSerialization)
            .entryTtl(Duration.ofHours(1))
            .disableCachingNullValues();
        
        // Cache configuration for warehouses (long TTL for stable data)
        RedisCacheConfiguration warehouseConfig = RedisCacheConfiguration.defaultCacheConfig()
            .serializeValuesWith(valueSerialization)
            .entryTtl(Duration.ofHours(1))
            .disableCachingNullValues();
        
        return RedisCacheManager.builder(connectionFactory)
            .cacheDefaults(defaultConfig)
            .withCacheConfiguration("inventory", inventoryConfig)
            .withCacheConfiguration("products", productConfig)
            .withCacheConfiguration("categories", categoryConfig)
            .withCacheConfiguration("warehouses", warehouseConfig)
            .build();
    }
    
    @Bean
    @Primary
    @ConditionalOnMissingBean
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        return mapper;
    }
}
