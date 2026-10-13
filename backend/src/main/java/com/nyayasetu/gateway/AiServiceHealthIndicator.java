package com.nyayasetu.gateway;

import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

@Component("aiService")
public class AiServiceHealthIndicator implements HealthIndicator {
    private final AiServiceClient client;

    public AiServiceHealthIndicator(AiServiceClient client) {
        this.client = client;
    }

    @Override
    public Health health() {
        try {
            String status = client.health().path("status").asText("unknown");
            return "ok".equals(status) ? Health.up().build() : Health.status("DEGRADED").build();
        } catch (Exception e) {
            return Health.down().build();
        }
    }
}
