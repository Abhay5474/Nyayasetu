package com.nyayasetu.draft;

import com.fasterxml.jackson.databind.JsonNode;
import com.nyayasetu.gateway.AiServiceClient;
import com.nyayasetu.gateway.AiServiceException;
import com.nyayasetu.web.ApiException;
import java.util.Set;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Ready-to-file RTI drafts (application, first appeal, reply to a fee demand) in English or Marathi, as PDF or Word.
 * Stateless: nothing the person types is stored; the form goes to the AI service, which validates it and builds the document.
 */
@RestController
@RequestMapping("/api/drafts")
public class DraftController {
    static final Set<String> KINDS = Set.of("rti_application", "first_appeal", "fee_payment_reply");
    static final int MAX_FORM_CHARS = 30_000;

    private final AiServiceClient ai;

    public DraftController(AiServiceClient ai) {
        this.ai = ai;
    }

    @PostMapping("/preview")
    public JsonNode preview(@RequestBody JsonNode form) {
        check(form);
        try {
            return ai.draftPreview(form);
        } catch (AiServiceException e) {
            throw map(e);
        }
    }

    @PostMapping("/file")
    public ResponseEntity<byte[]> file(@RequestBody JsonNode form, @RequestParam(defaultValue = "pdf") String format) {
        if (!format.equals("pdf") && !format.equals("docx")) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "BAD_FORMAT", "Choose pdf or docx");
        }
        check(form);
        try {
            AiServiceClient.DraftFile f = ai.draftFile(form, format);
            ResponseEntity.BodyBuilder out = ResponseEntity.ok().header(HttpHeaders.CONTENT_TYPE, f.contentType());
            if (f.contentDisposition() != null) out.header(HttpHeaders.CONTENT_DISPOSITION, f.contentDisposition());
            return out.body(f.bytes());
        } catch (AiServiceException e) {
            throw map(e);
        }
    }

    private static void check(JsonNode form) {
        if (form == null || !form.isObject() || !KINDS.contains(form.path("kind").asText())) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "BAD_DRAFT", "Choose a valid draft type");
        }
        if (form.toString().length() > MAX_FORM_CHARS) {
            throw new ApiException(HttpStatus.PAYLOAD_TOO_LARGE, "DRAFT_TOO_LARGE", "The form is too long");
        }
    }

    /** 4xx from the AI service is a problem with what the person typed (it explains which field); anything else is ours. */
    private static ApiException map(AiServiceException e) {
        if (e.status() == 422) return new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "DRAFT_INVALID", e.userMessage());
        return new ApiException(HttpStatus.BAD_GATEWAY, "AI_UNAVAILABLE", e.userMessage());
    }
}
