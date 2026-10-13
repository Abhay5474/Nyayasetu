package com.nyayasetu.document;

import java.util.Collection;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ProcessingResultRepository extends JpaRepository<ProcessingResult, UUID> {
    Optional<ProcessingResult> findByDocumentIdAndLanguage(UUID documentId, String language);

    List<ProcessingResult> findByDocumentIdIn(Collection<UUID> documentIds);

    List<ProcessingResult> findByStatus(ResultStatus status);

    boolean existsByDocumentIdAndStatus(UUID documentId, ResultStatus status);
}
