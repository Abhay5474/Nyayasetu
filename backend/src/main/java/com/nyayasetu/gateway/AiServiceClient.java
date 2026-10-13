package com.nyayasetu.gateway;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nyayasetu.config.AppProperties;
import java.net.http.HttpClient;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

/** Gateway to the Python AI/NLP microservice (OCR + extraction, RAG + LLM simplification). */
@Component
public class AiServiceClient {
    private static final Logger log = LoggerFactory.getLogger(AiServiceClient.class);
    static final String TOKEN_HEADER = "X-Internal-Token";

    private final RestClient extractClient;
    private final RestClient simplifyClient;
    private final RestClient healthClient;
    private final ObjectMapper mapper;

    public AiServiceClient(AppProperties props, ObjectMapper mapper) {
        this.mapper = mapper;
        AppProperties.Ai ai = props.ai();
        this.extractClient = build(ai, Duration.ofSeconds(ai.extractTimeoutSeconds()));
        this.simplifyClient = build(ai, Duration.ofSeconds(ai.simplifyTimeoutSeconds()));
        this.healthClient = build(ai, Duration.ofSeconds(3));
    }

    private RestClient build(AppProperties.Ai ai, Duration readTimeout) {
        // HTTP/1.1 only: the JDK client otherwise attempts an h2c upgrade that uvicorn rejects, corrupting multipart uploads.
        HttpClient http = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .connectTimeout(Duration.ofSeconds(ai.connectTimeoutSeconds()))
                .build();
        JdkClientHttpRequestFactory factory = new JdkClientHttpRequestFactory(http);
        factory.setReadTimeout(readTimeout);
        return RestClient.builder()
                .baseUrl(ai.baseUrl())
                .requestFactory(factory)
                .defaultHeader(TOKEN_HEADER, ai.internalToken())
                .build();
    }

    /** OCR / text extraction for a stored upload. */
    public AiExtractResponse extract(Path file) {
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", new FileSystemResource(file));
        return call(() -> extractClient.post().uri("/v1/extract")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(body)
                .retrieve()
                .onStatus(HttpStatusCode::isError, (req, res) -> { throw toException(res.getStatusCode().value(), res.getBody().readAllBytes()); })
                .body(AiExtractResponse.class));
    }

    /** RAG-grounded simplification. Returns the AI service payload untouched (snake_case JSON). */
    public JsonNode simplify(String text, String language, String documentId) {
        Map<String, Object> body = Map.of("text", text, "language", language, "document_id", documentId);
        return call(() -> simplifyClient.post().uri("/v1/simplify")
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .onStatus(HttpStatusCode::isError, (req, res) -> { throw toException(res.getStatusCode().value(), res.getBody().readAllBytes()); })
                .body(JsonNode.class));
    }

    /** One turn of the document Q&A conversation; {@code history} excludes the new question. */
    public JsonNode chat(String documentText, String question, String language, List<Turn> history) {
        Map<String, Object> body = Map.of("text", documentText, "question", question, "language", language, "history", history);
        return call(() -> simplifyClient.post().uri("/v1/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .body(body)
                .retrieve()
                .onStatus(HttpStatusCode::isError, (req, res) -> { throw toException(res.getStatusCode().value(), res.getBody().readAllBytes()); })
                .body(JsonNode.class));
    }

    public record Turn(String role, String content) {}

    /** Lightweight liveness probe used by the health indicator. */
    public JsonNode health() {
        return healthClient.get().uri("/health").retrieve().body(JsonNode.class);
    }

    private <T> T call(java.util.function.Supplier<T> action) {
        try {
            T result = action.get();
            if (result == null) throw new AiServiceException(502, "The AI service returned an empty response", null);
            return result;
        } catch (AiServiceException e) {
            throw e;
        } catch (ResourceAccessException e) { // connect failure, timeout
            log.warn("AI service unreachable or timed out: {}", e.getMessage());
            throw new AiServiceException(0, "The AI service is not responding right now. Please try again shortly.", e);
        } catch (RuntimeException e) {
            log.error("Unexpected AI service client error", e);
            throw new AiServiceException(502, "The AI service returned an unexpected response", e);
        }
    }

    private AiServiceException toException(int status, byte[] body) {
        String detail = null;
        try {
            JsonNode n = mapper.readTree(body);
            if (n.path("detail").isTextual()) detail = n.get("detail").asText();
        } catch (Exception ignored) { /* not JSON */ }
        log.warn("AI service replied {}: {}", status, detail);
        String message;
        if (status == 422 && detail != null) message = detail; // user-actionable (unreadable scan, wrong type, ...)
        else if (status == 503) message = "The AI model is not configured on the server.";
        else message = "The AI service could not process this document (" + status + ").";
        return new AiServiceException(status, message, null);
    }
}
