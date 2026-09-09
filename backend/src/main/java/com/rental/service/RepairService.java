package com.rental.service;

import com.rental.entity.Repair;
import com.rental.repository.RepairRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class RepairService {

    @Autowired
    private RepairRepository repairRepository;

    public List<Repair> findAll() {
        return repairRepository.findAll();
    }

    public Repair findById(Long id) {
        return repairRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("报障记录不存在"));
    }

    public List<Repair> findByTenantId(Long tenantId) {
        return repairRepository.findByTenantId(tenantId);
    }

    public List<Repair> findByLandlordId(Long landlordId) {
        return repairRepository.findByLandlordId(landlordId);
    }

    public Repair save(Repair repair) {
        if (repair.getStatus() == null || repair.getStatus().isEmpty()) {
            repair.setStatus("待处理");
        }
        return repairRepository.save(repair);
    }

    public Repair update(Long id, Repair repair) {
        Repair existing = findById(id);
        repair.setId(id);
        repair.setCreateTime(existing.getCreateTime());
        return repairRepository.save(repair);
    }

    public Repair handleRepair(Long id, String status, String reply) {
        Repair repair = findById(id);
        repair.setStatus(status);
        repair.setReply(reply);
        return repairRepository.save(repair);
    }

    public void delete(Long id) {
        repairRepository.deleteById(id);
    }
}
