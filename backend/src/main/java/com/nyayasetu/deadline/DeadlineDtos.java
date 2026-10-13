package com.nyayasetu.deadline;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.UUID;

public final class DeadlineDtos {
    private DeadlineDtos() {}

    public record DeadlineDto(UUID id, UUID documentId, String documentName, String description, LocalDate dueDate,
                              String period, String sourceText, DeadlineStatus status, Long daysLeft) {

        public static DeadlineDto from(Deadline d, String documentName, LocalDate today) {
            Long daysLeft = d.getDueDate() == null ? null : ChronoUnit.DAYS.between(today, d.getDueDate());
            return new DeadlineDto(d.getId(), d.getDocumentId(), documentName, d.getDescription(), d.getDueDate(),
                    d.getPeriodText(), d.getSourceText(), d.getStatus(), daysLeft);
        }
    }

    public record UpdateDeadlineRequest(@NotNull DeadlineStatus status) {}
}
