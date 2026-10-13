package com.nyayasetu.security;

import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.nyayasetu.web.ApiException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;

class LoginThrottleTest {

    @Test
    void locksAfterFiveFailuresAndRecoversAfterWindow() {
        AtomicReference<Instant> now = new AtomicReference<>(Instant.parse("2025-01-01T00:00:00Z"));
        Clock clock = new Clock() {
            public java.time.ZoneId getZone() { return ZoneOffset.UTC; }
            public Clock withZone(java.time.ZoneId z) { return this; }
            public Instant instant() { return now.get(); }
        };
        LoginThrottle t = new LoginThrottle(clock);
        for (int i = 0; i < 5; i++) {
            t.assertAllowed("k");
            t.recordFailure("k");
        }
        assertThatThrownBy(() -> t.assertAllowed("k")).isInstanceOf(ApiException.class);
        assertThatCode(() -> t.assertAllowed("other")).doesNotThrowAnyException();
        now.set(now.get().plus(Duration.ofMinutes(16)));
        assertThatCode(() -> t.assertAllowed("k")).doesNotThrowAnyException();
    }

    @Test
    void successResetsCounter() {
        LoginThrottle t = new LoginThrottle();
        for (int i = 0; i < 4; i++) t.recordFailure("k");
        t.reset("k");
        for (int i = 0; i < 4; i++) t.recordFailure("k");
        assertThatCode(() -> t.assertAllowed("k")).doesNotThrowAnyException();
    }
}
