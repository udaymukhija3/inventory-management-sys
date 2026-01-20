package com.gateway.service;

import com.gateway.dto.AuthResponse;
import com.gateway.dto.LoginRequest;
import com.gateway.dto.RegisterRequest;
import com.gateway.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Authentication service for handling login and registration.
 * 
 * NOTE: This is a simplified in-memory implementation for demo purposes.
 * In production, this should integrate with a proper user management service
 * or identity provider (e.g., Auth0, Keycloak, or a dedicated user service).
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {

    private final JwtTokenProvider jwtTokenProvider;

    /**
     * In-memory user store for demo purposes.
     * Key: username, Value: password (in production, use hashed passwords!)
     */
    private final Map<String, UserRecord> users = new ConcurrentHashMap<>() {
        {
            // Default admin user for demo
            put("admin", new UserRecord("admin", "admin123", List.of("ROLE_ADMIN", "ROLE_USER")));
            put("user", new UserRecord("user", "user123", List.of("ROLE_USER")));
        }
    };

    /**
     * Authenticate user and generate JWT token.
     */
    public Mono<AuthResponse> login(LoginRequest request) {
        return Mono.fromCallable(() -> {
            String username = request.getUsername();
            String password = request.getPassword();

            UserRecord user = users.get(username);
            if (user == null) {
                log.warn("Login failed: user not found - {}", username);
                throw new RuntimeException("Invalid username or password");
            }

            // In production, use password encoder (BCrypt)
            if (!user.password().equals(password)) {
                log.warn("Login failed: invalid password for user - {}", username);
                throw new RuntimeException("Invalid username or password");
            }

            String token = jwtTokenProvider.generateToken(username, user.roles());
            log.info("User logged in successfully: {}", username);

            return AuthResponse.builder()
                    .token(token)
                    .type("Bearer")
                    .username(username)
                    .roles(user.roles())
                    .expiresIn(jwtTokenProvider.getExpirationTime())
                    .build();
        });
    }

    /**
     * Register a new user.
     */
    public Mono<AuthResponse> register(RegisterRequest request) {
        return Mono.fromCallable(() -> {
            String username = request.getUsername();

            if (users.containsKey(username)) {
                log.warn("Registration failed: username already exists - {}", username);
                throw new RuntimeException("Username already exists");
            }

            if (request.getPassword() == null || request.getPassword().length() < 6) {
                throw new RuntimeException("Password must be at least 6 characters");
            }

            // Create new user with default role
            List<String> roles = List.of("ROLE_USER");
            users.put(username, new UserRecord(username, request.getPassword(), roles));

            String token = jwtTokenProvider.generateToken(username, roles);
            log.info("User registered successfully: {}", username);

            return AuthResponse.builder()
                    .token(token)
                    .type("Bearer")
                    .username(username)
                    .roles(roles)
                    .expiresIn(jwtTokenProvider.getExpirationTime())
                    .build();
        });
    }

    /**
     * Refresh an existing token (if valid).
     */
    public Mono<AuthResponse> refresh(String token) {
        return Mono.fromCallable(() -> {
            if (!jwtTokenProvider.validateToken(token)) {
                throw new RuntimeException("Invalid token");
            }

            String username = jwtTokenProvider.getUsernameFromToken(token);
            UserRecord user = users.get(username);

            if (user == null) {
                throw new RuntimeException("User not found");
            }

            String newToken = jwtTokenProvider.generateToken(username, user.roles());
            log.info("Token refreshed for user: {}", username);

            return AuthResponse.builder()
                    .token(newToken)
                    .type("Bearer")
                    .username(username)
                    .roles(user.roles())
                    .expiresIn(jwtTokenProvider.getExpirationTime())
                    .build();
        });
    }

    /**
     * Simple user record for demo purposes.
     */
    private record UserRecord(String username, String password, List<String> roles) {
    }
}
