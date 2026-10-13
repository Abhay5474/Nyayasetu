package com.nyayasetu.deadline;

import com.nyayasetu.deadline.DeadlineDtos.DeadlineDto;
import com.nyayasetu.deadline.DeadlineDtos.UpdateDeadlineRequest;
import com.nyayasetu.security.AuthUser;
import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/deadlines")
public class DeadlineController {

    private final DeadlineService service;

    public DeadlineController(DeadlineService service) {
        this.service = service;
    }

    @GetMapping
    public List<DeadlineDto> list(@AuthenticationPrincipal AuthUser user,
                                  @RequestParam(required = false) DeadlineStatus status) {
        return service.list(user.id(), status);
    }

    @PatchMapping("/{id}")
    public DeadlineDto update(@AuthenticationPrincipal AuthUser user, @PathVariable UUID id,
                              @Valid @RequestBody UpdateDeadlineRequest req) {
        return service.updateStatus(user.id(), id, req.status());
    }
}
