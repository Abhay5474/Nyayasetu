package com.nyayasetu;

import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nyayasetu.gateway.AiExtractResponse;
import com.nyayasetu.gateway.AiServiceClient;
import com.nyayasetu.gateway.AiServiceException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

/**
 * Full-stack test (Spring Security + JPA + Flyway on a real PostgreSQL) with the Python AI service mocked.
 *   TEST_DB_URL=jdbc:postgresql://localhost:5432/nyayasetu_test mvn test
 */
@SpringBootTest
@AutoConfigureMockMvc
@EnabledIfEnvironmentVariable(named = "TEST_DB_URL", matches = ".+")
class ApiIntegrationTest {

    static final Path STORAGE = createTempDir();

    static Path createTempDir() {
        try {
            return Files.createTempDirectory("nyayasetu-it");
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry r) {
        r.add("spring.datasource.url", () -> System.getenv("TEST_DB_URL"));
        r.add("spring.datasource.username", () -> System.getenv().getOrDefault("TEST_DB_USER", "nyayasetu"));
        r.add("spring.datasource.password", () -> System.getenv().getOrDefault("TEST_DB_PASSWORD", "nyayasetu"));
        r.add("nyayasetu.jwt.secret", () -> TestProps.SECRET);
        r.add("nyayasetu.storage.dir", STORAGE::toString);
    }

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;
    @MockBean AiServiceClient ai;

    static final byte[] PDF = "%PDF-1.4\n1 0 obj<<>>endobj\n".getBytes(StandardCharsets.US_ASCII);

    private String register(String email) throws Exception {
        String body = json.writeValueAsString(Map.of("email", email, "password", "S3cure-pass!", "fullName", "Asha Patil",
                "preferredLanguage", "mr"));
        MvcResult res = mvc.perform(post("/api/auth/register").contentType("application/json").content(body))
                .andExpect(status().isCreated()).andReturn();
        return json.readTree(res.getResponse().getContentAsString()).get("token").asText();
    }

    private JsonNode aiPayload(String lang) throws Exception {
        return json.readTree("""
            {"language":"%s","model":"test-model","generated_at":"2025-01-01T00:00:00Z",
             "document":{"document_type":"RTI reply","title":"Reply","summary":"The office refused.",
               "key_points":["Rejected under 8(1)(j)"],
               "deadlines":[{"description":"File first appeal","date":"2030-01-15","period":null,"source_text":"within 30 days"},
                            {"description":"Pay copying fee","date":null,"period":"within 10 days","source_text":"x"}],
               "required_actions":[{"action":"Appeal","priority":"high","due":null}],
               "legal_references":[{"citation":"RTI Act - Section 19(1)","explanation":"appeal","source_id":"S1"}],"caveats":[]},
             "sources":[{"source_id":"S1","kb_id":"rti-act-s19","kind":"act","title":"RTI","citation":"RTI Act - Section 19","snippet":"...","score":1.0,"cited":true}]}
            """.formatted(lang));
    }

    private String uploadDoc(String token, String lang) throws Exception {
        MockMultipartFile file = new MockMultipartFile("file", "reply.pdf", "application/pdf", PDF);
        MvcResult res = mvc.perform(multipart("/api/documents").file(file).param("language", lang)
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isAccepted()).andReturn();
        return json.readTree(res.getResponse().getContentAsString()).get("id").asText();
    }

    private JsonNode waitForStatus(String token, String id, String expected) {
        return await().atMost(Duration.ofSeconds(15)).pollInterval(Duration.ofMillis(100)).until(() -> {
            String body = mvc.perform(get("/api/documents/" + id).header("Authorization", "Bearer " + token))
                    .andReturn().getResponse().getContentAsString();
            return json.readTree(body);
        }, n -> expected.equals(n.get("status").asText()));
    }

    @Test
    void authenticationAndValidation() throws Exception {
        mvc.perform(get("/api/documents")).andExpect(status().isUnauthorized()).andExpect(jsonPath("$.code").value("UNAUTHORIZED"));
        mvc.perform(get("/api/documents").header("Authorization", "Bearer not.a.jwt")).andExpect(status().isUnauthorized());

        mvc.perform(post("/api/auth/register").contentType("application/json")
                        .content("{\"email\":\"bad\",\"password\":\"short\",\"fullName\":\"\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.fieldErrors.email").exists())
                .andExpect(jsonPath("$.fieldErrors.password").exists());

        String email = "dup-" + UUID.randomUUID() + "@example.in";
        register(email);
        mvc.perform(post("/api/auth/register").contentType("application/json")
                        .content(json.writeValueAsString(Map.of("email", email.toUpperCase(), "password", "S3cure-pass!", "fullName", "X"))))
                .andExpect(status().isConflict()).andExpect(jsonPath("$.code").value("EMAIL_TAKEN"));

        mvc.perform(post("/api/auth/login").contentType("application/json")
                        .content(json.writeValueAsString(Map.of("email", email, "password", "wrong-password"))))
                .andExpect(status().isUnauthorized()).andExpect(jsonPath("$.code").value("INVALID_CREDENTIALS"));
        mvc.perform(post("/api/auth/login").contentType("application/json")
                        .content(json.writeValueAsString(Map.of("email", email, "password", "S3cure-pass!"))))
                .andExpect(status().isOk()).andExpect(jsonPath("$.token").isNotEmpty())
                .andExpect(jsonPath("$.user.preferredLanguage").value("mr"));
    }

    @Test
    void uploadProcessReadAndTrackDeadlines() throws Exception {
        String token = register("flow-" + UUID.randomUUID() + "@example.in");
        when(ai.extract(any(Path.class))).thenReturn(new AiExtractResponse(
                "Reply to RTI application ... appeal within 30 days.", 1, 50, "digital", List.of(), "en", List.of()));
        when(ai.simplify(any(), eq("mr"), any())).thenReturn(aiPayload("mr"));
        when(ai.simplify(any(), eq("en"), any())).thenReturn(aiPayload("en"));

        String id = uploadDoc(token, "mr");
        JsonNode doc = waitForStatus(token, id, "COMPLETED");
        assertThat(doc.get("pageCount").asInt()).isEqualTo(1);
        assertThat(doc.get("extractionMethod").asText()).isEqualTo("digital");
        assertThat(doc.get("results").get(0).get("language").asText()).isEqualTo("mr");

        mvc.perform(get("/api/documents/" + id + "/results/mr").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("COMPLETED"))
                .andExpect(jsonPath("$.result.document.summary").value("The office refused."))
                .andExpect(jsonPath("$.result.sources[0].source_id").value("S1"));
        mvc.perform(get("/api/documents/" + id + "/results/en").header("Authorization", "Bearer " + token))
                .andExpect(status().isNotFound());

        // second language reuses the extracted text (no second OCR call)
        mvc.perform(post("/api/documents/" + id + "/process").param("language", "en").header("Authorization", "Bearer " + token))
                .andExpect(status().isAccepted());
        await().atMost(Duration.ofSeconds(15)).until(() -> mvc.perform(get("/api/documents/" + id + "/results/en")
                .header("Authorization", "Bearer " + token)).andReturn().getResponse().getStatus() == 200);
        org.mockito.Mockito.verify(ai, org.mockito.Mockito.times(1)).extract(any(Path.class));

        // deadlines captured once (not duplicated by the second language) and trackable
        MvcResult dl = mvc.perform(get("/api/documents/" + id + "/deadlines").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk()).andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].dueDate").value("2030-01-15")).andReturn();
        String deadlineId = json.readTree(dl.getResponse().getContentAsString()).get(0).get("id").asText();
        mvc.perform(patch("/api/deadlines/" + deadlineId).contentType("application/json").content("{\"status\":\"DONE\"}")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk()).andExpect(jsonPath("$.status").value("DONE"));

        // original file is downloadable by the owner
        mvc.perform(get("/api/documents/" + id + "/file").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk()).andExpect(content().contentType("application/pdf"));

        mvc.perform(get("/api/documents").header("Authorization", "Bearer " + token))
                .andExpect(jsonPath("$.totalItems").value(1));
        mvc.perform(delete("/api/documents/" + id).header("Authorization", "Bearer " + token)).andExpect(status().isNoContent());
        mvc.perform(get("/api/documents/" + id).header("Authorization", "Bearer " + token)).andExpect(status().isNotFound());
    }

