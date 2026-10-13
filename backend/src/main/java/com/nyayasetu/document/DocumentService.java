package com.nyayasetu.document;

import com.nyayasetu.document.DocumentDtos.DocumentDto;
import com.nyayasetu.document.DocumentDtos.PageResponse;
import com.nyayasetu.document.DocumentDtos.ResultDto;
import com.nyayasetu.storage.FileStorageService;
import com.nyayasetu.storage.StoredFile;
import com.nyayasetu.web.ApiException;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.core.task.TaskRejectedException;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

/** Application service behind the document REST API. Every lookup is scoped to the calling user. */
@Service
public class DocumentService {
    private static final Logger log = LoggerFactory.getLogger(DocumentService.class);
    static final Set<String> LANGUAGES = Set.of("en", "mr");

    private final DocumentRepository documents;
    private final ProcessingResultRepository results;
    private final DocumentStateService state;
    private final DocumentProcessor processor;
    private final FileStorageService storage;

    public DocumentService(DocumentRepository documents, ProcessingResultRepository results,
                           DocumentStateService state, DocumentProcessor processor, FileStorageService storage) {
        this.documents = documents;
        this.results = results;
        this.state = state;
        this.processor = processor;
        this.storage = storage;
    }

    public DocumentDto upload(UUID userId, MultipartFile file, String language) {
        String lang = requireLanguage(language);
        StoredFile stored = storage.store(userId, file);
        Document doc = new Document();
        doc.setUserId(userId);
        doc.setOriginalFilename(stored.originalFilename());
        doc.setStoredPath(stored.relativePath());
        doc.setContentType(stored.type().mimeType());
        doc.setSizeBytes(stored.sizeBytes());
        doc.setSha256(stored.sha256());
        try {
            doc = documents.save(doc);
        } catch (RuntimeException e) {
            storage.delete(stored.relativePath()); // do not leave orphaned files behind
            throw e;
        }
        start(doc.getId(), lang, false);
        return toDto(documents.findById(doc.getId()).orElseThrow());
    }

    public DocumentDto reprocess(UUID userId, UUID id, String language, boolean force) {
        String lang = requireLanguage(language);
        Document doc = owned(userId, id);
        start(doc.getId(), lang, force);
        return toDto(documents.findById(id).orElseThrow());
    }

    public PageResponse<DocumentDto> list(UUID userId, int page, int size) {
        Page<Document> p = documents.findByUserIdOrderByCreatedAtDesc(userId, PageRequest.of(Math.max(page, 0), Math.min(Math.max(size, 1), 50)));
        Map<UUID, List<ProcessingResult>> byDoc = results.findByDocumentIdIn(p.map(Document::getId).toList()).stream()
                .collect(Collectors.groupingBy(ProcessingResult::getDocumentId));
        List<DocumentDto> items = p.stream().map(d -> DocumentDto.from(d, byDoc.getOrDefault(d.getId(), List.of()))).toList();
        return new PageResponse<>(items, p.getNumber(), p.getSize(), p.getTotalElements(), p.getTotalPages());
    }

    public DocumentDto get(UUID userId, UUID id) {
        return toDto(owned(userId, id));
    }

    public ResultDto result(UUID userId, UUID id, String language) {
        owned(userId, id);
        return results.findByDocumentIdAndLanguage(id, requireLanguage(language))
                .map(ResultDto::from)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "RESULT_NOT_FOUND",
                        "This document has not been processed in that language yet"));
    }

    public Resource originalFile(UUID userId, UUID id) {
        Document d = owned(userId, id);
        return new FileSystemResource(storage.resolve(d.getStoredPath()));
    }

    public Document metadata(UUID userId, UUID id) {
        return owned(userId, id);
    }

    public void delete(UUID userId, UUID id) {
        Document d = owned(userId, id);
        documents.delete(d); // results + deadlines are removed by ON DELETE CASCADE
        storage.delete(d.getStoredPath());
    }

    public void deleteAllForUser(UUID userId) {
        documents.findByUserId(userId).forEach(documents::delete);
        storage.deleteUserDirectory(userId);
    }

    // ------------------------------------------------------------------ internals
    private void start(UUID documentId, String language, boolean force) {
        if (!state.beginProcessing(documentId, language, force)) return; // already running / already done
        try {
            processor.process(documentId, language);
        } catch (TaskRejectedException e) {
            log.warn("Processing queue is full; rejecting document {}", documentId);
            state.failResult(documentId, language, "The server is busy right now. Please try again in a minute.");
        }
    }

    private Document owned(UUID userId, UUID id) {
        return documents.findByIdAndUserId(id, userId)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "Document not found"));
    }

    private DocumentDto toDto(Document d) {
        return DocumentDto.from(d, results.findByDocumentIdIn(List.of(d.getId())));
    }

    private static String requireLanguage(String language) {
        String l = language == null ? "en" : language.trim().toLowerCase();
        if (!LANGUAGES.contains(l)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "UNSUPPORTED_LANGUAGE", "Language must be 'en' or 'mr'");
        }
        return l;
    }
}
