package com.nyayasetu.notification;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/** Audit trail of every reminder attempt. */
@Entity
@Table(name = "notification_log")
@Getter
@Setter
@NoArgsConstructor
public class NotificationLog {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "deadline_id", nullable = false)
    private UUID deadlineId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private NotificationChannel channel;

    @Column(nullable = false)
    private boolean success;

    private String detail;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    public NotificationLog(UUID deadlineId, NotificationChannel channel, boolean success, String detail) {
        this.deadlineId = deadlineId;
        this.channel = channel;
        this.success = success;
        this.detail = detail == null ? null : (detail.length() > 500 ? detail.substring(0, 500) : detail);
    }
}
