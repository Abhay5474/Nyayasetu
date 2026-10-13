package com.nyayasetu.deadline;

import jakarta.persistence.*;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "deadlines")
@Getter
@Setter
@NoArgsConstructor
public class Deadline {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "document_id", nullable = false, updatable = false)
    private UUID documentId;

    @Column(name = "user_id", nullable = false, updatable = false)
    private UUID userId;

    @Column(nullable = false)
    private String description;

    @Column(name = "due_date")
    private LocalDate dueDate;

    /** Relative period when no calendar date could be derived, e.g. "within 30 days of receipt". */
    @Column(name = "period_text")
    private String periodText;

    @Column(name = "source_text")
    private String sourceText;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private DeadlineStatus status = DeadlineStatus.PENDING;

    /** Smallest configured reminder offset (in days) already notified; null = nothing sent yet. */
    @Column(name = "last_reminder_stage")
    private Integer lastReminderStage;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();
}
