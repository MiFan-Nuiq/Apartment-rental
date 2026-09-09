package com.rental.controller;

import com.rental.dto.ApiResponse;
import com.rental.entity.Complaint;
import com.rental.entity.User;
import com.rental.repository.UserRepository;
import com.rental.service.ComplaintService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/complaints")
public class ComplaintController {
    @Autowired
    private ComplaintService complaintService;
    @Autowired
    private UserRepository userRepository;

    @GetMapping("/tenant/{tenantId}")
    public ApiResponse<List<Complaint>> getTenantComplaints(@PathVariable Long tenantId) {
        return ApiResponse.success(complaintService.findByTenantId(tenantId));
    }

    @GetMapping
    public ApiResponse<List<Complaint>> getAllComplaints() {
        return ApiResponse.success(complaintService.findAll());
    }

    @GetMapping("/pending")
    public ApiResponse<List<Complaint>> getPendingComplaints() {
        return ApiResponse.success(complaintService.findPending());
    }

    @PostMapping
    public ApiResponse<Complaint> createComplaint(@RequestBody Complaint complaint) {
        Complaint saved = complaintService.createComplaint(complaint);
        return ApiResponse.success("提交成功", saved);
    }

    @PostMapping("/{id}/reply")
    public ApiResponse<Complaint> reply(@PathVariable Long id, @RequestBody Map<String, String> params) {
        Complaint complaint = complaintService.reply(id, params.get("reply"));
        return ApiResponse.success("回复成功", complaint);
    }
}
