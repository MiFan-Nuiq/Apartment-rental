package com.rental.service;

import com.rental.entity.Apartment;
import com.rental.entity.Contract;
import com.rental.entity.Payment;
import com.rental.entity.User;
import com.rental.repository.ContractRepository;
import com.rental.repository.PaymentRepository;
import com.rental.repository.AppointmentRepository;
import com.rental.repository.ApartmentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class ContractService {

    @Autowired
    private ContractRepository contractRepository;

    @Autowired
    private ApartmentService apartmentService;

    @Autowired
    private UserService userService;

    @Autowired
    private PaymentRepository paymentRepository;

    @Autowired
    private AppointmentRepository appointmentRepository;

    @Autowired
    private ApartmentRepository apartmentRepository;

    public List<Contract> findAll() {
        checkAndUpdateExpiredContracts();
        return contractRepository.findAll();
    }

    public Contract findById(Long id) {
        checkAndUpdateExpiredContracts();
        return contractRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("合同不存在"));
    }

    public List<Contract> findByTenantId(Long tenantId) {
        checkAndUpdateExpiredContracts();
        return contractRepository.findByTenantId(tenantId);
    }

    public List<Contract> findByLandlordId(Long landlordId) {
        checkAndUpdateExpiredContracts();
        return contractRepository.findByLandlordId(landlordId);
    }

    public List<Contract> findByApartmentId(Long apartmentId) {
        checkAndUpdateExpiredContracts();
        return contractRepository.findByApartmentId(apartmentId);
    }

    public List<Contract> findActiveContractsByApartment(Long apartmentId) {
        return contractRepository.findByApartmentId(apartmentId).stream()
                .filter(c -> "生效中".equals(c.getStatus()) || "待确认".equals(c.getStatus()))
                .collect(Collectors.toList());
    }

    @Transactional
    public void checkAndUpdateExpiredContracts() {
        LocalDate today = LocalDate.now();
        List<Contract> activeContracts = contractRepository.findByStatus("生效中");

        for (Contract contract : activeContracts) {
            if (contract.getEndDate() != null && contract.getEndDate().isBefore(today)) {
                contract.setStatus("已到期");
                contractRepository.save(contract);

                Apartment apartment = contract.getApartment();
                if (apartment != null) {
                    boolean hasOtherActiveContracts = contractRepository
                            .findByApartmentIdAndStatus(apartment.getId(), "生效中")
                            .stream()
                            .anyMatch(c -> !c.getId().equals(contract.getId()));

                    if (!hasOtherActiveContracts) {
                        apartment.setStatus("空置");
                        apartmentRepository.save(apartment);
                    }
                }
            }
        }
    }

    public Contract save(Contract contract) {
        if (contract.getContractNo() == null || contract.getContractNo().isEmpty()) {
            contract.setContractNo(generateContractNo());
        }

        if (contract.getContractType() == null) {
            contract.setContractType("新签");
        }

        if (contract.getSubletStatus() == null) {
            contract.setSubletStatus("无");
        }

        if (contract.getApartment() != null && contract.getStartDate() != null && contract.getEndDate() != null) {
            checkTimeConflict(contract.getApartment().getId(), contract.getStartDate(), contract.getEndDate(), null);
        }

        return contractRepository.save(contract);
    }

    private void checkTimeConflict(Long apartmentId, LocalDate startDate, LocalDate endDate, Long excludeContractId) {
        List<Contract> existingContracts = findActiveContractsByApartment(apartmentId);

        for (Contract existing : existingContracts) {
            if (excludeContractId != null && existing.getId().equals(excludeContractId)) {
                continue;
            }

            if (hasTimeOverlap(startDate, endDate, existing.getStartDate(), existing.getEndDate())) {
                throw new RuntimeException(
                        "该房源在 " + existing.getStartDate() + " 至 " + existing.getEndDate() + " 已有合同，时间段冲突");
            }
        }
    }

    private boolean hasTimeOverlap(LocalDate start1, LocalDate end1, LocalDate start2, LocalDate end2) {
        return !start1.isAfter(end2) && !end1.isBefore(start2);
    }

    @Transactional
    public Contract update(Long id, Contract contract) {
        Contract existing = findById(id);
        contract.setId(id);
        contract.setCreateTime(existing.getCreateTime());
        contract.setContractNo(existing.getContractNo());

        if (contract.getApartment() != null && contract.getStartDate() != null && contract.getEndDate() != null) {
            checkTimeConflict(contract.getApartment().getId(), contract.getStartDate(), contract.getEndDate(), id);
        }

        Contract saved = contractRepository.save(contract);

        if ("生效中".equals(contract.getStatus()) && !"生效中".equals(existing.getStatus())) {
            Apartment apartment = apartmentService.findById(contract.getApartment().getId());
            apartment.setStatus("已出租");
            apartmentService.save(apartment);

            deleteRelatedAppointments(contract.getApartment().getId(), contract.getTenant().getId());

            createInitialPayments(saved);
        }

        return saved;
    }

    private void createInitialPayments(Contract contract) {
        if (contract.getMonthlyRent() != null && contract.getMonthlyRent().compareTo(BigDecimal.ZERO) > 0) {
            Payment rentPayment = new Payment();
            rentPayment.setContract(contract);
            rentPayment.setTenant(contract.getTenant());
            rentPayment.setLandlord(contract.getLandlord());
            rentPayment.setPaymentDate(LocalDate.now());
            rentPayment.setAmount(contract.getMonthlyRent());
            rentPayment.setPaymentType("租金");
            rentPayment.setStatus("待支付");
            rentPayment.setRemark("合同首月租金");
            paymentRepository.save(rentPayment);
        }

        if (contract.getDeposit() != null && contract.getDeposit().compareTo(BigDecimal.ZERO) > 0) {
            Payment depositPayment = new Payment();
            depositPayment.setContract(contract);
            depositPayment.setTenant(contract.getTenant());
            depositPayment.setLandlord(contract.getLandlord());
            depositPayment.setPaymentDate(LocalDate.now());
            depositPayment.setAmount(contract.getDeposit());
            depositPayment.setPaymentType("押金");
            depositPayment.setStatus("待支付");
            depositPayment.setRemark("合同押金");
            paymentRepository.save(depositPayment);
        }
    }

    private void deleteRelatedAppointments(Long apartmentId, Long tenantId) {
        appointmentRepository.findByApartmentId(apartmentId)
                .forEach(appointment -> appointmentRepository.deleteById(appointment.getId()));
    }

    @Transactional
    public Contract terminate(Long id, String reason) {
        Contract contract = findById(id);
        if (!"生效中".equals(contract.getStatus())) {
            throw new RuntimeException("只有生效中的合同才能解约");
        }

        contract.setStatus("已终止");
        contract.setTerminateReason(reason);
        contract.setTerminateTime(LocalDateTime.now());

        Apartment apartment = apartmentService.findById(contract.getApartment().getId());
        apartment.setStatus("空置");
        apartmentService.save(apartment);

        return contractRepository.save(contract);
    }

    @Transactional
    public Contract requestSublet(Long id, Long newTenantId) {
        Contract contract = findById(id);
        if (!"生效中".equals(contract.getStatus())) {
            throw new RuntimeException("只有生效中的合同才能申请转租");
        }

        User newTenant = userService.findById(newTenantId);
        if (!"TENANT".equals(newTenant.getRole())) {
            throw new RuntimeException("新租户必须是租户角色");
        }

        contract.setSubletStatus("待确认");
        contract.setNewTenant(newTenant);

        return contractRepository.save(contract);
    }

    @Transactional
    public Contract confirmSublet(Long id) {
        Contract contract = findById(id);
        if (!"待确认".equals(contract.getSubletStatus())) {
            throw new RuntimeException("转租申请状态不正确");
        }

        User newTenant = contract.getNewTenant();
        contract.setTenant(newTenant);
        contract.setSubletStatus("已转租");
        contract.setNewTenant(null);

        return contractRepository.save(contract);
    }

    @Transactional
    public Contract rejectSublet(Long id) {
        Contract contract = findById(id);
        if (!"待确认".equals(contract.getSubletStatus())) {
            throw new RuntimeException("转租申请状态不正确");
        }

        contract.setSubletStatus("已拒绝");
        contract.setNewTenant(null);

        return contractRepository.save(contract);
    }

    @Transactional
    public void delete(Long id) {
        Contract contract = findById(id);

        if ("生效中".equals(contract.getStatus())) {
            throw new RuntimeException("生效中的合同不能删除，请先解约");
        }

        paymentRepository.deleteByContractId(id);

        contractRepository.deleteById(id);
    }

    private String generateContractNo() {
        String dateStr = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        long count = contractRepository.count() + 1;
        return "HT" + dateStr + String.format("%04d", count);
    }
}
