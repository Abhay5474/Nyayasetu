package com.nyayasetu.document;

import com.fasterxml.jackson.databind.JsonNode;
import com.nyayasetu.gateway.AiExtractResponse;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Small transactional state transitions, so long-running AI calls never hold a DB transaction open. */
@Service
public class DocumentStateService {

    private final DocumentRepository documents;
    private final ProcessingResultRepository results;

    public DocumentStateService(DocumentRepository documents, ProcessingResultRepository results) {
        this.documents = documents;
        this.results = results;
    }

    /**
     * Marks (document, language) as PROCESSING unless it already is, or is COMPLETED and not forced.
     * @return true when a new processing run should be started
     */
    @Transactional
    public boolean beginProcessing(UUID documentId, String language, boolean force) {
        Document d = documents.findById(documentId).orElseThrow();
        ProcessingResult r = results.findByDocumentIdAndLanguage(documentId, language).orElse(null);
        if (r != null && r.getStatus() == ResultStatus.PROCESSING) return false;
        if (r != null && r.getStatus() == ResultStatus.COMPLETED && !force) return false;
        if (r == null) {
            r = new ProcessingResult();
            r.setDocumentId(documentId);
            r.setLanguage(language);
        }
        r.setStatus(ResultStatus.PROCESSING);
        r.setErrorMessage(null);
        results.save(r);
        d.setStatus(DocumentStatus.PROCESSING);
        d.setErrorMessage(null);
        documents.save(d);
        return true;
    }

    @Transactional
    public void saveExtraction(UUID documentId, AiExtractResponse e) {
        Document d = documents.findById(documentId).orElseThrow();
        d.setExtractedText(e.text());
        d.setPageCount(e.pageCount());
        d.setExtractionMethod(e.method());
        d.setDetectedLanguage(e.languageHint());
        documents.save(d);
    }

    @Transactional
    public void completeResult(UUID documentId, String language, JsonNode payload) {
        ProcessingResult r = results.findByDocumentIdAndLanguage(documentId, language).orElseThrow();
        r.setStatus(ResultStatus.COMPLETED);
        r.setResult(payload);
        r.setModel(payload.path("model").asText(null));
        r.setErrorMessage(null);
        results.save(r);
        refreshDocumentStatus(documentId, null);
    }

    @Transactional
    public void failResult(UUID documentId, String language, String message) {
        results.findByDocumentIdAndLanguage(documentId, language).ifPresent(r -> {
            r.setStatus(ResultStatus.FAILED);
            r.setErrorMessage(message);
            results.save(r);
        });
        refreshDocumentStatus(documentId, message);
    }

    /** PROCESSING while any run is active; else COMPLETED if any language succeeded; else FAILED. */
    private void refreshDocumentStatus(UUID documentId, String failure) {
        Document d = documents.findById(documentId).orElse(null);
        if (d == null) return;
        boolean active = results.existsByDocumentIdAndStatus(documentId, ResultStatus.PROCESSING);
        boolean done = results.existsByDocumentIdAndStatus(documentId, ResultStatus.COMPLETED);
        if (active) d.setStatus(DocumentStatus.PROCESSING);
        else if (done) { d.setStatus(DocumentStatus.COMPLETED); d.setErrorMessage(null); }
        else { d.setStatus(DocumentStatus.FAILED); d.setErrorMessage(failure); }
        documents.save(d);
    }

    /** After a restart nothing is actually running any more: fail whatever was left in PROCESSING. */
    @Transactional
    public int failInterrupted() {
        var stale = results.findByStatus(ResultStatus.PROCESSING);
        for (ProcessingResult r : stale) {
            r.setStatus(ResultStatus.FAILED);
            r.setErrorMessage("Processing was interrupted by a server restart. Please try again.");
            results.save(r);
            refreshDocumentStatus(r.getDocumentId(), r.getErrorMessage());
        }
        return stale.size();
    }
}
