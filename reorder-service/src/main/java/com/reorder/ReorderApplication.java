package com.reorder;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.kafka.annotation.EnableKafka;

@SpringBootApplication
@EnableKafka
public class ReorderApplication {
    public static void main(String[] args) {
        SpringApplication.run(ReorderApplication.class, args);
    }
}

