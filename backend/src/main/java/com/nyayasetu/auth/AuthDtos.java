package com.nyayasetu.auth;

import com.nyayasetu.user.UserDto;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.Instant;

public final class AuthDtos {
    private AuthDtos() {}

    public record RegisterRequest(
            @NotBlank @Email @Size(max = 255) String email,
            // bcrypt only uses the first 72 bytes, so longer passwords are rejected rather than silently truncated
            @NotBlank @Size(min = 8, max = 72, message = "must be 8 to 72 characters") String password,
            @NotBlank @Size(max = 120) String fullName,
            @Pattern(regexp = "^\\+[1-9]\\d{7,14}$", message = "must be in international format, e.g. +919876543210") String phone,
            @Pattern(regexp = "en|mr", message = "must be 'en' or 'mr'") String preferredLanguage) {}

    public record LoginRequest(@NotBlank @Email String email, @NotBlank @Size(max = 72) String password) {}

    public record AuthResponse(String token, String tokenType, Instant expiresAt, UserDto user) {}
}