    @Test
    void usersCannotSeeEachOthersDocuments() throws Exception {
        String alice = register("alice-" + UUID.randomUUID() + "@example.in");
        String mallory = register("mallory-" + UUID.randomUUID() + "@example.in");
        when(ai.extract(any(Path.class))).thenReturn(new AiExtractResponse("text text text text text", 1, 25, "digital", List.of(), "en", List.of()));
        when(ai.simplify(any(), any(), any())).thenReturn(aiPayload("en"));
        String id = uploadDoc(alice, "en");
        waitForStatus(alice, id, "COMPLETED");

        for (String path : List.of("/api/documents/" + id, "/api/documents/" + id + "/results/en",
                "/api/documents/" + id + "/file", "/api/documents/" + id + "/deadlines")) {
            mvc.perform(get(path).header("Authorization", "Bearer " + mallory)).andExpect(status().isNotFound());
        }
        mvc.perform(delete("/api/documents/" + id).header("Authorization", "Bearer " + mallory)).andExpect(status().isNotFound());
        mvc.perform(get("/api/documents").header("Authorization", "Bearer " + mallory)).andExpect(jsonPath("$.totalItems").value(0));
    }

    @Test
    void aiFailureIsReportedAndRetryable() throws Exception {
        String token = register("fail-" + UUID.randomUUID() + "@example.in");
        when(ai.extract(any(Path.class))).thenThrow(new AiServiceException(422, "No readable text found.", null));
        String id = uploadDoc(token, "en");
        JsonNode doc = waitForStatus(token, id, "FAILED");
        assertThat(doc.get("errorMessage").asText()).isEqualTo("No readable text found.");

        when(ai.extract(any(Path.class))).thenReturn(new AiExtractResponse("recovered text recovered text", 1, 30, "ocr", List.of(1), "mr", List.of()));
        when(ai.simplify(any(), any(), any())).thenReturn(aiPayload("en"));
        mvc.perform(post("/api/documents/" + id + "/process").param("language", "en").header("Authorization", "Bearer " + token))
                .andExpect(status().isAccepted());
        waitForStatus(token, id, "COMPLETED");
    }

