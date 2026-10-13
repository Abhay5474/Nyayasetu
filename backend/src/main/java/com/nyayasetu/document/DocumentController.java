package com.nyayasetu.document;

import com.nyayasetu.deadline.DeadlineDtos.DeadlineDto;
import com.nyayasetu.deadline.DeadlineService;
import com.nyayasetu.document.DocumentDtos.DocumentDto;
import com.nyayasetu.document.DocumentDtos.PageResponse;
import com.nyayasetu.document.DocumentDtos.ResultDto;
import com.nyayasetu.security.AuthUser;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.UUID;
import org.springframework.core.io.Resource;
import org.springframework.http.CacheControl;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/documents")
public class DocumentController {

    private final DocumentService documents;
    private final DeadlineService deadlines;

    public DocumentController(DocumentService documents, DeadlineService deadlines) {
        this.documents = documents;
        this.deadlines = deadlines;
    }

    /** Upload a PDF/image and start processing in the chosen output language (en | mr). */
    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseStatus(HttpStatus.ACCEPTED)
    public DocumentDto upload(@AuthenticationPrincipal AuthUser user,
                              @RequestPart("file") MultipartFile file,
                              @RequestParam(defaultValue = "en") String language) {
        return documents.upload(user.id(), file, language);
    }

    @GetMapping
    public PageResponse<DocumentDto> list(@AuthenticationPrincipal AuthUser user,
                                          @RequestParam(defaultValue = "0") int page,
                                          @RequestParam(defaultValue = "20") int size) {
        return documents.list(user.id(), page, size);
    }

    @GetMapping("/{id}")
    public DocumentDto get(@AuthenticationPrincipal AuthUser user, @PathVariable UUID id) {
        return documents.get(user.id(), id);
    }

    /** (Re)generate the explanation in another language, reusing the already extracted text. */
    @PostMapping("/{id}/process")
    @ResponseStatus(HttpStatus.ACCEPTED)
    public DocumentDto process(@AuthenticationPrincipal AuthUser user, @PathVariable UUID id,
                               @RequestParam(defaultValue = "en") String language,
                               @RequestParam(defaultValue = "false") boolean force) {
        return documents.reprocess(user.id(), id, language, force);
    }

    @GetMapping("/{id}/results/{language}")
    public ResultDto result(@AuthenticationPrincipal AuthUser user, @PathVariable UUID id, @PathVariable String language) {
        return documents.result(user.id(), id, language);
    }

    @GetMapping("/{id}/deadlines")
    public List<DeadlineDto> deadlines(@AuthenticationPrincipal AuthUser user, @PathVariable UUID id) {
        documents.get(user.id(), id); // ownership check
        return deadlines.forDocument(user.id(), id);
    }

    @GetMapping("/{id}/file")
    public ResponseEntity<Resource> file(@AuthenticationPrincipal AuthUser user, @PathVariable UUID id) {
        Document meta = documents.metadata(user.id(), id);
        Resource body = documents.originalFile(user.id(), id);
        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(meta.getContentType()))
                .cacheControl(CacheControl.noStore().cachePrivate())
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        ContentDisposition.inline().filename(meta.getOriginalFilename(), StandardCharsets.UTF_8).build().toString())
                .body(body);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@AuthenticationPrincipal AuthUser user, @PathVariable UUID id) {
        documents.delete(user.id(), id);
    }
}
