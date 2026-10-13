package com.nyayasetu.security;

import com.nyayasetu.user.Role;
import java.util.UUID;

/** Authenticated principal placed in the SecurityContext by {@link JwtAuthenticationFilter}. */
public record AuthUser(UUID id, String email, Role role) {}
