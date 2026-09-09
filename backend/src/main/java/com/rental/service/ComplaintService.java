package com.rental.service;

import com.rental.entity.Complaint;
import com.rental.repository.ComplaintRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class ComplaintService {
    @Autowired
    private ComplaintRepository complaintRepository;

    public List<Complaint> findByTenantId(Long tenantId) {
        return complaintRepository.findByTenantIdOrderByCreateTimeDesc(tenantId);
    }

    public List<Complaint> findAll() {
        return complaintRepository.findAllByOrderByCreateTimeDesc();
    }

    public List<Complaint> findPending() {
        return complaintRepository.findByStatusOrderByCreateTimeDesc("待处理");
    }

    @Transactional
    public Complaint createComplaint(Complaint complaint) {
        return complaintRepository.save(complaint);
    }

    @Transactional
    public Complaint reply(Long id, String reply) {
        Complaint complaint = complaintRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("投诉不存在"));
        complaint.setAdminReply(reply);
        complaint.setReplyTime(LocalDateTime.now());
        complaint.setStatus("已处理");
        return complaintRepository.save(complaint);
    }
}
