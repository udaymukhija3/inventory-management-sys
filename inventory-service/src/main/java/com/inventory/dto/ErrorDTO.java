package com.inventory.dto;

import java.time.LocalDateTime;

public class ErrorDTO {
    private String error;
    private String message;
    private LocalDateTime timestamp;
    private String path;
    
    public ErrorDTO() {
        this.timestamp = LocalDateTime.now();
    }
    
    public ErrorDTO(String error, String message) {
        this();
        this.error = error;
        this.message = message;
    }
    
    public ErrorDTO(String error, String message, String path) {
        this(error, message);
        this.path = path;
    }
    
    // Getters and Setters
    public String getError() { return error; }
    public void setError(String error) { this.error = error; }
    
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
    
    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }
    
    public String getPath() { return path; }
    public void setPath(String path) { this.path = path; }
}