    @Test
    void rejectsNonDocumentUploads() throws Exception {
        String token = register("bad-" + UUID.randomUUID() + "@example.in");
        MockMultipartFile exe = new MockMultipartFile("file", "invoice.pdf", "application/pdf", "MZ\u0090\u0000 binary".getBytes(StandardCharsets.ISO_8859_1));
        mvc.perform(multipart("/api/documents").file(exe).header("Authorization", "Bearer " + token))
                .andExpect(status().isUnsupportedMediaType()).andExpect(jsonPath("$.code").value("UNSUPPORTED_FILE_TYPE"));
        MockMultipartFile ok = new MockMultipartFile("file", "a.pdf", "application/pdf", PDF);
        mvc.perform(multipart("/api/documents").file(ok).param("language", "fr").header("Authorization", "Bearer " + token))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.code").value("UNSUPPORTED_LANGUAGE"));
    }

    @Test
    void profileUpdateAndAccountErasure() throws Exception {
        String email = "me-" + UUID.randomUUID() + "@example.in";
        String token = register(email);
        mvc.perform(patch("/api/users/me").contentType("application/json").header("Authorization", "Bearer " + token)
                        .content("{\"smsAlerts\":true}"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.code").value("PHONE_REQUIRED"));
        mvc.perform(patch("/api/users/me").contentType("application/json").header("Authorization", "Bearer " + token)
                        .content("{\"phone\":\"+919876543210\",\"smsAlerts\":true,\"preferredLanguage\":\"en\"}"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.smsAlerts").value(true));
        mvc.perform(delete("/api/users/me").header("Authorization", "Bearer " + token)).andExpect(status().isNoContent());
        mvc.perform(get("/api/users/me").header("Authorization", "Bearer " + token)).andExpect(status().isUnauthorized());
    }

    @Test
    void documentChatIsContinuousPersistedAndPrivate() throws Exception {
        String token = register("chat-" + UUID.randomUUID() + "@example.in");
        String other = register("snoop-" + UUID.randomUUID() + "@example.in");
        when(ai.extract(any(Path.class))).thenReturn(new AiExtractResponse("Reply text ... appeal within 30 days ...", 1, 40, "digital", List.of(), "en", List.of()));
        when(ai.simplify(any(), any(), any())).thenReturn(aiPayload("en"));
        String id = uploadDoc(token, "en");
        waitForStatus(token, id, "COMPLETED");

        var answer1 = json.readTree("{\"answer\":\"Within 30 days.\",\"answerable\":true,\"quotes\":[\"appeal within 30 days\"],"
                + "\"sources\":[{\"source_id\":\"S1\",\"citation\":\"RTI Act - Section 19\"}],\"follow_ups\":[\"Who do I appeal to?\"],\"model\":\"m\"}");
        var answer2 = json.readTree("{\"answer\":\"The senior officer.\",\"answerable\":true,\"quotes\":[],\"sources\":[],\"follow_ups\":[],\"model\":\"m\"}");
        when(ai.chat(any(), eq("How long do I have to appeal?"), eq("en"), any())).thenReturn(answer1);
        when(ai.chat(any(), eq("Who do I appeal to?"), eq("en"), any())).thenReturn(answer2);

        mvc.perform(post("/api/documents/" + id + "/chat").contentType("application/json").header("Authorization", "Bearer " + token)
                        .content("{\"question\":\"How long do I have to appeal?\",\"language\":\"en\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.question.role").value("USER"))
                .andExpect(jsonPath("$.answer.content").value("Within 30 days."))
                .andExpect(jsonPath("$.answer.details.quotes[0]").value("appeal within 30 days"))
                .andExpect(jsonPath("$.answer.details.sources[0].source_id").value("S1"))
                .andExpect(jsonPath("$.answer.details.follow_ups[0]").value("Who do I appeal to?"));
        mvc.perform(post("/api/documents/" + id + "/chat").contentType("application/json").header("Authorization", "Bearer " + token)
                        .content("{\"question\":\"Who do I appeal to?\",\"language\":\"en\"}"))
                .andExpect(status().isOk());

        // the second turn replayed the first Q+A as history
        org.mockito.ArgumentCaptor<List<AiServiceClient.Turn>> history = org.mockito.ArgumentCaptor.forClass(List.class);
        org.mockito.Mockito.verify(ai).chat(any(), eq("Who do I appeal to?"), eq("en"), history.capture());
        assertThat(history.getValue()).extracting(AiServiceClient.Turn::role).containsExactly("user", "assistant");
        assertThat(history.getValue().get(1).content()).isEqualTo("Within 30 days.");

        mvc.perform(get("/api/documents/" + id + "/chat").header("Authorization", "Bearer " + token))
                .andExpect(jsonPath("$.length()").value(4))
                .andExpect(jsonPath("$[0].role").value("USER")).andExpect(jsonPath("$[3].role").value("ASSISTANT"));

        // privacy + validation
        mvc.perform(get("/api/documents/" + id + "/chat").header("Authorization", "Bearer " + other)).andExpect(status().isNotFound());
        mvc.perform(post("/api/documents/" + id + "/chat").contentType("application/json").header("Authorization", "Bearer " + other)
                .content("{\"question\":\"hi\"}")).andExpect(status().isNotFound());
        mvc.perform(post("/api/documents/" + id + "/chat").contentType("application/json").header("Authorization", "Bearer " + token)
                .content("{\"question\":\"   \"}")).andExpect(status().isBadRequest());

        // AI failure is reported and nothing is stored
        when(ai.chat(any(), eq("Will fail"), any(), any())).thenThrow(new AiServiceException(0, "The AI service is not responding right now.", null));
        mvc.perform(post("/api/documents/" + id + "/chat").contentType("application/json").header("Authorization", "Bearer " + token)
                        .content("{\"question\":\"Will fail\",\"language\":\"en\"}"))
                .andExpect(status().isBadGateway()).andExpect(jsonPath("$.code").value("AI_UNAVAILABLE"));
        mvc.perform(get("/api/documents/" + id + "/chat").header("Authorization", "Bearer " + token)).andExpect(jsonPath("$.length()").value(4));

        mvc.perform(delete("/api/documents/" + id + "/chat").header("Authorization", "Bearer " + token)).andExpect(status().isNoContent());
        mvc.perform(get("/api/documents/" + id + "/chat").header("Authorization", "Bearer " + token)).andExpect(jsonPath("$.length()").value(0));
    }

    @Test
    void chatRequiresExtractedText() throws Exception {
        String token = register("early-" + UUID.randomUUID() + "@example.in");
        when(ai.extract(any(Path.class))).thenThrow(new AiServiceException(422, "No readable text found.", null));
        String id = uploadDoc(token, "en");
        waitForStatus(token, id, "FAILED");
        mvc.perform(post("/api/documents/" + id + "/chat").contentType("application/json").header("Authorization", "Bearer " + token)
                        .content("{\"question\":\"anything?\"}"))
                .andExpect(status().isConflict()).andExpect(jsonPath("$.code").value("NOT_READY"));
    }

    // ------------------------------------------------------------------ drafts (stateless proxy to the AI service)
    private static final String DRAFT = "{\"kind\":\"rti_application\",\"language\":\"en\",\"full_name\":\"Ramesh\",\"address\":\"Pune\","
            + "\"place\":\"Pune\",\"authority\":\"PMC\",\"subject\":\"Roads\",\"items\":[\"Work orders\"]}";

    @Test
    void draftsRequireLoginAndForwardTheForm() throws Exception {
        mvc.perform(post("/api/drafts/preview").contentType("application/json").content(DRAFT)).andExpect(status().isUnauthorized());

        String token = register("drafts-" + UUID.randomUUID() + "@example.com");
        when(ai.draftPreview(any())).thenReturn(json.readTree("{\"title\":\"RTI application\",\"blocks\":[],\"warnings\":[],\"notes\":[]}"));
        mvc.perform(post("/api/drafts/preview").header("Authorization", "Bearer " + token).contentType("application/json").content(DRAFT))
                .andExpect(status().isOk()).andExpect(jsonPath("$.title").value("RTI application"));

        byte[] pdf = "%PDF-1.4 draft".getBytes(StandardCharsets.US_ASCII);
        when(ai.draftFile(any(), eq("pdf"))).thenReturn(new AiServiceClient.DraftFile(pdf, "application/pdf",
                "attachment; filename=\"RTI-application-2026-10-14.pdf\""));
        MvcResult res = mvc.perform(post("/api/drafts/file?format=pdf").header("Authorization", "Bearer " + token)
                        .contentType("application/json").content(DRAFT))
                .andExpect(status().isOk()).andExpect(header().string("Content-Type", "application/pdf"))
                .andExpect(header().string("Content-Disposition", org.hamcrest.Matchers.containsString("RTI-application"))).andReturn();
        assertThat(res.getResponse().getContentAsByteArray()).isEqualTo(pdf);
    }

    @Test
    void draftsRejectBadInputAndExplainFieldProblems() throws Exception {
        String token = register("drafts2-" + UUID.randomUUID() + "@example.com");
        mvc.perform(post("/api/drafts/preview").header("Authorization", "Bearer " + token).contentType("application/json")
                        .content("{\"kind\":\"evil\"}")).andExpect(status().isBadRequest());
        mvc.perform(post("/api/drafts/file?format=exe").header("Authorization", "Bearer " + token).contentType("application/json")
                        .content(DRAFT)).andExpect(status().isBadRequest());
        mvc.perform(post("/api/drafts/preview").header("Authorization", "Bearer " + token).contentType("application/json")
                        .content("[1,2]")).andExpect(status().isBadRequest());

        org.mockito.Mockito.doThrow(new AiServiceException(422, "fee_reference is required when the fee is paid by cash", null)).when(ai).draftPreview(any());
        mvc.perform(post("/api/drafts/preview").header("Authorization", "Bearer " + token).contentType("application/json").content(DRAFT))
                .andExpect(status().isUnprocessableEntity()).andExpect(jsonPath("$.message").value("fee_reference is required when the fee is paid by cash"));

        org.mockito.Mockito.doThrow(new AiServiceException(0, "The AI service is not responding right now.", null)).when(ai).draftPreview(any());
        mvc.perform(post("/api/drafts/preview").header("Authorization", "Bearer " + token).contentType("application/json").content(DRAFT))
                .andExpect(status().isBadGateway());
    }
}
