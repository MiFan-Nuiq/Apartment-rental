package com.rental.controller;

import com.rental.dto.ApiResponse;
import com.rental.entity.Payment;
import com.rental.service.PaymentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/payments")
public class PaymentController {

    @Autowired
    private PaymentService paymentService;

    @GetMapping
    public ApiResponse<List<Payment>> findAll() {
        return ApiResponse.success(paymentService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<Payment> findById(@PathVariable Long id) {
        return ApiResponse.success(paymentService.findById(id));
    }

    @GetMapping("/contract/{contractId}")
    public ApiResponse<List<Payment>> findByContractId(@PathVariable Long contractId) {
        return ApiResponse.success(paymentService.findByContractId(contractId));
    }

    @GetMapping("/tenant/{tenantId}")
    public ApiResponse<List<Payment>> findByTenantId(@PathVariable Long tenantId) {
        return ApiResponse.success(paymentService.findByTenantId(tenantId));
    }

    @GetMapping("/landlord/{landlordId}")
    public ApiResponse<List<Payment>> findByLandlordId(@PathVariable Long landlordId) {
        return ApiResponse.success(paymentService.findByLandlordId(landlordId));
    }

    @PostMapping
    public ApiResponse<Payment> save(@RequestBody Payment payment) {
        return ApiResponse.success(paymentService.save(payment));
    }

    @PutMapping("/{id}")
    public ApiResponse<Payment> update(@PathVariable Long id, @RequestBody Payment payment) {
        return ApiResponse.success(paymentService.update(id, payment));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        paymentService.delete(id);
        return ApiResponse.success("删除成功", null);
    }
}
