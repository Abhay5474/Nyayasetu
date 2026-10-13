package com.nyayasetu.notification;

import com.nyayasetu.config.AppProperties;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;

/** SMS through Twilio's REST API. Enabled with SMS_PROVIDER=twilio plus account SID, token and sender number. */
@Component
public class TwilioSmsSender implements SmsSender {
    private final AppProperties.Sms cfg;
    private final RestClient client = RestClient.create("https://api.twilio.com");

    public TwilioSmsSender(AppProperties props) {
        this.cfg = props.alerts().sms();
    }

    @Override
    public boolean isEnabled() {
        return "twilio".equalsIgnoreCase(cfg.provider())
                && notBlank(cfg.twilioAccountSid()) && notBlank(cfg.twilioAuthToken()) && notBlank(cfg.twilioFromNumber());
    }

    @Override
    public void send(String toE164, String body) {
        if (!isEnabled()) throw new IllegalStateException("SMS provider is not configured");
        MultiValueMap<String, String> form = new LinkedMultiValueMap<>();
        form.add("To", toE164);
        form.add("From", cfg.twilioFromNumber());
        form.add("Body", body);
        client.post()
                .uri("/2010-04-01/Accounts/{sid}/Messages.json", cfg.twilioAccountSid())
                .headers(h -> h.setBasicAuth(cfg.twilioAccountSid(), cfg.twilioAuthToken()))
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .body(form)
                .retrieve()
                .toBodilessEntity();
    }

    private static boolean notBlank(String s) {
        return s != null && !s.isBlank();
    }
}
