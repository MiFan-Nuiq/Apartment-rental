package com.rental.controller;

import com.rental.dto.ApiResponse;
import com.rental.entity.*;
import com.rental.repository.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/statistics")
public class StatisticsController {
    @Autowired
    private ApartmentRepository apartmentRepository;
    @Autowired
    private ContractRepository contractRepository;
    @Autowired
    private PaymentRepository paymentRepository;
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private ReviewRepository reviewRepository;
    @Autowired
    private ComplaintRepository complaintRepository;
    @Autowired
    private AppointmentRepository appointmentRepository;
    @Autowired
    private RepairRepository repairRepository;

    @GetMapping("/landlord/{landlordId}")
    public ApiResponse<Map<String, Object>> getLandlordStatistics(@PathVariable Long landlordId) {
        Map<String, Object> stats = new HashMap<>();

        List<Apartment> apartments = apartmentRepository.findByLandlordId(landlordId);
        long totalApartments = apartments.size();
        long rentedApartments = apartments.stream().filter(a -> "已出租".equals(a.getStatus())).count();
        long vacantApartments = apartments.stream().filter(a -> "空置".equals(a.getStatus())).count();

        double rentalRate = totalApartments > 0 ? (double) rentedApartments / totalApartments * 100 : 0;

        double totalIncome = 0;
        List<Contract> contracts = contractRepository.findByLandlordId(landlordId);
        for (Contract c : contracts) {
            if (c.getMonthlyRent() != null) {
                totalIncome += c.getMonthlyRent().doubleValue();
            }
        }

        List<Payment> payments = paymentRepository.findByLandlordId(landlordId);
        double actualIncome = payments.stream()
                .filter(p -> "已支付".equals(p.getStatus()))
                .mapToDouble(p -> p.getAmount() != null ? p.getAmount().doubleValue() : 0)
                .sum();

        List<Map<String, Object>> monthlyIncomes = calculateMonthlyIncome(payments);

        List<Review> reviews = reviewRepository.findByLandlordId(landlordId);
        List<Review> recentReviews = reviews.stream()
                .filter(r -> "已通过".equals(r.getStatus()))
                .sorted((a, b) -> b.getCreateTime().compareTo(a.getCreateTime()))
                .limit(5)
                .collect(Collectors.toList());

        stats.put("totalApartments", totalApartments);
        stats.put("rentedApartments", rentedApartments);
        stats.put("vacantApartments", vacantApartments);
        stats.put("rentalRate", Math.round(rentalRate * 100.0) / 100.0);
        stats.put("totalIncome", actualIncome);
        stats.put("monthlyIncomes", monthlyIncomes);
        stats.put("recentReviews", recentReviews);

        return ApiResponse.success(stats);
    }

    @GetMapping("/admin")
    public ApiResponse<Map<String, Object>> getAdminStatistics() {
        Map<String, Object> stats = new HashMap<>();

        long totalUsers = userRepository.count();
        long landlordCount = userRepository.findByRole("LANDLORD").size();
        long tenantCount = userRepository.findByRole("TENANT").size();

        long totalApartments = apartmentRepository.count();
        long rentedApartments = apartmentRepository.findByStatus("已出租").size();
        long availableApartments = apartmentRepository.findByStatus("空置").size();
        long pendingAudit = apartmentRepository.findByStatus("待审核").size();

        double occupancyRate = totalApartments > 0 ? (double) rentedApartments / totalApartments * 100 : 0;

        long totalContracts = contractRepository.count();
        long activeContracts = contractRepository.findByStatus("生效中").size();

        List<Complaint> complaints = complaintRepository.findAll();
        long pendingComplaints = complaints.stream().filter(c -> "待处理".equals(c.getStatus())).count();
        long processedComplaints = complaints.stream().filter(c -> "已处理".equals(c.getStatus())).count();

        List<Payment> payments = paymentRepository.findAll();
        double totalIncome = payments.stream()
                .filter(p -> "已支付".equals(p.getStatus()))
                .mapToDouble(p -> p.getAmount() != null ? p.getAmount().doubleValue() : 0)
                .sum();

        List<Map<String, Object>> monthlyIncomes = calculateMonthlyIncome(payments);

        List<Map<String, Object>> userGrowth = calculateUserGrowth();

        stats.put("totalUsers", totalUsers);
        stats.put("landlordCount", landlordCount);
        stats.put("tenantCount", tenantCount);
        stats.put("totalApartments", totalApartments);
        stats.put("rentedApartments", rentedApartments);
        stats.put("availableApartments", availableApartments);
        stats.put("pendingAudit", pendingAudit);
        stats.put("occupancyRate", Math.round(occupancyRate * 100.0) / 100.0);
        stats.put("totalContracts", totalContracts);
        stats.put("activeContracts", activeContracts);
        stats.put("pendingComplaints", pendingComplaints);
        stats.put("processedComplaints", processedComplaints);
        stats.put("totalIncome", totalIncome);
        stats.put("monthlyIncomes", monthlyIncomes);
        stats.put("userGrowth", userGrowth);

        return ApiResponse.success(stats);
    }

    private List<Map<String, Object>> calculateMonthlyIncome(List<Payment> payments) {
        List<Map<String, Object>> result = new ArrayList<>();
        LocalDate now = LocalDate.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM");

        Map<String, Double> incomeByMonth = new LinkedHashMap<>();
        for (int i = 5; i >= 0; i--) {
            LocalDate month = now.minusMonths(i);
            String monthStr = month.format(formatter);
            incomeByMonth.put(monthStr, 0.0);
        }

        for (Payment p : payments) {
            if ("已支付".equals(p.getStatus()) && p.getPaymentDate() != null && p.getAmount() != null) {
                String monthStr = p.getPaymentDate().format(formatter);
                if (incomeByMonth.containsKey(monthStr)) {
                    incomeByMonth.put(monthStr, incomeByMonth.get(monthStr) + p.getAmount().doubleValue());
                }
            }
        }

        for (Map.Entry<String, Double> entry : incomeByMonth.entrySet()) {
            Map<String, Object> item = new HashMap<>();
            item.put("month", entry.getKey());
            item.put("income", Math.round(entry.getValue() * 100.0) / 100.0);
            result.add(item);
        }

        return result;
    }

    private List<Map<String, Object>> calculateUserGrowth() {
        List<Map<String, Object>> result = new ArrayList<>();
        LocalDate now = LocalDate.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM");

        List<User> users = userRepository.findAll();

        Map<String, Long> growthByMonth = new LinkedHashMap<>();
        for (int i = 5; i >= 0; i--) {
            LocalDate month = now.minusMonths(i);
            String monthStr = month.format(formatter);
            growthByMonth.put(monthStr, 0L);
        }

        for (User u : users) {
            if (u.getCreateTime() != null) {
                String monthStr = u.getCreateTime().format(formatter);
                if (growthByMonth.containsKey(monthStr)) {
                    growthByMonth.put(monthStr, growthByMonth.get(monthStr) + 1);
                }
            }
        }

        for (Map.Entry<String, Long> entry : growthByMonth.entrySet()) {
            Map<String, Object> item = new HashMap<>();
            item.put("month", entry.getKey());
            item.put("count", entry.getValue());
            result.add(item);
        }

        return result;
    }
}
