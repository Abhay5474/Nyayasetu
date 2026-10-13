package com.nyayasetu.notification;

import java.time.LocalDate;

/** E-mail / SMS wording in English and Marathi. */
final class AlertMessages {
    private AlertMessages() {}

    record Message(String subject, String body, String sms) {}

    static Message render(String language, String documentName, String description, LocalDate dueDate, long daysLeft) {
        boolean mr = "mr".equals(language);
        String when;
        if (daysLeft <= 0) when = mr ? "आज" : "today";
        else if (daysLeft == 1) when = mr ? "उद्या" : "tomorrow";
        else when = mr ? daysLeft + " दिवसांत" : "in " + daysLeft + " days";

        if (mr) {
            String subject = "न्यायसेतू स्मरणपत्र: " + documentName + " - अंतिम तारीख " + when;
            String body = "नमस्कार,\n\nतुमच्या \"" + documentName + "\" या कागदपत्रातील एका कारवाईची मुदत " + when
                    + " (" + dueDate + ") आहे:\n\n" + description
                    + "\n\nकृपया वेळेत कार्यवाही करा. तुम्ही न्यायसेतू मध्ये ही मुदत पूर्ण म्हणून नोंदवू शकता."
                    + "\n\nहे स्पष्टीकरण कायदेशीर सल्ला नाही. आवश्यक असल्यास वकिलाचा सल्ला घ्या.\n- न्यायसेतू";
            return new Message(subject, body, "न्यायसेतू: " + truncate(description, 90) + " - मुदत " + when + " (" + dueDate + ")");
        }
        String subject = "NyayaSetu reminder: " + documentName + " - deadline " + when;
        String body = "Hello,\n\nAn action in your document \"" + documentName + "\" is due " + when + " (" + dueDate + "):\n\n"
                + description + "\n\nPlease act in time. You can mark this deadline as done inside NyayaSetu."
                + "\n\nThis explanation is not legal advice. Consult a lawyer if needed.\n- NyayaSetu";
        return new Message(subject, body, "NyayaSetu: " + truncate(description, 90) + " - due " + when + " (" + dueDate + ")");
    }

    private static String truncate(String s, int max) {
        return s.length() <= max ? s : s.substring(0, max - 1) + "…";
    }
}
