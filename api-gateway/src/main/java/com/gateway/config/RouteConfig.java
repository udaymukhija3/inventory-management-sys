package com.gateway.config;

import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RouteConfig {
    
    @Bean
    public RouteLocator routes(RouteLocatorBuilder builder) {
        return builder.routes()
            .route("inventory-service", r -> r
                .path("/api/v1/inventory/**")
                .uri("http://inventory-service:8080"))
            .route("analytics-service", r -> r
                .path("/api/v1/analytics/**")
                .uri("http://analytics-service:8000"))
            .route("reorder-service", r -> r
                .path("/api/v1/reorder/**")
                .uri("http://reorder-service:8081"))
            .build();
    }
}

