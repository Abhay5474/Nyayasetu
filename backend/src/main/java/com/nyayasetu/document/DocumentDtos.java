package com.nyayasetu.document;

import com.fasterxml.jackson.databind.JsonNode;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

public final class DocumentDtos {
    private DocumentDtos() {}

    public record ResultSummary(String language, ResultStatus status, String error) {}

    public record DocumentDto(UUID id, String originalFilename, String contentType, long sizeBytes,
                              DocumentStatus status, String errorMessage, Integer pageCount,
                              String extractionMethod, String detectedLanguage, Instant createdAt,
                              List<ResultSummary> results) {

        public static DocumentDto from(Document d, List<ProcessingResult> results) {
            return new DocumentDto(d.getId(), d.getOriginalFilename(), d.getContentType(), d.getSizeBytes(),
                    d.getStatus(), d.getErrorMessage(), d.getPageCount(), d.getExtractionMethod(),
                    d.getDetectedLanguage(), d.getCreatedAt(),
                    results.stream().map(r -> new ResultSummary(r.getLanguage(), r.getStatus(), r.getErrorMessage())).toList());
        }
    }

    /** {@code result} is the AI service payload verbatim: document, sources, model, language, ... */
    public record ResultDto(UUID documentId, String language, ResultStatus status, String error, String model,
                            Instant updatedAt, JsonNode result) {

        public static ResultDto from(ProcessingResult r) {
            return new ResultDto(r.getDocumentId(), r.getLanguage(), r.getStatus(), r.getErrorMessage(), r.getModel(),
                    r.getUpdatedAt(), r.getResult());
        }
    }

    public record PageResponse<T>(List<T> items, int page, int size, long totalItems, int totalPages) {}
}
