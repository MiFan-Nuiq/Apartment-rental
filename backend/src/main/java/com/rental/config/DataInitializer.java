package com.rental.config;

import com.rental.entity.User;
import com.rental.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
public class DataInitializer implements CommandLineRunner {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Override
    public void run(String... args) throws Exception {
        if (userRepository.count() == 0) {
            initUsers();
        }
    }

    private void initUsers() {
        String encodedPassword = passwordEncoder.encode("123456");

        User admin = new User();
        admin.setUsername("admin");
        admin.setPassword(encodedPassword);
        admin.setRealName("系统管理员");
        admin.setPhone("13800138000");
        admin.setRole("ADMIN");
        userRepository.save(admin);

        User landlord = new User();
        landlord.setUsername("landlord");
        landlord.setPassword(encodedPassword);
        landlord.setRealName("张房东");
        landlord.setPhone("13800138001");
        landlord.setRole("LANDLORD");
        userRepository.save(landlord);

        User tenant = new User();
        tenant.setUsername("tenant");
        tenant.setPassword(encodedPassword);
        tenant.setRealName("李租户");
        tenant.setPhone("13800138002");
        tenant.setRole("TENANT");
        userRepository.save(tenant);
    }
}
