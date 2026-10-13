package com.nyayasetu;

import com.nyayasetu.config.AppProperties;
import java.util.List;

public final class TestProps {
    public static final String SECRET = "unit-test-secret-unit-test-secret-1234567890";

    private TestProps() {}

    public static AppProperties props(String secret, String storageDir) {
        return new AppProperties(
                new AppProperties.Jwt(secret, 60, "nyayasetu"),
                new AppProperties.Cors(List.of("http://localhost:5173")),
                new AppProperties.Storage(storageDir, 1),
                new AppProperties.Ai("http://localhost:8000", "token", 1, 5, 5),
                new AppProperties.Alerts(true, "0 0 8 * * *", List.of(7, 3, 1, 0), "no-reply@test",
                        new AppProperties.Sms("none", "", "", "")));
    }
}
