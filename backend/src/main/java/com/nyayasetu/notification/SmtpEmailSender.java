package com.nyayasetu.notification;

import com.nyayasetu.config.AppProperties;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Component;

@Component
public class SmtpEmailSender implements EmailSender {
    private final ObjectProvider<JavaMailSender> mailSender;
    private final String from;

    public SmtpEmailSender(ObjectProvider<JavaMailSender> mailSender, AppProperties props) {
        this.mailSender = mailSender;
        this.from = props.alerts().mailFrom();
    }

    @Override
    public boolean isEnabled() {
        return mailSender.getIfAvailable() != null;
    }

    @Override
    public void send(String to, String subject, String body) {
        JavaMailSender sender = mailSender.getIfAvailable();
        if (sender == null) throw new IllegalStateException("SMTP is not configured");
        SimpleMailMessage msg = new SimpleMailMessage();
        msg.setFrom(from);
        msg.setTo(to);
        msg.setSubject(subject);
        msg.setText(body);
        sender.send(msg);
    }
}
