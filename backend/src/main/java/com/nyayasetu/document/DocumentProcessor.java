package com.nyayasetu.document;

import com.fasterxml.jackson.databind.JsonNode;
import com.nyayasetu.deadline.DeadlineService;
import com.nyayasetu.gateway.AiExtractResponse;
import com.nyayasetu.gateway.AiServiceClient;
import com.nyayasetu.gateway.AiServiceException;
import com.nyayasetu.storage.FileStorageService;
import java.util.UUID;
import java.util.function.Supplier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

/**
 * Orchestrates one document through the Python AI service:
 * stored file -> /v1/extract (once) -> /v1/simplify (per output language) -> persisted result + deadlines.
 */
@Component
public class DocumentProcessor {
    private static final Logger log = LoggerFactory.getLogger(DocumentProcessor.class);

    private final DocumentRepository documents;
    private final DocumentStateService state;
    private final AiServiceClient ai;
    private final FileStorageService storage;
    private final DeadlineService deadlines;

    public DocumentProcessor(DocumentRepository documents, DocumentStateService state, AiServiceClient ai,
                             FileStorageService storage, DeadlineService deadlines) {
        this.documents = documents;
        this.state = state;
        this.ai = ai;
        this.storage = storage;
        this.deadlines = deadlines;
    }

    @Async("documentExecutor")
    public void process(UUID documentId, String language) {
        Document doc = documents.findById(documentId).orElse(null);
        if (doc == null) return; // deleted while queued
        try {
            String text = doc.getExtractedText();
            if (text == null || text.isBlank()) {
                AiExtractResponse extraction = withRetry(() -> ai.extract(storage.resolve(doc.getStoredPath())));
                state.saveExtraction(documentId, extraction);
                text = extraction.text();
            }
            final String documentText = text;
            JsonNode payload = withRetry(() -> ai.simplify(documentText, language, documentId.toString()));
            state.completeResult(documentId, language, payload);
            try {
                deadlines.captureFromResult(documentId, doc.getUserId(), payload);
            } catch (RuntimeException e) { // never lose a finished explanation over deadline bookkeeping
                log.warn("Could not store deadlines for document {}", documentId, e);
            }
        } catch (AiServiceException e) {
            log.warn("Processing document {} ({}) failed: {}", documentId, language, e.getMessage());
            state.failResult(documentId, language, e.userMessage());
        } catch (RuntimeException e) {
            log.error("Processing document {} ({}) crashed", documentId, language, e);
            state.failResult(documentId, language, "Processing failed unexpectedly. Please try again.");
        }
    }

    /** One retry for transient failures (connection problems, 5xx); client errors are final. */
    private static <T> T withRetry(Supplier<T> call) {
        try {
            return call.get();
        } catch (AiServiceException first) {
            if (first.isPermanent() || first.status() == 503) throw first;
            try {
                Thread.sleep(2000);
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                throw first;
            }
            return call.get();
        }
    }
}
