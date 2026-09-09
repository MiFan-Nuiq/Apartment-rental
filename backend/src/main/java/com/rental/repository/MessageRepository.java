package com.rental.repository;

import com.rental.entity.Message;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface MessageRepository extends JpaRepository<Message, Long> {
    List<Message> findByReceiverId(Long receiverId);
    List<Message> findBySenderId(Long senderId);
    List<Message> findByStatus(String status);
    List<Message> findByType(String type);
    List<Message> findByTypeAndTargetRole(String type, String targetRole);
    List<Message> findByTypeOrTargetRole(String type, String targetRole);
}
