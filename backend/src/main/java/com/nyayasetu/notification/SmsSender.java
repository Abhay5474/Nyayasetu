package com.nyayasetu.notification;

public interface SmsSender {
    boolean isEnabled();

    /** @param toE164 destination in international format, e.g. +919876543210 */
    void send(String toE164, String body);
}
