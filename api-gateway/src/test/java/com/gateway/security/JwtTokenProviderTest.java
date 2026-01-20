package com.gateway.security;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.nio.charset.StandardCharsets;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class JwtTokenProviderTest {

    private JwtTokenProvider jwtTokenProvider;
    private final String secret = "test_secret_key_must_be_at_least_32_chars_long";
    private final long expiration = 3600000; // 1 hour

    @BeforeEach
    void setUp() {
        jwtTokenProvider = new JwtTokenProvider();
        ReflectionTestUtils.setField(jwtTokenProvider, "jwtSecret", secret);
        ReflectionTestUtils.setField(jwtTokenProvider, "jwtExpiration", expiration);
        jwtTokenProvider.init();
    }

    @Test
    void generateToken_ShouldReturnValidToken() {
        String token = jwtTokenProvider.generateToken("testuser", List.of("ROLE_USER"));
        assertNotNull(token);
        assertTrue(token.length() > 0);
    }

    @Test
    void validateToken_ShouldReturnTrueForValidToken() {
        String token = jwtTokenProvider.generateToken("testuser", List.of("ROLE_USER"));
        assertTrue(jwtTokenProvider.validateToken(token));
    }

    @Test
    void validateToken_ShouldReturnFalseForInvalidToken() {
        assertFalse(jwtTokenProvider.validateToken("invalid_token_string"));
    }

    @Test
    void getUsernameFromToken_ShouldReturnCorrectUsername() {
        String token = jwtTokenProvider.generateToken("testuser", List.of("ROLE_USER"));
        assertEquals("testuser", jwtTokenProvider.getUsernameFromToken(token));
    }

    @Test
    void getRolesFromToken_ShouldReturnCorrectRoles() {
        String token = jwtTokenProvider.generateToken("testuser", List.of("ROLE_ADMIN", "ROLE_USER"));
        List<String> roles = jwtTokenProvider.getRolesFromToken(token);
        assertEquals(2, roles.size());
        assertTrue(roles.contains("ROLE_ADMIN"));
        assertTrue(roles.contains("ROLE_USER"));
    }

    @Test
    void isTokenExpired_ShouldReturnFalseForNewToken() {
        String token = jwtTokenProvider.generateToken("testuser", List.of("ROLE_USER"));
        assertFalse(jwtTokenProvider.isTokenExpired(token));
    }
}
