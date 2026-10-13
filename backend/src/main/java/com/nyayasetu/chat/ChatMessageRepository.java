package com.nyayasetu.chat;

import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ChatMessageRepository extends JpaRepository<ChatMessage, UUID> {
    List<ChatMessage> findByDocumentIdAndUserIdOrderByCreatedAtAsc(UUID documentId, UUID userId);

    /** Newest first; callers reverse. */
    List<ChatMessage> findByDocumentIdAndUserIdOrderByCreatedAtDesc(UUID documentId, UUID userId, Pageable page);

    long countByDocumentIdAndUserIdAndRole(UUID documentId, UUID userId, ChatRole role);

    void deleteByDocumentIdAndUserId(UUID documentId, UUID userId);
}
