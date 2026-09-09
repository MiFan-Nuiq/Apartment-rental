package com.rental.controller;

import com.rental.dto.ApiResponse;
import com.rental.entity.Apartment;
import com.rental.entity.Favorite;
import com.rental.entity.User;
import com.rental.repository.ApartmentRepository;
import com.rental.repository.UserRepository;
import com.rental.service.FavoriteService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/favorites")
public class FavoriteController {
    @Autowired
    private FavoriteService favoriteService;
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private ApartmentRepository apartmentRepository;

    @GetMapping("/tenant/{tenantId}")
    public ApiResponse<List<Map<String, Object>>> getFavorites(@PathVariable Long tenantId) {
        List<Favorite> favorites = favoriteService.findByTenantId(tenantId);
        List<Map<String, Object>> result = favorites.stream().map(f -> {
            Map<String, Object> map = new HashMap<>();
            map.put("id", f.getId());
            map.put("apartment", f.getApartment());
            map.put("createTime", f.getCreateTime());
            return map;
        }).collect(Collectors.toList());
        return ApiResponse.success(result);
    }

    @GetMapping("/check")
    public ApiResponse<Boolean> checkFavorite(@RequestParam Long tenantId, @RequestParam Long apartmentId) {
        return ApiResponse.success(favoriteService.isFavorited(tenantId, apartmentId));
    }

    @PostMapping
    public ApiResponse<Favorite> addFavorite(@RequestBody Map<String, Long> params) {
        User tenant = userRepository.findById(params.get("tenantId"))
                .orElseThrow(() -> new RuntimeException("用户不存在"));
        Apartment apartment = apartmentRepository.findById(params.get("apartmentId"))
                .orElseThrow(() -> new RuntimeException("房源不存在"));
        Favorite favorite = favoriteService.addFavorite(tenant, apartment);
        return ApiResponse.success("收藏成功", favorite);
    }

    @DeleteMapping
    public ApiResponse<Void> removeFavorite(@RequestParam Long tenantId, @RequestParam Long apartmentId) {
        favoriteService.removeFavorite(tenantId, apartmentId);
        return ApiResponse.success("取消收藏成功", null);
    }

    @GetMapping("/count/{apartmentId}")
    public ApiResponse<Long> getFavoriteCount(@PathVariable Long apartmentId) {
        return ApiResponse.success(favoriteService.getFavoriteCount(apartmentId));
    }
}
