package com.nyayasetu.storage;

import java.util.Optional;

/** Allowed upload formats, identified from the file's leading bytes (never from the client-supplied name). */
public enum FileType {
    PDF("pdf", "application/pdf"),
    PNG("png", "image/png"),
    JPEG("jpg", "image/jpeg"),
    TIFF("tif", "image/tiff"),
    BMP("bmp", "image/bmp"),
    WEBP("webp", "image/webp");

    private final String extension;
    private final String mimeType;

    FileType(String extension, String mimeType) {
        this.extension = extension;
        this.mimeType = mimeType;
    }

    public String extension() { return extension; }

    public String mimeType() { return mimeType; }

    public static Optional<FileType> sniff(byte[] h, int len) {
        if (len >= 5 && h[0] == '%' && h[1] == 'P' && h[2] == 'D' && h[3] == 'F' && h[4] == '-') return Optional.of(PDF);
        if (len >= 8 && (h[0] & 0xFF) == 0x89 && h[1] == 'P' && h[2] == 'N' && h[3] == 'G'
                && h[4] == 0x0D && h[5] == 0x0A && h[6] == 0x1A && h[7] == 0x0A) return Optional.of(PNG);
        if (len >= 3 && (h[0] & 0xFF) == 0xFF && (h[1] & 0xFF) == 0xD8 && (h[2] & 0xFF) == 0xFF) return Optional.of(JPEG);
        if (len >= 4 && ((h[0] == 'I' && h[1] == 'I' && h[2] == 0x2A && h[3] == 0x00)
                || (h[0] == 'M' && h[1] == 'M' && h[2] == 0x00 && h[3] == 0x2A))) return Optional.of(TIFF);
        if (len >= 2 && h[0] == 'B' && h[1] == 'M') return Optional.of(BMP);
        if (len >= 12 && h[0] == 'R' && h[1] == 'I' && h[2] == 'F' && h[3] == 'F'
                && h[8] == 'W' && h[9] == 'E' && h[10] == 'B' && h[11] == 'P') return Optional.of(WEBP);
        return Optional.empty();
    }
}
