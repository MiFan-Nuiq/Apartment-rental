package com.rental.service;

import com.rental.entity.Apartment;
import com.rental.repository.ApartmentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class ApartmentService {

    @Autowired
    private ApartmentRepository apartmentRepository;

    public List<Apartment> findAll() {
        return apartmentRepository.findAll();
    }

    public Apartment findById(Long id) {
        return apartmentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("公寓不存在"));
    }

    public List<Apartment> findByStatus(String status) {
        return apartmentRepository.findByStatus(status);
    }

    public List<Apartment> findByLandlordId(Long landlordId) {
        return apartmentRepository.findByLandlordId(landlordId);
    }

    public List<Apartment> findByAuditStatus(String auditStatus) {
        return apartmentRepository.findByAuditStatus(auditStatus);
    }

    public Apartment save(Apartment apartment) {
        if (apartment.getStatus() == null || apartment.getStatus().isEmpty()) {
            apartment.setStatus("空置");
        }
        if (apartment.getAuditStatus() == null || apartment.getAuditStatus().isEmpty()) {
            apartment.setAuditStatus("待审核");
        }
        return apartmentRepository.save(apartment);
    }

    public Apartment update(Long id, Apartment apartment) {
        Apartment existing = findById(id);
        apartment.setId(id);
        apartment.setCreateTime(existing.getCreateTime());
        return apartmentRepository.save(apartment);
    }

    public Apartment audit(Long id, String status, String remark) {
        Apartment apartment = findById(id);
        apartment.setAuditStatus(status);
        apartment.setAuditRemark(remark);
        return apartmentRepository.save(apartment);
    }

    public void delete(Long id) {
        apartmentRepository.deleteById(id);
    }
}
