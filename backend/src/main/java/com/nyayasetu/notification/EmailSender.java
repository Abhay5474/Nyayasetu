package com.nyayasetu.notification;

public interface EmailSender {
    /** False when no SMTP server is configured (MAIL_HOST empty). */
    boolean isEnabled();

    void send(String to, String subject, String body);
}
