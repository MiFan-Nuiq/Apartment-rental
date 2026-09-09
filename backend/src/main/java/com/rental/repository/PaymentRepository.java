package com.rental.repository;

import com.rental.entity.Payment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface PaymentRepository extends JpaRepository<Payment, Long> {
    List<Payment> findByContractId(Long contractId);
    List<Payment> findByTenantId(Long tenantId);
    List<Payment> findByLandlordId(Long landlordId);
    List<Payment> findByStatus(String status);
    void deleteByContractId(Long contractId);
}
