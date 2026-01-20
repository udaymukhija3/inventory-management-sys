package com.gateway.controller;

import com.gateway.dto.AuthResponse;
import com.gateway.dto.LoginRequest;
import com.gateway.dto.RegisterRequest;
import com.gateway.service.AuthService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Mono;

import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(SpringExtension.class)
@WebFluxTest(AuthController.class)
@Import(TestSecurityConfig.class)
class AuthControllerTest {

        @Autowired
        private WebTestClient webTestClient;

        @MockBean
        private AuthService authService;

        @Test
        void login_ShouldReturnToken_WhenCredentialsValid() {
                AuthResponse response = AuthResponse.builder()
                                .token("test-token")
                                .type("Bearer")
                                .username("testuser")
                                .roles(List.of("ROLE_USER"))
                                .expiresIn(86400000)
                                .build();

                when(authService.login(any(LoginRequest.class)))
                                .thenReturn(Mono.just(response));

                webTestClient.post()
                                .uri("/api/auth/login")
                                .contentType(MediaType.APPLICATION_JSON)
                                .bodyValue("{\"username\":\"testuser\",\"password\":\"password123\"}")
                                .exchange()
                                .expectStatus().isOk()
                                .expectBody()
                                .jsonPath("$.token").isEqualTo("test-token")
                                .jsonPath("$.type").isEqualTo("Bearer")
                                .jsonPath("$.username").isEqualTo("testuser");
        }

        @Test
        void login_ShouldReturn401_WhenCredentialsInvalid() {
                when(authService.login(any(LoginRequest.class)))
                                .thenReturn(Mono.error(new RuntimeException("Invalid credentials")));

                webTestClient.post()
                                .uri("/api/auth/login")
                                .contentType(MediaType.APPLICATION_JSON)
                                .bodyValue("{\"username\":\"baduser\",\"password\":\"wrongpass\"}")
                                .exchange()
                                .expectStatus().isUnauthorized();
        }

        @Test
        void register_ShouldReturn201_WhenRegistrationSuccessful() {
                AuthResponse response = AuthResponse.builder()
                                .token("new-token")
                                .type("Bearer")
                                .username("newuser")
                                .roles(List.of("ROLE_USER"))
                                .expiresIn(86400000)
                                .build();

                when(authService.register(any(RegisterRequest.class)))
                                .thenReturn(Mono.just(response));

                webTestClient.post()
                                .uri("/api/auth/register")
                                .contentType(MediaType.APPLICATION_JSON)
                                .bodyValue("{\"username\":\"newuser\",\"password\":\"password123\",\"email\":\"new@test.com\"}")
                                .exchange()
                                .expectStatus().isCreated()
                                .expectBody()
                                .jsonPath("$.token").isEqualTo("new-token")
                                .jsonPath("$.username").isEqualTo("newuser");
        }

        @Test
        void health_ShouldReturnUp() {
                webTestClient.get()
                                .uri("/api/auth/health")
                                .exchange()
                                .expectStatus().isOk()
                                .expectBody()
                                .jsonPath("$.status").isEqualTo("UP");
        }
}
