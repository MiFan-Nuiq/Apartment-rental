package com.rental.repository;

import com.rental.entity.Apartment;
import com.rental.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface ApartmentRepository extends JpaRepository<Apartment, Long> {
    List<Apartment> findByStatus(String status);

    List<Apartment> findByLandlordId(Long landlordId);

    List<Apartment> findByLandlord(User landlord);

    List<Apartment> findByAuditStatus(String auditStatus);

    List<Apartment> findByLandlordIdAndStatus(Long landlordId, String status);
}
