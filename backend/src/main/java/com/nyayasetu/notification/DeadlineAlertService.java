package com.nyayasetu.notification;

import com.nyayasetu.config.AppProperties;
import com.nyayasetu.deadline.Deadline;
import com.nyayasetu.deadline.DeadlineRepository;
import com.nyayasetu.deadline.DeadlineStatus;
import com.nyayasetu.document.Document;
import com.nyayasetu.document.DocumentRepository;
import com.nyayasetu.user.User;
import com.nyayasetu.user.UserRepository;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.Comparator;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * Sends reminders for pending deadlines. A deadline is reminded once per configured stage
 * (default: 7, 3, 1 days before and on the day). If the job misses a day (downtime) the next run
 * sends the reminder for the stage the deadline is currently in, so nothing is silently skipped.
 */
@Service
public class DeadlineAlertService {
    private static final Logger log = LoggerFactory.getLogger(DeadlineAlertService.class);

    private final DeadlineRepository deadlines;
    private final DocumentRepository documents;
    private final UserRepository users;
    private final NotificationLogRepository logs;
    private final EmailSender email;
    private final SmsSender sms;
    private final List<Integer> offsets;

    public DeadlineAlertService(DeadlineRepository deadlines, DocumentRepository documents, UserRepository users,
                                NotificationLogRepository logs, EmailSender email, SmsSender sms, AppProperties props) {
        this.deadlines = deadlines;
        this.documents = documents;
        this.users = users;
        this.logs = logs;
        this.email = email;
        this.sms = sms;
        this.offsets = props.alerts().reminderDays().stream().sorted(Comparator.reverseOrder()).toList();
    }

    /** @return number of deadlines for which at least one reminder was delivered */
    public int sendDueReminders(LocalDate today) {
        if (offsets.isEmpty()) return 0;
        int horizon = offsets.get(0);
        int notified = 0;
        for (Deadline d : deadlines.findByStatusAndDueDateBetween(DeadlineStatus.PENDING, today, today.plusDays(horizon))) {
            long daysLeft = ChronoUnit.DAYS.between(today, d.getDueDate());
            Integer stage = stageFor(daysLeft, offsets);
            if (stage == null || (d.getLastReminderStage() != null && d.getLastReminderStage() <= stage)) continue;
            try {
                if (remind(d, daysLeft)) {
                    d.setLastReminderStage(stage);
                    deadlines.save(d);
                    notified++;
                }
            } catch (RuntimeException e) { // one bad record must not stop the batch
                log.error("Reminder failed for deadline {}", d.getId(), e);
            }
        }
        log.info("Deadline alerts: {} deadline(s) notified", notified);
        return notified;
    }

    /** The smallest configured offset that is still >= daysLeft (the stage a deadline is currently in). */
    static Integer stageFor(long daysLeft, List<Integer> offsetsDescending) {
        Integer stage = null;
        for (Integer o : offsetsDescending) {
            if (o >= daysLeft) stage = o;
        }
        return stage;
    }

    private boolean remind(Deadline d, long daysLeft) {
        User user = users.findById(d.getUserId()).orElse(null);
        if (user == null) return false;
        String docName = documents.findById(d.getDocumentId()).map(Document::getOriginalFilename).orElse("your document");
        AlertMessages.Message msg = AlertMessages.render(user.getPreferredLanguage(), docName, d.getDescription(), d.getDueDate(), daysLeft);

        boolean delivered = false;
        if (user.isEmailAlerts() && email.isEnabled()) {
            delivered |= attempt(d, NotificationChannel.EMAIL, () -> email.send(user.getEmail(), msg.subject(), msg.body()));
        }
        if (user.isSmsAlerts() && user.getPhone() != null && sms.isEnabled()) {
            delivered |= attempt(d, NotificationChannel.SMS, () -> sms.send(user.getPhone(), msg.sms()));
        }
        if (!delivered) log.debug("No alert channel available for user {} / deadline {}", user.getId(), d.getId());
        return delivered;
    }

    private boolean attempt(Deadline d, NotificationChannel channel, Runnable send) {
        try {
            send.run();
            logs.save(new NotificationLog(d.getId(), channel, true, null));
            return true;
        } catch (RuntimeException e) {
            log.warn("{} reminder for deadline {} failed: {}", channel, d.getId(), e.getMessage());
            logs.save(new NotificationLog(d.getId(), channel, false, e.getMessage()));
            return false;
        }
    }
}
