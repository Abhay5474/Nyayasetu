package com.nyayasetu.chat;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.nyayasetu.chat.ChatDtos.ChatExchange;
import com.nyayasetu.chat.ChatDtos.ChatMessageDto;
import com.nyayasetu.document.Document;
import com.nyayasetu.document.DocumentRepository;
import com.nyayasetu.gateway.AiServiceClient;
import com.nyayasetu.gateway.AiServiceException;
import com.nyayasetu.web.ApiException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** Continuous Q&A about one document: history is persisted and replayed to the AI service on every turn. */
@Service
public class ChatService {
    /** Cost guard: questions per document. */
    static final int MAX_QUESTIONS_PER_DOCUMENT = 100;
    /** Messages (not turns) replayed to the model; the AI service trims further. */
    static final int HISTORY_WINDOW = 10;

    private final DocumentRepository documents;
    private final ChatMessageRepository messages;
    private final AiServiceClient ai;
    private final ObjectMapper mapper;

    public ChatService(DocumentRepository documents, ChatMessageRepository messages, AiServiceClient ai, ObjectMapper mapper) {
        this.documents = documents;
        this.messages = messages;
        this.ai = ai;
        this.mapper = mapper;
    }

    @Transactional(readOnly = true)
    public List<ChatMessageDto> history(UUID userId, UUID documentId) {
        owned(userId, documentId);
        return messages.findByDocumentIdAndUserIdOrderByCreatedAtAsc(documentId, userId).stream().map(ChatMessageDto::from).toList();
    }

    /** Not transactional on purpose: the AI call can take a while and must not hold a DB connection. */
    public ChatExchange ask(UUID userId, UUID documentId, String question, String language) {
        Document doc = owned(userId, documentId);
        String text = doc.getExtractedText();
        if (text == null || text.isBlank()) {
            throw new ApiException(HttpStatus.CONFLICT, "NOT_READY",
                    "This document has not been read yet. Wait for processing to finish, then ask your question.");
        }
        String q = question.strip();
        if (q.isEmpty()) throw new ApiException(HttpStatus.BAD_REQUEST, "EMPTY_QUESTION", "Please type a question");
        if (messages.countByDocumentIdAndUserIdAndRole(documentId, userId, ChatRole.USER) >= MAX_QUESTIONS_PER_DOCUMENT) {
            throw new ApiException(HttpStatus.CONFLICT, "CHAT_LIMIT",
                    "This conversation has reached its limit. Clear it to start a new one.");
        }
        String lang = language == null ? "en" : language;

        List<ChatMessage> recent = new ArrayList<>(messages.findByDocumentIdAndUserIdOrderByCreatedAtDesc(
                documentId, userId, PageRequest.of(0, HISTORY_WINDOW)));
        Collections.reverse(recent);

        JsonNode reply;
        try {
            reply = ai.chat(text, q, lang, recent.stream().map(m -> new AiServiceClient.Turn(
                    m.getRole() == ChatRole.USER ? "user" : "assistant", m.getContent())).toList());
        } catch (AiServiceException e) {
            throw new ApiException(HttpStatus.BAD_GATEWAY, "AI_UNAVAILABLE", e.userMessage());
        }

        ChatMessage userMsg = save(documentId, userId, ChatRole.USER, lang, q, null);
        ObjectNode details = mapper.createObjectNode();
        details.put("answerable", reply.path("answerable").asBoolean(true));
        details.set("quotes", reply.path("quotes"));
        details.set("sources", reply.path("sources"));
        details.set("follow_ups", reply.path("follow_ups"));
        details.put("model", reply.path("model").asText(null));
        ChatMessage answerMsg = save(documentId, userId, ChatRole.ASSISTANT, lang, reply.path("answer").asText(""), details);
        return new ChatExchange(ChatMessageDto.from(userMsg), ChatMessageDto.from(answerMsg));
    }

    @Transactional
    public void clear(UUID userId, UUID documentId) {
        owned(userId, documentId);
        messages.deleteByDocumentIdAndUserId(documentId, userId);
    }

    private ChatMessage save(UUID documentId, UUID userId, ChatRole role, String lang, String content, JsonNode details) {
        ChatMessage m = new ChatMessage();
        m.setDocumentId(documentId);
        m.setUserId(userId);
        m.setRole(role);
        m.setLanguage(lang);
        m.setContent(content);
        m.setDetails(details);
        return messages.saveAndFlush(m);
    }

    private Document owned(UUID userId, UUID documentId) {
        return documents.findByIdAndUserId(documentId, userId)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", "Document not found"));
    }
}
