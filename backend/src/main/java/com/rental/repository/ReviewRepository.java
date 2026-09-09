package com.rental.repository;

import com.rental.entity.Review;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;

public interface ReviewRepository extends JpaRepository<Review, Long> {
    List<Review> findByApartmentId(Long apartmentId);

    List<Review> findByTenantId(Long tenantId);

    List<Review> findByApartmentIdOrderByCreateTimeDesc(Long apartmentId);

    List<Review> findByStatus(String status);

    List<Review> findByApartmentIdAndStatus(Long apartmentId, String status);

    boolean existsByContractId(Long contractId);

    @Query("SELECT r FROM Review r WHERE r.apartment.landlord.id = ?1 ORDER BY r.createTime DESC")
    List<Review> findByLandlordId(Long landlordId);

    @Query("SELECT r FROM Review r WHERE r.apartment.landlord.id = ?1 AND r.status = '已通过' ORDER BY r.createTime DESC")
    List<Review> findApprovedByLandlordId(Long landlordId);

    @Query("SELECT AVG(r.rating) FROM Review r WHERE r.apartment.id = ?1 AND r.status = '已通过'")
    Double getAverageRatingByApartmentId(Long apartmentId);
}
