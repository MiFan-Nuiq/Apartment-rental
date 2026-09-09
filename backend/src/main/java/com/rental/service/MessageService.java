package com.rental.service;

import com.rental.entity.Message;
import com.rental.repository.MessageRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class MessageService {

    @Autowired
    private MessageRepository messageRepository;

    public List<Message> findAll() {
        return messageRepository.findAll();
    }

    public Message findById(Long id) {
        return messageRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("消息不存在"));
    }

    public List<Message> findByReceiverId(Long receiverId) {
        return messageRepository.findByReceiverId(receiverId);
    }

    public List<Message> findBySenderId(Long senderId) {
        return messageRepository.findBySenderId(senderId);
    }

    public List<Message> findAnnouncements(String role) {
        List<Message> allAnnouncements = messageRepository.findByType("公告");
        return allAnnouncements.stream()
                .filter(m -> m.getTargetRole() == null || m.getTargetRole().isEmpty() || m.getTargetRole().equals(role) || m.getTargetRole().equals("全部"))
                .collect(Collectors.toList());
    }

    public Message save(Message message) {
        if (message.getStatus() == null || message.getStatus().isEmpty()) {
            message.setStatus("未读");
        }
        return messageRepository.save(message);
    }

    public Message markAsRead(Long id) {
        Message message = findById(id);
        message.setStatus("已读");
        return messageRepository.save(message);
    }

    public void delete(Long id) {
        messageRepository.deleteById(id);
    }
}
