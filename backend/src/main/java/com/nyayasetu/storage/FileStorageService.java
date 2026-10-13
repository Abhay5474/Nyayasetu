package com.nyayasetu.storage;

import com.nyayasetu.config.AppProperties;
import com.nyayasetu.web.ApiException;
import jakarta.annotation.PostConstruct;
import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.UUID;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

/** Validates uploads and keeps them on local disk under {root}/{userId}/{random-uuid}.{ext}. */
@Service
public class FileStorageService {
    private static final Logger log = LoggerFactory.getLogger(FileStorageService.class);
    private static final Pattern UNSAFE = Pattern.compile("[\\p{Cntrl}\\\\/:*?\"<>|]+");

    private final Path root;
    private final long maxBytes;

    public FileStorageService(AppProperties props) {
        this.root = Path.of(props.storage().dir()).toAbsolutePath().normalize();
        this.maxBytes = props.storage().maxSizeMb() * 1024L * 1024L;
    }

    @PostConstruct
    void init() throws IOException {
        Files.createDirectories(root);
    }

    public StoredFile store(UUID userId, MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "EMPTY_FILE", "Please choose a file to upload");
        }
        if (file.getSize() > maxBytes) {
            throw new ApiException(HttpStatus.PAYLOAD_TOO_LARGE, "FILE_TOO_LARGE",
                    "The file is larger than " + (maxBytes / 1024 / 1024) + " MB");
        }
        Path tmp = null;
        try (InputStream raw = new BufferedInputStream(file.getInputStream())) {
            raw.mark(16);
            byte[] head = new byte[16];
            int n = raw.readNBytes(head, 0, head.length);
            raw.reset();
            FileType type = FileType.sniff(head, n).orElseThrow(() -> new ApiException(
                    HttpStatus.UNSUPPORTED_MEDIA_TYPE, "UNSUPPORTED_FILE_TYPE",
                    "Unsupported file. Upload a PDF, PNG, JPEG, TIFF, BMP or WEBP file."));

            Path userDir = root.resolve(userId.toString());
            Files.createDirectories(userDir);
            String storedName = UUID.randomUUID() + "." + type.extension();
            Path target = userDir.resolve(storedName).normalize();
            if (!target.startsWith(root)) throw new IllegalStateException("Path escape attempt");
            tmp = Files.createTempFile(userDir, "upload-", ".part");

            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            long size;
            try (DigestInputStream in = new DigestInputStream(raw, digest)) {
                size = Files.copy(in, tmp, StandardCopyOption.REPLACE_EXISTING);
            }
            if (size > maxBytes) {
                throw new ApiException(HttpStatus.PAYLOAD_TOO_LARGE, "FILE_TOO_LARGE", "The file is too large");
            }
            Files.move(tmp, target, StandardCopyOption.ATOMIC_MOVE);
            tmp = null;
            return new StoredFile(userId + "/" + storedName, sanitizeName(file.getOriginalFilename()), type, size,
                    HexFormat.of().formatHex(digest.digest()));
        } catch (IOException e) {
            throw new UncheckedIOException("Could not store upload", e);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        } finally {
            if (tmp != null) {
                try { Files.deleteIfExists(tmp); } catch (IOException ignored) { /* best effort */ }
            }
        }
    }

    public Path resolve(String relativePath) {
        Path p = root.resolve(relativePath).normalize();
        if (!p.startsWith(root)) throw new IllegalArgumentException("Invalid path");
        return p;
    }

    public void delete(String relativePath) {
        try {
            Files.deleteIfExists(resolve(relativePath));
        } catch (IOException e) {
            log.warn("Could not delete stored file {}: {}", relativePath, e.getMessage());
        }
    }

    public void deleteUserDirectory(UUID userId) {
        Path dir = root.resolve(userId.toString()).normalize();
        if (!dir.startsWith(root) || !Files.isDirectory(dir)) return;
        try (var files = Files.walk(dir)) {
            files.sorted(java.util.Comparator.reverseOrder()).forEach(p -> {
                try { Files.deleteIfExists(p); } catch (IOException e) { log.warn("Could not delete {}", p); }
            });
        } catch (IOException e) {
            log.warn("Could not remove user directory {}: {}", dir, e.getMessage());
        }
    }

    static String sanitizeName(String name) {
        if (name == null || name.isBlank()) return "document";
        String base = name.replace('\\', '/');
        base = base.substring(base.lastIndexOf('/') + 1);
        base = UNSAFE.matcher(base).replaceAll("_").strip();
        if (base.isEmpty() || base.chars().allMatch(c -> c == '.')) return "document";
        return base.length() > 200 ? base.substring(0, 200) : base;
    }
}
