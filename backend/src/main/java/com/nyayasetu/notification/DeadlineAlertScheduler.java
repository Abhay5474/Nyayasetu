package com.nyayasetu.notification;

import java.time.LocalDate;
import java.time.ZoneId;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * Optional background process (ALERTS_ENABLED=true). Runs daily at 08:00 IST by default.
 * Single-instance design: if you run several backend replicas, enable it on only one of them.
 */
@Component
@ConditionalOnProperty(prefix = "nyayasetu.alerts", name = "enabled", havingValue = "true")
public class DeadlineAlertScheduler {
    private static final ZoneId IST = ZoneId.of("Asia/Kolkata");
    private final DeadlineAlertService service;

    public DeadlineAlertScheduler(DeadlineAlertService service) {
        this.service = service;
    }

    @Scheduled(cron = "${nyayasetu.alerts.cron}", zone = "Asia/Kolkata")
    public void run() {
        service.sendDueReminders(LocalDate.now(IST));
    }
}
