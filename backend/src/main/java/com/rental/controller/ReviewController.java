package com.rental.controller;

import com.rental.dto.ApiResponse;
import com.rental.entity.*;
import com.rental.repository.*;
import com.rental.service.ReviewService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/reviews")
public class ReviewController {
    @Autowired
    private ReviewService reviewService;
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private ApartmentRepository apartmentRepository;
    @Autowired
    private ContractRepository contractRepository;

    @GetMapping
    public ApiResponse<List<Review>> getAllReviews() {
        return ApiResponse.success(reviewService.findAll());
    }

    @GetMapping("/apartment/{apartmentId}")
    public ApiResponse<List<Review>> getApartmentReviews(@PathVariable Long apartmentId) {
        return ApiResponse.success(reviewService.findByApartmentId(apartmentId));
    }

    @GetMapping("/apartment/{apartmentId}/approved")
    public ApiResponse<List<Review>> getApprovedApartmentReviews(@PathVariable Long apartmentId) {
        return ApiResponse.success(reviewService.findApprovedByApartment(apartmentId));
    }

    @GetMapping("/tenant/{tenantId}")
    public ApiResponse<List<Review>> getTenantReviews(@PathVariable Long tenantId) {
        return ApiResponse.success(reviewService.findByTenantId(tenantId));
    }

    @GetMapping("/landlord/{landlordId}")
    public ApiResponse<List<Review>> getLandlordReviews(@PathVariable Long landlordId) {
        return ApiResponse.success(reviewService.findByLandlordId(landlordId));
    }

    @GetMapping("/landlord/{landlordId}/approved")
    public ApiResponse<List<Review>> getApprovedLandlordReviews(@PathVariable Long landlordId) {
        return ApiResponse.success(reviewService.findApprovedByLandlordId(landlordId));
    }

    @GetMapping("/status/{status}")
    public ApiResponse<List<Review>> getReviewsByStatus(@PathVariable String status) {
        return ApiResponse.success(reviewService.findByStatus(status));
    }

    @PostMapping
    public ApiResponse<Review> createReview(@RequestBody Map<String, Object> params) {
        Long tenantId = Long.valueOf(params.get("tenantId").toString());
        Long apartmentId = Long.valueOf(params.get("apartmentId").toString());
        Long contractId = Long.valueOf(params.get("contractId").toString());
        Integer rating = Integer.valueOf(params.get("rating").toString());
        String content = params.get("content").toString();

        User tenant = userRepository.findById(tenantId).orElseThrow(() -> new RuntimeException("用户不存在"));
        Apartment apartment = apartmentRepository.findById(apartmentId)
                .orElseThrow(() -> new RuntimeException("房源不存在"));
        Contract contract = contractRepository.findById(contractId).orElseThrow(() -> new RuntimeException("合同不存在"));

        Review review = reviewService.createReview(tenant, apartment, contract, rating, content);
        return ApiResponse.success("评价已提交，等待管理员审核", review);
    }

    @PutMapping("/{id}/audit")
    public ApiResponse<Review> auditReview(@PathVariable Long id, @RequestParam String status,
            @RequestParam(required = false) String remark) {
        Review review = reviewService.auditReview(id, status, remark);
        return ApiResponse.success("审核完成", review);
    }

    @PostMapping("/{id}/reply")
    public ApiResponse<Review> landlordReply(@PathVariable Long id, @RequestBody Map<String, String> params) {
        Review review = reviewService.landlordReply(id, params.get("reply"));
        return ApiResponse.success("回复成功", review);
    }

    @DeleteMapping("/{id}/tenant/{tenantId}")
    public ApiResponse<Void> deleteByTenant(@PathVariable Long id, @PathVariable Long tenantId) {
        reviewService.deleteByTenant(id, tenantId);
        return ApiResponse.success("删除成功", null);
    }

    @GetMapping("/average/{apartmentId}")
    public ApiResponse<Double> getAverageRating(@PathVariable Long apartmentId) {
        return ApiResponse.success(reviewService.getAverageRating(apartmentId));
    }
}
