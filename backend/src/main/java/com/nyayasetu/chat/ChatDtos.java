package com.nyayasetu.chat;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.Instant;
import java.util.UUID;

public final class ChatDtos {
    private ChatDtos() {}

    public record AskRequest(
            @NotBlank @Size(max = 1000, message = "must be at most 1000 characters") String question,
            @Pattern(regexp = "en|mr", message = "must be 'en' or 'mr'") String language) {}

    public record ChatMessageDto(UUID id, ChatRole role, String language, String content, JsonNode details, Instant createdAt) {
        public static ChatMessageDto from(ChatMessage m) {
            return new ChatMessageDto(m.getId(), m.getRole(), m.getLanguage(), m.getContent(), m.getDetails(), m.getCreatedAt());
        }
    }

    public record ChatExchange(ChatMessageDto question, ChatMessageDto answer) {}
}
