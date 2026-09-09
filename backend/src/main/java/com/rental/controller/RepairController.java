package com.rental.controller;

import com.rental.dto.ApiResponse;
import com.rental.entity.Repair;
import com.rental.service.RepairService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/repairs")
public class RepairController {

    @Autowired
    private RepairService repairService;

    @GetMapping
    public ApiResponse<List<Repair>> findAll() {
        return ApiResponse.success(repairService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<Repair> findById(@PathVariable Long id) {
        return ApiResponse.success(repairService.findById(id));
    }

    @GetMapping("/tenant/{tenantId}")
    public ApiResponse<List<Repair>> findByTenantId(@PathVariable Long tenantId) {
        return ApiResponse.success(repairService.findByTenantId(tenantId));
    }

    @GetMapping("/landlord/{landlordId}")
    public ApiResponse<List<Repair>> findByLandlordId(@PathVariable Long landlordId) {
        return ApiResponse.success(repairService.findByLandlordId(landlordId));
    }

    @PostMapping
    public ApiResponse<Repair> save(@RequestBody Repair repair) {
        return ApiResponse.success(repairService.save(repair));
    }

    @PutMapping("/{id}")
    public ApiResponse<Repair> update(@PathVariable Long id, @RequestBody Repair repair) {
        return ApiResponse.success(repairService.update(id, repair));
    }

    @PutMapping("/{id}/handle")
    public ApiResponse<Repair> handleRepair(@PathVariable Long id, @RequestParam String status, @RequestParam(required = false) String reply) {
        return ApiResponse.success(repairService.handleRepair(id, status, reply));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        repairService.delete(id);
        return ApiResponse.success("删除成功", null);
    }
}
