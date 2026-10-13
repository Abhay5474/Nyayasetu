package com.nyayasetu.document;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

/** Jobs queued in memory are lost on restart; surface them as failed (retryable) instead of "processing" forever. */
@Component
public class StartupRecovery {
    private static final Logger log = LoggerFactory.getLogger(StartupRecovery.class);
    private final DocumentStateService state;

    public StartupRecovery(DocumentStateService state) {
        this.state = state;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void recover() {
        int n = state.failInterrupted();
        if (n > 0) log.warn("Marked {} interrupted processing job(s) as failed", n);
    }
}
