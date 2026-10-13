package com.nyayasetu.deadline;

import com.fasterxml.jackson.databind.JsonNode;
import com.nyayasetu.deadline.DeadlineDtos.DeadlineDto;
import com.nyayasetu.document.Document;
import com.nyayasetu.document.DocumentRepository;
import com.nyayasetu.web.ApiException;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class DeadlineService {
    private static final Logger log = LoggerFactory.getLogger(DeadlineService.class);
    static final ZoneId IST = ZoneId.of("Asia/Kolkata");

    private final DeadlineRepository deadlines;
    private final DocumentRepository documents;

    public DeadlineService(DeadlineRepository deadlines, DocumentRepository documents) {
        this.deadlines = deadlines;
        this.documents = documents;
    }

    /**
     * Persists deadlines found by the AI service so they can be tracked and reminded about.
     * Only the first processed language creates them, so translating a document does not duplicate rows.
     */
    @Transactional
    public int captureFromResult(UUID documentId, UUID userId, JsonNode payload) {
        if (deadlines.countByDocumentId(documentId) > 0) return 0;
        int created = 0;
        for (JsonNode n : payload.path("document").path("deadlines")) {
            String description = n.path("description").asText("").strip();
            if (description.isEmpty()) continue;
            Deadline d = new Deadline();
            d.setDocumentId(documentId);
            d.setUserId(userId);
            d.setDescription(truncate(description, 1000));
            d.setDueDate(parseDate(n.path("date").asText(null)));
            d.setPeriodText(truncate(n.path("period").asText(null), 300));
            d.setSourceText(truncate(n.path("source_text").asText(null), 500));
            deadlines.save(d);
            created++;
        }
        if (created > 0) log.info("Captured {} deadline(s) for document {}", created, documentId);
        return created;
    }

    @Transactional(readOnly = true)
    public List<DeadlineDto> list(UUID userId, DeadlineStatus status) {
        List<Deadline> rows = deadlines.findByUserIdOrderByDueDateAscCreatedAtDesc(userId).stream()
                .filter(d -> status == null || d.getStatus() == status).toList();
        return toDtos(rows);
    }

    @Transactional(readOnly = true)
    public List<DeadlineDto> forDocument(UUID userId, UUID documentId) {
        return toDtos(deadlines.findByDocumentIdAndUserIdOrderByDueDateAsc(documentId, userId));
    }

    @Transactional
    public DeadlineDto updateStatus(UUID userId, UUID id, DeadlineStatus status) {
        Deadline d = deadlines.findByIdAndUserId(id, userId)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "Deadline not found"));
        d.setStatus(status);
        Document doc = documents.findById(d.getDocumentId()).orElse(null);
        return DeadlineDto.from(deadlines.save(d), doc == null ? null : doc.getOriginalFilename(), LocalDate.now(IST));
    }

    private List<DeadlineDto> toDtos(List<Deadline> rows) {
        Map<UUID, String> names = documents.findAllById(rows.stream().map(Deadline::getDocumentId).distinct().toList())
                .stream().collect(Collectors.toMap(Document::getId, Document::getOriginalFilename, (a, b) -> a));
        LocalDate today = LocalDate.now(IST);
        return rows.stream().map(d -> DeadlineDto.from(d, names.get(d.getDocumentId()), today)).toList();
    }

    static LocalDate parseDate(String s) {
        if (s == null || s.isBlank() || "null".equalsIgnoreCase(s)) return null;
        try {
            return LocalDate.parse(s.strip());
        } catch (Exception e) {
            return null;
        }
    }

    private static String truncate(String s, int max) {
        if (s == null) return null;
        return s.length() <= max ? s : s.substring(0, max);
    }
}
