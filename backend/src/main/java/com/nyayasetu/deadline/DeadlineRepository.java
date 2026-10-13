package com.nyayasetu.deadline;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DeadlineRepository extends JpaRepository<Deadline, UUID> {
    List<Deadline> findByUserIdOrderByDueDateAscCreatedAtDesc(UUID userId);

    List<Deadline> findByDocumentIdAndUserIdOrderByDueDateAsc(UUID documentId, UUID userId);

    Optional<Deadline> findByIdAndUserId(UUID id, UUID userId);

    long countByDocumentId(UUID documentId);

    List<Deadline> findByStatusAndDueDateBetween(DeadlineStatus status, LocalDate from, LocalDate to);
}
