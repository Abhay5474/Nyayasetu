package com.nyayasetu.user;

import com.nyayasetu.document.DocumentService;
import com.nyayasetu.security.AuthUser;
import com.nyayasetu.web.ApiException;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users/me")
public class UserController {

    private final UserRepository users;
    private final DocumentService documents;

    public UserController(UserRepository users, DocumentService documents) {
        this.users = users;
        this.documents = documents;
    }

    @GetMapping
    public UserDto me(@AuthenticationPrincipal AuthUser principal) {
        return UserDto.from(load(principal));
    }

    @PatchMapping
    public UserDto update(@AuthenticationPrincipal AuthUser principal, @Valid @RequestBody UpdateProfileRequest req) {
        User u = load(principal);
        if (req.fullName() != null) u.setFullName(req.fullName().trim());
        if (req.phone() != null) u.setPhone(req.phone());
        if (req.preferredLanguage() != null) u.setPreferredLanguage(req.preferredLanguage());
        if (req.emailAlerts() != null) u.setEmailAlerts(req.emailAlerts());
        if (req.smsAlerts() != null) {
            if (req.smsAlerts() && (u.getPhone() == null || u.getPhone().isBlank())) {
                throw new ApiException(HttpStatus.BAD_REQUEST, "PHONE_REQUIRED", "Add a phone number to enable SMS alerts");
            }
            u.setSmsAlerts(req.smsAlerts());
        }
        return UserDto.from(users.save(u));
    }

    /** Right to erasure: removes the account, all uploaded files, results and deadlines. */
    @DeleteMapping
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@AuthenticationPrincipal AuthUser principal) {
        documents.deleteAllForUser(principal.id());
        users.deleteById(principal.id());
    }

    private User load(AuthUser principal) {
        return users.findById(principal.id())
                .orElseThrow(() -> new ApiException(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", "Account no longer exists"));
    }
}
