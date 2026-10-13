package com.nyayasetu.config;

import java.util.List;
import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "nyayasetu")
public record AppProperties(Jwt jwt, Cors cors, Storage storage, Ai ai, Alerts alerts) {

    public record Jwt(String secret, int expirationMinutes, String issuer) {}

    public record Cors(List<String> allowedOrigins) {}

    public record Storage(String dir, int maxSizeMb) {}

    public record Ai(String baseUrl, String internalToken, int connectTimeoutSeconds,
                     int extractTimeoutSeconds, int simplifyTimeoutSeconds) {}

    public record Alerts(boolean enabled, String cron, List<Integer> reminderDays, String mailFrom, Sms sms) {}

    public record Sms(String provider, String twilioAccountSid, String twilioAuthToken, String twilioFromNumber) {}
}
