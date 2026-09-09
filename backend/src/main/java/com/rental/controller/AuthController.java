package com.rental.controller;

import com.rental.dto.ApiResponse;
import com.rental.dto.LoginRequest;
import com.rental.dto.LoginResponse;
import com.rental.dto.RegisterRequest;
import com.rental.entity.User;
import com.rental.service.UserService;
import com.rental.util.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private UserService userService;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private JwtUtil jwtUtil;

    @PostMapping("/login")
    public ApiResponse<LoginResponse> login(@RequestBody LoginRequest request) {
        try {
            User user = userService.findByUsername(request.getUsername());
            if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
                return ApiResponse.error("用户名或密码错误");
            }
            String token = jwtUtil.generateToken(user.getUsername());
            LoginResponse response = new LoginResponse(token, user.getUsername(), user.getRealName(), user.getRole(), user.getId());
            return ApiResponse.success("登录成功", response);
        } catch (Exception e) {
            return ApiResponse.error(e.getMessage());
        }
    }

    @PostMapping("/register")
    public ApiResponse<LoginResponse> register(@RequestBody RegisterRequest request) {
        try {
            if (userService.existsByUsername(request.getUsername())) {
                return ApiResponse.error("用户名已存在");
            }
            User user = new User();
            user.setUsername(request.getUsername());
            user.setPassword(request.getPassword());
            user.setRealName(request.getRealName());
            user.setPhone(request.getPhone());
            user.setRole(request.getRole() != null ? request.getRole() : "TENANT");
            user = userService.save(user);
            
            String token = jwtUtil.generateToken(user.getUsername());
            LoginResponse response = new LoginResponse(token, user.getUsername(), user.getRealName(), user.getRole(), user.getId());
            return ApiResponse.success("注册成功", response);
        } catch (Exception e) {
            return ApiResponse.error(e.getMessage());
        }
    }

    @GetMapping("/info")
    public ApiResponse<User> getUserInfo(@RequestHeader("Authorization") String token) {
        try {
            String username = jwtUtil.extractUsername(token.replace("Bearer ", ""));
            User user = userService.findByUsername(username);
            return ApiResponse.success(user);
        } catch (Exception e) {
            return ApiResponse.error(e.getMessage());
        }
    }
}

@RestController
@RequestMapping("/api/users")
class UserController {

    @Autowired
    private UserService userService;

    @GetMapping
    public ApiResponse<List<User>> findAll() {
        return ApiResponse.success(userService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<User> findById(@PathVariable Long id) {
        return ApiResponse.success(userService.findById(id));
    }

    @PostMapping
    public ApiResponse<User> save(@RequestBody User user) {
        return ApiResponse.success(userService.save(user));
    }

    @PutMapping("/{id}")
    public ApiResponse<User> update(@PathVariable Long id, @RequestBody User user) {
        return ApiResponse.success(userService.update(id, user));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        userService.delete(id);
        return ApiResponse.success("删除成功", null);
    }
}
