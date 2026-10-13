package com.nyayasetu.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.nyayasetu.TestProps;
import com.nyayasetu.user.Role;
import com.nyayasetu.user.User;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class JwtServiceTest {

    private User user() {
        User u = new User();
        u.setId(UUID.randomUUID());
        u.setEmail("a@b.in");
        u.setRole(Role.USER);
        return u;
    }

    @Test
    void issuesAndParsesToken() {
        JwtService jwt = new JwtService(TestProps.props(TestProps.SECRET, "x"));
        User u = user();
        var token = jwt.issue(u);
        var claims = jwt.parse(token.value()).orElseThrow();
        assertThat(claims.getSubject()).isEqualTo(u.getId().toString());
        assertThat(claims.get("role", String.class)).isEqualTo("USER");
    }

    @Test
    void rejectsTamperedAndForeignTokens() {
        JwtService jwt = new JwtService(TestProps.props(TestProps.SECRET, "x"));
        JwtService other = new JwtService(TestProps.props("another-secret-another-secret-another-1234", "x"));
        String token = jwt.issue(user()).value();
        assertThat(jwt.parse(token + "x")).isEmpty();
        assertThat(other.parse(token)).isEmpty();
        assertThat(jwt.parse("garbage")).isEmpty();
        assertThat(jwt.parse("")).isEmpty();
    }

    @Test
    void rejectsExpiredToken() {
        Instant now = Instant.parse("2025-01-01T00:00:00Z");
        JwtService issuer = new JwtService(TestProps.props(TestProps.SECRET, "x"), Clock.fixed(now, ZoneOffset.UTC));
        String token = issuer.issue(user()).value();
        JwtService later = new JwtService(TestProps.props(TestProps.SECRET, "x"),
                Clock.fixed(now.plus(Duration.ofMinutes(61)), ZoneOffset.UTC));
        assertThat(later.parse(token)).isEmpty();
        assertThat(issuer.parse(token)).isPresent();
    }

    @Test
    void refusesWeakSecret() {
        assertThatThrownBy(() -> new JwtService(TestProps.props("short", "x"))).isInstanceOf(IllegalStateException.class);
        assertThatThrownBy(() -> new JwtService(TestProps.props("", "x"))).isInstanceOf(IllegalStateException.class);
    }
}
