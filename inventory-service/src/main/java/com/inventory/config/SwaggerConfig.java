package com.inventory.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.Contact;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {
    
    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("Inventory Management System API")
                .version("1.0.0")
                .description("Monolithic inventory management system with backend APIs and data engineering capabilities")
                .contact(new Contact()
                    .name("Inventory Team")
                    .email("inventory@example.com")
                )
            );
    }
}

