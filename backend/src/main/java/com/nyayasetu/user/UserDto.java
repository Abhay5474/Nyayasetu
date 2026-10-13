package com.nyayasetu.user;

import java.util.UUID;

public record UserDto(UUID id, String email, String fullName, String phone, String preferredLanguage,
                      boolean emailAlerts, boolean smsAlerts, Role role) {

    public static UserDto from(User u) {
        return new UserDto(u.getId(), u.getEmail(), u.getFullName(), u.getPhone(), u.getPreferredLanguage(),
                u.isEmailAlerts(), u.isSmsAlerts(), u.getRole());
    }
}
