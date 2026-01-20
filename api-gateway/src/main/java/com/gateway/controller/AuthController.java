package com.gateway.controller;

import com.gateway.dto.AuthResponse;
import com.gateway.dto.LoginRequest;
import com.gateway.dto.RegisterRequest;
import com.gateway.service.AuthService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.Map;

/**
 * Authentication controller for login, registration, and token management.
 * All endpoints in this controller are public (no JWT required).
 */
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
@Slf4j
public class AuthController {

    private final AuthService authService;

    /**
     * Login endpoint - authenticates user and returns JWT token.
     * 
     * POST /api/auth/login
     * Body: {"username": "admin", "password": "admin123"}
     */
    @PostMapping("/login")
    public Mono<ResponseEntity<AuthResponse>> login(@RequestBody LoginRequest request) {
        log.info("Login attempt for user: {}", request.getUsername());

        return authService.login(request)
                .map(ResponseEntity::ok)
                .onErrorResume(e -> {
                    log.error("Login failed: {}", e.getMessage());
                    return Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).build());
                });
    }

    /**
     * Registration endpoint - creates new user and returns JWT token.
     * 
     * POST /api/auth/register
     * Body: {"username": "newuser", "password": "password123", "email":
     * "user@example.com"}
     */
    @PostMapping("/register")
    public Mono<ResponseEntity<AuthResponse>> register(@RequestBody RegisterRequest request) {
        log.info("Registration attempt for user: {}", request.getUsername());

        return authService.register(request)
                .map(response -> ResponseEntity.status(HttpStatus.CREATED).body(response))
                .onErrorResume(e -> {
                    log.error("Registration failed: {}", e.getMessage());
                    return Mono.just(ResponseEntity.status(HttpStatus.BAD_REQUEST).build());
                });
    }

    /**
     * Token refresh endpoint - issues new token if current one is valid.
     * 
     * POST /api/auth/refresh
     * Header: Authorization: Bearer <token>
     */
    @PostMapping("/refresh")
    public Mono<ResponseEntity<AuthResponse>> refresh(
            @RequestHeader(value = "Authorization", required = false) String authHeader) {

        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            return Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).build());
        }

        String token = authHeader.substring(7);
        log.info("Token refresh attempt");

        return authService.refresh(token)
                .map(ResponseEntity::ok)
                .onErrorResume(e -> {
                    log.error("Token refresh failed: {}", e.getMessage());
                    return Mono.just(ResponseEntity.status(HttpStatus.UNAUTHORIZED).build());
                });
    }

    /**
     * Health check endpoint for the auth service.
     */
    @GetMapping("/health")
    public Mono<ResponseEntity<Map<String, String>>> health() {
        return Mono.just(ResponseEntity.ok(Map.of(
                "status", "UP",
                "service", "auth-service")));
    }
}
