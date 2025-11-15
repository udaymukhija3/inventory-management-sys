package com.gateway.filter;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.logging.Logger;

@Component
public class LoggingFilter implements GlobalFilter, Ordered {
    
    private static final Logger logger = Logger.getLogger(LoggingFilter.class.getName());
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        logger.info("Request: " + exchange.getRequest().getMethod() + " " + 
                   exchange.getRequest().getURI());
        return chain.filter(exchange);
    }
    
    @Override
    public int getOrder() {
        return 0;
    }
}

