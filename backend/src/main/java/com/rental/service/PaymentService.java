package com.rental.service;

import com.rental.entity.Payment;
import com.rental.repository.PaymentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;

@Service
public class PaymentService {

    @Autowired
    private PaymentRepository paymentRepository;

    public List<Payment> findAll() {
        return paymentRepository.findAll();
    }

    public Payment findById(Long id) {
        return paymentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("缴费记录不存在"));
    }

    public List<Payment> findByContractId(Long contractId) {
        return paymentRepository.findByContractId(contractId);
    }

    public List<Payment> findByTenantId(Long tenantId) {
        return paymentRepository.findByTenantId(tenantId);
    }

    public List<Payment> findByLandlordId(Long landlordId) {
        return paymentRepository.findByLandlordId(landlordId);
    }

    public Payment save(Payment payment) {
        if (payment.getPaymentNo() == null || payment.getPaymentNo().isEmpty()) {
            payment.setPaymentNo(generatePaymentNo());
        }
        return paymentRepository.save(payment);
    }

    public Payment update(Long id, Payment payment) {
        Payment existing = findById(id);
        payment.setId(id);
        payment.setCreateTime(existing.getCreateTime());
        payment.setPaymentNo(existing.getPaymentNo());
        return paymentRepository.save(payment);
    }

    public void delete(Long id) {
        paymentRepository.deleteById(id);
    }

    private String generatePaymentNo() {
        String dateStr = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        long count = paymentRepository.count() + 1;
        return "JF" + dateStr + String.format("%04d", count);
    }
}
