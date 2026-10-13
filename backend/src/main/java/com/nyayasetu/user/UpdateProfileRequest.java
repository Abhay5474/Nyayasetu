package com.nyayasetu.user;

import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/** All fields optional: only non-null values are applied. */
public record UpdateProfileRequest(
        @Size(min = 1, max = 120) String fullName,
        @Pattern(regexp = "^\\+[1-9]\\d{7,14}$", message = "must be in international format, e.g. +919876543210") String phone,
        @Pattern(regexp = "en|mr", message = "must be 'en' or 'mr'") String preferredLanguage,
        Boolean emailAlerts,
        Boolean smsAlerts) {
}
