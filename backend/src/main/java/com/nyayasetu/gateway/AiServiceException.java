package com.nyayasetu.gateway;

/** Failure talking to the Python AI service. {@link #userMessage()} is safe to show to end users. */
public class AiServiceException extends RuntimeException {
    private final int status;
    private final String userMessage;

    public AiServiceException(int status, String userMessage, Throwable cause) {
        super(userMessage, cause);
        this.status = status;
        this.userMessage = userMessage;
    }

    /** HTTP status of the AI service reply, or 0 for connectivity problems / timeouts. */
    public int status() { return status; }

    public String userMessage() { return userMessage; }

    /** 4xx from the AI service: retrying with the same input will not help (e.g. unreadable scan). */
    public boolean isPermanent() { return status >= 400 && status < 500; }
}
