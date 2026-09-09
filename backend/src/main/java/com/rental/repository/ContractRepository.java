package com.rental.repository;

import com.rental.entity.Contract;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface ContractRepository extends JpaRepository<Contract, Long> {
    List<Contract> findByTenantId(Long tenantId);

    List<Contract> findByLandlordId(Long landlordId);

    List<Contract> findByApartmentId(Long apartmentId);

    List<Contract> findByStatus(String status);

    List<Contract> findByApartmentIdAndStatus(Long apartmentId, String status);
}
