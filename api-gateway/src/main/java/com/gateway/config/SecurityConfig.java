package com.gateway.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.reactive.EnableWebFluxSecurity;
import org.springframework.security.config.web.server.ServerHttpSecurity;
import org.springframework.security.web.server.SecurityWebFilterChain;

/**
 * Security configuration for the API Gateway.
 * 
 * Note: JWT authentication is handled by the AuthenticationFilter
 * (GlobalFilter).
 * This config disables Spring Security's default behavior and allows all
 * requests
 * to pass through to the custom filter chain.
 */
@Configuration
@EnableWebFluxSecurity
public class SecurityConfig {

    @Bean
    public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
        return http
                // Disable CSRF for API Gateway (stateless JWT auth)
                .csrf(ServerHttpSecurity.CsrfSpec::disable)
                // Allow all exchanges - JWT auth is handled by AuthenticationFilter
                .authorizeExchange(exchanges -> exchanges
                        .anyExchange().permitAll())
                // Disable form login (we use JWT)
                .formLogin(ServerHttpSecurity.FormLoginSpec::disable)
                // Disable HTTP Basic (we use JWT)
                .httpBasic(ServerHttpSecurity.HttpBasicSpec::disable)
                .build();
    }
}
