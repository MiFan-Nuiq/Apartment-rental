package com.rental.repository;

import com.rental.entity.Appointment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface AppointmentRepository extends JpaRepository<Appointment, Long> {
    List<Appointment> findByTenantId(Long tenantId);
    List<Appointment> findByLandlordId(Long landlordId);
    List<Appointment> findByApartmentId(Long apartmentId);
    List<Appointment> findByStatus(String status);
    List<Appointment> findByLandlordIdAndStatus(Long landlordId, String status);
    List<Appointment> findByApartmentIdAndTenantIdAndStatus(Long apartmentId, Long tenantId, String status);
}
