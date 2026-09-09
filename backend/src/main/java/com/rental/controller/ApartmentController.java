package com.rental.controller;

import com.rental.dto.ApiResponse;
import com.rental.entity.Apartment;
import com.rental.service.ApartmentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/apartments")
public class ApartmentController {

    @Autowired
    private ApartmentService apartmentService;

    @GetMapping
    public ApiResponse<List<Apartment>> findAll() {
        return ApiResponse.success(apartmentService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<Apartment> findById(@PathVariable Long id) {
        return ApiResponse.success(apartmentService.findById(id));
    }

    @GetMapping("/status/{status}")
    public ApiResponse<List<Apartment>> findByStatus(@PathVariable String status) {
        return ApiResponse.success(apartmentService.findByStatus(status));
    }

    @GetMapping("/landlord/{landlordId}")
    public ApiResponse<List<Apartment>> findByLandlordId(@PathVariable Long landlordId) {
        return ApiResponse.success(apartmentService.findByLandlordId(landlordId));
    }

    @GetMapping("/audited")
    public ApiResponse<List<Apartment>> findAudited() {
        return ApiResponse.success(apartmentService.findByAuditStatus("审核通过"));
    }

    @GetMapping("/pending-audit")
    public ApiResponse<List<Apartment>> findPendingAudit() {
        return ApiResponse.success(apartmentService.findByAuditStatus("待审核"));
    }

    @PostMapping
    public ApiResponse<Apartment> save(@RequestBody Apartment apartment) {
        return ApiResponse.success(apartmentService.save(apartment));
    }

    @PutMapping("/{id}")
    public ApiResponse<Apartment> update(@PathVariable Long id, @RequestBody Apartment apartment) {
        return ApiResponse.success(apartmentService.update(id, apartment));
    }

    @PutMapping("/{id}/audit")
    public ApiResponse<Apartment> audit(@PathVariable Long id, @RequestParam String status, @RequestParam(required = false) String remark) {
        return ApiResponse.success(apartmentService.audit(id, status, remark));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        apartmentService.delete(id);
        return ApiResponse.success("删除成功", null);
    }
}
