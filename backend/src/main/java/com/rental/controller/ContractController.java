package com.rental.controller;

import com.rental.dto.ApiResponse;
import com.rental.entity.Contract;
import com.rental.service.ContractService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/contracts")
public class ContractController {

    @Autowired
    private ContractService contractService;

    @GetMapping
    public ApiResponse<List<Contract>> findAll() {
        return ApiResponse.success(contractService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<Contract> findById(@PathVariable Long id) {
        return ApiResponse.success(contractService.findById(id));
    }

    @GetMapping("/tenant/{tenantId}")
    public ApiResponse<List<Contract>> findByTenantId(@PathVariable Long tenantId) {
        return ApiResponse.success(contractService.findByTenantId(tenantId));
    }

    @GetMapping("/landlord/{landlordId}")
    public ApiResponse<List<Contract>> findByLandlordId(@PathVariable Long landlordId) {
        return ApiResponse.success(contractService.findByLandlordId(landlordId));
    }

    @GetMapping("/apartment/{apartmentId}")
    public ApiResponse<List<Contract>> findByApartmentId(@PathVariable Long apartmentId) {
        return ApiResponse.success(contractService.findByApartmentId(apartmentId));
    }

    @PostMapping
    public ApiResponse<Contract> save(@RequestBody Contract contract) {
        return ApiResponse.success(contractService.save(contract));
    }

    @PutMapping("/{id}")
    public ApiResponse<Contract> update(@PathVariable Long id, @RequestBody Contract contract) {
        return ApiResponse.success(contractService.update(id, contract));
    }

    @PutMapping("/{id}/terminate")
    public ApiResponse<Contract> terminate(@PathVariable Long id, @RequestParam String reason) {
        return ApiResponse.success(contractService.terminate(id, reason));
    }

    @PutMapping("/{id}/sublet")
    public ApiResponse<Contract> requestSublet(@PathVariable Long id, @RequestParam Long newTenantId) {
        return ApiResponse.success(contractService.requestSublet(id, newTenantId));
    }

    @PutMapping("/{id}/sublet/confirm")
    public ApiResponse<Contract> confirmSublet(@PathVariable Long id) {
        return ApiResponse.success(contractService.confirmSublet(id));
    }

    @PutMapping("/{id}/sublet/reject")
    public ApiResponse<Contract> rejectSublet(@PathVariable Long id) {
        return ApiResponse.success(contractService.rejectSublet(id));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        contractService.delete(id);
        return ApiResponse.success("删除成功", null);
    }
}
