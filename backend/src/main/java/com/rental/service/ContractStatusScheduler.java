package com.rental.service;

import com.rental.entity.Apartment;
import com.rental.entity.Contract;
import com.rental.repository.ContractRepository;
import com.rental.repository.ApartmentRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDate;
import java.util.List;

@Service
public class ContractStatusScheduler {

    @Autowired
    private ContractRepository contractRepository;

    @Autowired
    private ApartmentRepository apartmentRepository;

    @Scheduled(cron = "0 0 0 * * ?")
    @Transactional
    public void updateExpiredContracts() {
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
}
