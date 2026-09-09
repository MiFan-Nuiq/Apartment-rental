package com.rental.repository;

import com.rental.entity.Complaint;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ComplaintRepository extends JpaRepository<Complaint, Long> {
    List<Complaint> findByTenantIdOrderByCreateTimeDesc(Long tenantId);

    List<Complaint> findByStatusOrderByCreateTimeDesc(String status);

    List<Complaint> findAllByOrderByCreateTimeDesc();
}
