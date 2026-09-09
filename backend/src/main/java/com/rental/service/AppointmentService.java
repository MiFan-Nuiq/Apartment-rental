package com.rental.service;

import com.rental.entity.Appointment;
import com.rental.entity.Contract;
import com.rental.repository.AppointmentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;
import java.util.List;

@Service
public class AppointmentService {

    @Autowired
    private AppointmentRepository appointmentRepository;

    @Autowired
    private ContractService contractService;

    public List<Appointment> findAll() {
        return appointmentRepository.findAll();
    }

    public Appointment findById(Long id) {
        return appointmentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("预约不存在"));
    }

    public List<Appointment> findByTenantId(Long tenantId) {
        return appointmentRepository.findByTenantId(tenantId);
    }

    public List<Appointment> findByLandlordId(Long landlordId) {
        return appointmentRepository.findByLandlordId(landlordId);
    }

    public List<Appointment> findAcceptedTenantsByLandlord(Long landlordId) {
        return appointmentRepository.findByLandlordIdAndStatus(landlordId, "已接受");
    }

    public Appointment save(Appointment appointment) {
        if (appointment.getStatus() == null || appointment.getStatus().isEmpty()) {
            appointment.setStatus("待处理");
        }
        
        if (appointment.getApartment() != null && appointment.getAppointmentTime() != null) {
            checkAppointmentTimeConflict(appointment.getApartment().getId(), appointment.getAppointmentTime());
        }
        
        return appointmentRepository.save(appointment);
    }

    private void checkAppointmentTimeConflict(Long apartmentId, LocalDateTime appointmentTime) {
        List<Contract> activeContracts = contractService.findActiveContractsByApartment(apartmentId);
        
        for (Contract contract : activeContracts) {
            if (appointmentTime.toLocalDate().isAfter(contract.getStartDate().minusDays(1)) && 
                appointmentTime.toLocalDate().isBefore(contract.getEndDate().plusDays(1))) {
                throw new RuntimeException("该房源在 " + contract.getStartDate() + " 至 " + contract.getEndDate() + " 已被预订，请选择其他时间");
            }
        }
    }

    public Appointment update(Long id, Appointment appointment) {
        Appointment existing = findById(id);
        appointment.setId(id);
        appointment.setCreateTime(existing.getCreateTime());
        return appointmentRepository.save(appointment);
    }

    public Appointment handleAppointment(Long id, String status, String reply) {
        Appointment appointment = findById(id);
        appointment.setStatus(status);
        appointment.setReply(reply);
        return appointmentRepository.save(appointment);
    }

    public void delete(Long id) {
        appointmentRepository.deleteById(id);
    }
}
