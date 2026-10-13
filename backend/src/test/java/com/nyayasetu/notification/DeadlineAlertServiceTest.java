package com.nyayasetu.notification;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.contains;
import static org.mockito.Mockito.*;

import com.nyayasetu.TestProps;
import com.nyayasetu.deadline.Deadline;
import com.nyayasetu.deadline.DeadlineRepository;
import com.nyayasetu.deadline.DeadlineStatus;
import com.nyayasetu.document.Document;
import com.nyayasetu.document.DocumentRepository;
import com.nyayasetu.user.User;
import com.nyayasetu.user.UserRepository;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class DeadlineAlertServiceTest {

    static final LocalDate TODAY = LocalDate.of(2025, 3, 10);
    DeadlineRepository deadlines = mock(DeadlineRepository.class);
    DocumentRepository documents = mock(DocumentRepository.class);
    UserRepository users = mock(UserRepository.class);
    NotificationLogRepository logs = mock(NotificationLogRepository.class);
    EmailSender email = mock(EmailSender.class);
    SmsSender sms = mock(SmsSender.class);
    DeadlineAlertService service;
    User user;

    @BeforeEach
    void setUp() {
        service = new DeadlineAlertService(deadlines, documents, users, logs, email, sms, TestProps.props(TestProps.SECRET, "x"));
        user = new User();
        user.setId(UUID.randomUUID());
        user.setEmail("citizen@example.in");
        user.setPhone("+919876543210");
        user.setPreferredLanguage("en");
        when(users.findById(user.getId())).thenReturn(Optional.of(user));
        Document doc = new Document();
        doc.setOriginalFilename("rti-reply.pdf");
        when(documents.findById(any())).thenReturn(Optional.of(doc));
        when(email.isEnabled()).thenReturn(true);
        when(sms.isEnabled()).thenReturn(true);
    }

    private Deadline deadline(int daysFromToday, Integer lastStage) {
        Deadline d = new Deadline();
        d.setId(UUID.randomUUID());
        d.setUserId(user.getId());
        d.setDocumentId(UUID.randomUUID());
        d.setDescription("File first appeal");
        d.setDueDate(TODAY.plusDays(daysFromToday));
        d.setStatus(DeadlineStatus.PENDING);
        d.setLastReminderStage(lastStage);
        return d;
    }

    @Test
    void stageIsSmallestOffsetNotBelowDaysLeft() {
        List<Integer> offsets = List.of(7, 3, 1, 0);
        assertThat(DeadlineAlertService.stageFor(7, offsets)).isEqualTo(7);
        assertThat(DeadlineAlertService.stageFor(5, offsets)).isEqualTo(7);
        assertThat(DeadlineAlertService.stageFor(3, offsets)).isEqualTo(3);
        assertThat(DeadlineAlertService.stageFor(2, offsets)).isEqualTo(3);
        assertThat(DeadlineAlertService.stageFor(0, offsets)).isEqualTo(0);
        assertThat(DeadlineAlertService.stageFor(8, offsets)).isNull();
    }

    @Test
    void sendsEmailAndSmsOnceThenAdvancesStage() {
        user.setSmsAlerts(true);
        Deadline d = deadline(3, null);
        when(deadlines.findByStatusAndDueDateBetween(eq(DeadlineStatus.PENDING), any(), any())).thenReturn(List.of(d));

        assertThat(service.sendDueReminders(TODAY)).isEqualTo(1);
        verify(email).send(eq("citizen@example.in"), contains("3 days"), contains("File first appeal"));
        verify(sms).send(eq("+919876543210"), contains("File first appeal"));
        assertThat(d.getLastReminderStage()).isEqualTo(3);

        assertThat(service.sendDueReminders(TODAY)).isZero(); // same stage: no duplicate
        verify(email, times(1)).send(any(), any(), any());
    }

    @Test
    void catchesUpAfterMissedDaysAndEscalatesToNextStage() {
        Deadline d = deadline(2, 7); // reminded at the 7-day stage, job was down on day 3
        when(deadlines.findByStatusAndDueDateBetween(any(), any(), any())).thenReturn(List.of(d));
        assertThat(service.sendDueReminders(TODAY)).isEqualTo(1);
        assertThat(d.getLastReminderStage()).isEqualTo(3);
    }

    @Test
    void respectsUserPreferencesAndMarathi() {
        user.setEmailAlerts(false);
        user.setSmsAlerts(false);
        Deadline d = deadline(0, null);
        when(deadlines.findByStatusAndDueDateBetween(any(), any(), any())).thenReturn(List.of(d));
        assertThat(service.sendDueReminders(TODAY)).isZero();
        verify(email, never()).send(any(), any(), any());
        assertThat(d.getLastReminderStage()).isNull(); // nothing delivered => retry next run

        user.setEmailAlerts(true);
        user.setPreferredLanguage("mr");
        assertThat(service.sendDueReminders(TODAY)).isEqualTo(1);
        verify(email).send(any(), contains("न्यायसेतू"), contains("आज"));
    }

    @Test
    void failedDeliveryIsLoggedAndRetriedLater() {
        Deadline d = deadline(1, null);
        when(deadlines.findByStatusAndDueDateBetween(any(), any(), any())).thenReturn(List.of(d));
        doThrow(new RuntimeException("smtp down")).when(email).send(any(), any(), any());
        assertThat(service.sendDueReminders(TODAY)).isZero();
        assertThat(d.getLastReminderStage()).isNull();
        verify(logs).save(argThat(l -> !l.isSuccess() && l.getChannel() == NotificationChannel.EMAIL));
    }
}
