package com.rental.controller;

import com.rental.dto.ApiResponse;
import com.rental.entity.Message;
import com.rental.service.MessageService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/messages")
public class MessageController {

    @Autowired
    private MessageService messageService;

    @GetMapping
    public ApiResponse<List<Message>> findAll() {
        return ApiResponse.success(messageService.findAll());
    }

    @GetMapping("/{id}")
    public ApiResponse<Message> findById(@PathVariable Long id) {
        return ApiResponse.success(messageService.findById(id));
    }

    @GetMapping("/receiver/{receiverId}")
    public ApiResponse<List<Message>> findByReceiverId(@PathVariable Long receiverId) {
        return ApiResponse.success(messageService.findByReceiverId(receiverId));
    }

    @GetMapping("/sender/{senderId}")
    public ApiResponse<List<Message>> findBySenderId(@PathVariable Long senderId) {
        return ApiResponse.success(messageService.findBySenderId(senderId));
    }

    @GetMapping("/announcements")
    public ApiResponse<List<Message>> findAnnouncements(@RequestParam(required = false) String role) {
        return ApiResponse.success(messageService.findAnnouncements(role));
    }

    @PostMapping
    public ApiResponse<Message> save(@RequestBody Message message) {
        return ApiResponse.success(messageService.save(message));
    }

    @PutMapping("/{id}/read")
    public ApiResponse<Message> markAsRead(@PathVariable Long id) {
        return ApiResponse.success(messageService.markAsRead(id));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable Long id) {
        messageService.delete(id);
        return ApiResponse.success("删除成功", null);
    }
}
