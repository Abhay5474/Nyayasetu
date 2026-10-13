package com.nyayasetu.chat;

import com.nyayasetu.chat.ChatDtos.AskRequest;
import com.nyayasetu.chat.ChatDtos.ChatExchange;
import com.nyayasetu.chat.ChatDtos.ChatMessageDto;
import com.nyayasetu.security.AuthUser;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/documents/{documentId}/chat")
public class ChatController {

    private final ChatService chat;

    public ChatController(ChatService chat) {
        this.chat = chat;
    }

    @GetMapping
    public List<ChatMessageDto> history(@AuthenticationPrincipal AuthUser user, @PathVariable UUID documentId) {
        return chat.history(user.id(), documentId);
    }

    @PostMapping
    public ChatExchange ask(@AuthenticationPrincipal AuthUser user, @PathVariable UUID documentId,
                            @Valid @RequestBody AskRequest req) {
        return chat.ask(user.id(), documentId, req.question(), req.language());
    }

    @DeleteMapping
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void clear(@AuthenticationPrincipal AuthUser user, @PathVariable UUID documentId) {
        chat.clear(user.id(), documentId);
    }
}
