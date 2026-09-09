package com.rental.dto;

import lombok.Data;

@Data
public class LoginResponse {
    private String token;
    private String username;
    private String realName;
    private String role;
    private Long userId;

    public LoginResponse(String token, String username, String realName, String role, Long userId) {
        this.token = token;
        this.username = username;
        this.realName = realName;
        this.role = role;
        this.userId = userId;
    }
}
