package com.nyayasetu.auth;

import com.nyayasetu.auth.AuthDtos.AuthResponse;
import com.nyayasetu.auth.AuthDtos.LoginRequest;
import com.nyayasetu.auth.AuthDtos.RegisterRequest;
import com.nyayasetu.security.JwtService;
import com.nyayasetu.security.LoginThrottle;
import com.nyayasetu.user.User;
import com.nyayasetu.user.UserDto;
import com.nyayasetu.user.UserRepository;
import com.nyayasetu.web.ApiException;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    /** Verified against when the e-mail is unknown, so response time does not reveal which accounts exist. */
    private final String dummyHash;

    private final UserRepository users;
    private final PasswordEncoder encoder;
    private final JwtService jwt;
    private final LoginThrottle throttle;

    public AuthService(UserRepository users, PasswordEncoder encoder, JwtService jwt, LoginThrottle throttle) {
        this.users = users;
        this.encoder = encoder;
        this.jwt = jwt;
        this.throttle = throttle;
        this.dummyHash = encoder.encode("not-a-real-password");
    }

    public AuthResponse register(RegisterRequest req) {
        String email = req.email().trim().toLowerCase();
        if (users.existsByEmailIgnoreCase(email)) throw emailTaken();
        User u = new User();
        u.setEmail(email);
        u.setPasswordHash(encoder.encode(req.password()));
        u.setFullName(req.fullName().trim());
        u.setPhone(req.phone());
        u.setPreferredLanguage(req.preferredLanguage() == null ? "en" : req.preferredLanguage());
        try {
            u = users.saveAndFlush(u);
        } catch (DataIntegrityViolationException race) { // concurrent registration with the same e-mail
            throw emailTaken();
        }
        return respond(u);
    }

    public AuthResponse login(LoginRequest req, String clientIp) {
        String email = req.email().trim().toLowerCase();
        String key = email + "|" + clientIp;
        throttle.assertAllowed(key);
        User user = users.findByEmailIgnoreCase(email).orElse(null);
        boolean ok = encoder.matches(req.password(), user != null ? user.getPasswordHash() : dummyHash) && user != null;
        if (!ok) {
            throttle.recordFailure(key);
            throw new ApiException(HttpStatus.UNAUTHORIZED, "INVALID_CREDENTIALS", "Invalid email or password");
        }
        throttle.reset(key);
        return respond(user);
    }

    private AuthResponse respond(User u) {
        JwtService.IssuedToken t = jwt.issue(u);
        return new AuthResponse(t.value(), "Bearer", t.expiresAt(), UserDto.from(u));
    }

    private static ApiException emailTaken() {
        return new ApiException(HttpStatus.CONFLICT, "EMAIL_TAKEN", "An account with this email already exists");
    }
}
