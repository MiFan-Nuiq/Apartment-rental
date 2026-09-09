package com.rental.controller;

import com.rental.dto.ApiResponse;
import com.rental.entity.Appointment;
import com.rental.service.AppointmentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/appointments")
public class AppointmentController {

    @Autowired
    private AppointmentService appointmentService;

    @GetMapping
    public ApiResponse<List<Appointment>> findAll() {
        return ApiResponse.success(appointmentService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<Appointment> findById(@PathVariable Long id) {
        return ApiResponse.success(appointmentService.findById(id));
    }

    @GetMapping("/tenant/{tenantId}")
    public ApiResponse<List<Appointment>> findByTenantId(@PathVariable Long tenantId) {
        return ApiResponse.success(appointmentService.findByTenantId(tenantId));
    }

    @GetMapping("/landlord/{landlordId}")
    public ApiResponse<List<Appointment>> findByLandlordId(@PathVariable Long landlordId) {
        return ApiResponse.success(appointmentService.findByLandlordId(landlordId));
    }

    @GetMapping("/landlord/{landlordId}/accepted-tenants")
    public ApiResponse<List<Appointment>> findAcceptedTenantsByLandlord(@PathVariable Long landlordId) {
        return ApiResponse.success(appointmentService.findAcceptedTenantsByLandlord(landlordId));
    }

    @PostMapping
    public ApiResponse<Appointment> save(@RequestBody Appointment appointment) {
        return ApiResponse.success(appointmentService.save(appointment));
    }

    @PutMapping("/{id}")
    public ApiResponse<Appointment> update(@PathVariable Long id, @RequestBody Appointment appointment) {
        return ApiResponse.success(appointmentService.update(id, appointment));
    }

    @PutMapping("/{id}/handle")
    public ApiResponse<Appointment> handleAppointment(@PathVariable Long id, @RequestParam String status, @RequestParam(required = false) String reply) {
        return ApiResponse.success(appointmentService.handleAppointment(id, status, reply));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        appointmentService.delete(id);
        return ApiResponse.success("删除成功", null);
    }
}
