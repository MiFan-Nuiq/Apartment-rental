package com.rental.service;

import com.rental.entity.Apartment;
import com.rental.entity.Contract;
import com.rental.entity.Review;
import com.rental.entity.User;
import com.rental.repository.ReviewRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class ReviewService {
    @Autowired
    private ReviewRepository reviewRepository;

    public List<Review> findByApartmentId(Long apartmentId) {
        return reviewRepository.findByApartmentIdOrderByCreateTimeDesc(apartmentId);
    }

    public List<Review> findByTenantId(Long tenantId) {
        return reviewRepository.findByTenantId(tenantId);
    }

    public List<Review> findByStatus(String status) {
        return reviewRepository.findByStatus(status);
    }

    public List<Review> findAll() {
        return reviewRepository.findAll();
    }

    public List<Review> findApprovedByApartment(Long apartmentId) {
        return reviewRepository.findByApartmentIdAndStatus(apartmentId, "已通过");
    }

    public List<Review> findByLandlordId(Long landlordId) {
        return reviewRepository.findByLandlordId(landlordId);
    }

    public List<Review> findApprovedByLandlordId(Long landlordId) {
        return reviewRepository.findApprovedByLandlordId(landlordId);
    }

    @Transactional
    public Review createReview(User tenant, Apartment apartment, Contract contract, Integer rating, String content) {
        if (reviewRepository.existsByContractId(contract.getId())) {
            throw new RuntimeException("该合同已评价过");
        }
        if (rating < 1 || rating > 5) {
            throw new RuntimeException("评分必须在1-5之间");
        }
        Review review = new Review();
        review.setTenant(tenant);
        review.setApartment(apartment);
        review.setContract(contract);
        review.setRating(rating);
        review.setContent(content);
        review.setStatus("待审核");
        return reviewRepository.save(review);
    }

    @Transactional
    public Review auditReview(Long reviewId, String status, String remark) {
        Review review = reviewRepository.findById(reviewId)
                .orElseThrow(() -> new RuntimeException("评价不存在"));
        if (!"待审核".equals(review.getStatus())) {
            throw new RuntimeException("该评价已审核");
        }
        review.setStatus(status);
        review.setAuditRemark(remark);
        return reviewRepository.save(review);
    }

    @Transactional
    public Review landlordReply(Long reviewId, String reply) {
        Review review = reviewRepository.findById(reviewId)
                .orElseThrow(() -> new RuntimeException("评价不存在"));
        if (!"已通过".equals(review.getStatus())) {
            throw new RuntimeException("只能回复已通过审核的评价");
        }
        review.setLandlordReply(reply);
        review.setReplyTime(LocalDateTime.now());
        return reviewRepository.save(review);
    }

    @Transactional
    public void deleteByTenant(Long reviewId, Long tenantId) {
        Review review = reviewRepository.findById(reviewId)
                .orElseThrow(() -> new RuntimeException("评价不存在"));
        if (!review.getTenant().getId().equals(tenantId)) {
            throw new RuntimeException("无权删除此评价");
        }
        reviewRepository.delete(review);
    }

    public Double getAverageRating(Long apartmentId) {
        return reviewRepository.getAverageRatingByApartmentId(apartmentId);
    }
}
