package com.nyayasetu.web;

import org.springframework.http.HttpStatus;

/** Business error that maps directly to an HTTP status and a stable machine-readable code. */
public class ApiException extends RuntimeException {
    private final HttpStatus status;
    private final String code;

    public ApiException(HttpStatus status, String code, String message) {
        super(message);
        this.status = status;
        this.code = code;
    }

    public HttpStatus status() { return status; }

    public String code() { return code; }
}
