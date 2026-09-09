package com.rental.service;

import com.rental.entity.User;
import com.rental.repository.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private ContractRepository contractRepository;

    @Autowired
    private ApartmentRepository apartmentRepository;

    @Autowired
    private AppointmentRepository appointmentRepository;

    @Autowired
    private PaymentRepository paymentRepository;

    @Autowired
    private MessageRepository messageRepository;

    @Autowired
    private RepairRepository repairRepository;

    public List<User> findAll() {
        return userRepository.findAll();
    }

    public User findById(Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("用户不存在"));
    }

    public User findByUsername(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("用户不存在"));
    }

    public boolean existsByUsername(String username) {
        return userRepository.existsByUsername(username);
    }

    public User save(User user) {
        if (user.getId() == null && userRepository.existsByUsername(user.getUsername())) {
            throw new RuntimeException("用户名已存在");
        }
        if (user.getId() == null) {
            user.setPassword(passwordEncoder.encode(user.getPassword()));
        }
        return userRepository.save(user);
    }

    public User update(Long id, User user) {
        User existing = findById(id);
        user.setId(id);
        user.setPassword(existing.getPassword());
        return userRepository.save(user);
    }

    public void delete(Long id) {
        User user = findById(id);
        
        long contractCount = contractRepository.findByTenantId(id).size() + 
                            contractRepository.findByLandlordId(id).size();
        if (contractCount > 0) {
            throw new RuntimeException("该用户有关联的合同，无法删除");
        }
        
        long apartmentCount = apartmentRepository.findByLandlordId(id).size();
        if (apartmentCount > 0) {
            throw new RuntimeException("该用户有关联的公寓，无法删除");
        }
        
        long appointmentCount = appointmentRepository.findByTenantId(id).size() + 
                               appointmentRepository.findByLandlordId(id).size();
        if (appointmentCount > 0) {
            throw new RuntimeException("该用户有关联的预约，无法删除");
        }
        
        userRepository.deleteById(id);
    }
}
